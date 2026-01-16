"""Story mode engine for ShellQuest."""

import time
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn

from ..ui.theme import Theme
from ..ui.components import UIComponents
from ..models.player import PlayerStats, PlayerSession
from ..models.question import Question
from .quiz_engine import QuizEngine
from .scoring_system import ScoringSystem
from ..utils import logger, clear_terminal, PREMIUM_HINT_COST


@dataclass
class Level:
    """Represents a story level."""
    id: str
    name: str
    description: str
    story: str
    commands: List[str]
    questions_needed: int
    xp_reward: int
    boss: bool = False
    boss_name: str = ""
    boss_description: str = ""


@dataclass
class Chapter:
    """Represents a story chapter."""
    id: str
    name: str
    description: str
    icon: str
    commands: List[str]
    levels: List[Level]
    unlock_requirement: Optional[str] = None


class StoryEngine:
    """Manages story mode progression."""

    def __init__(self, console: Console, questions: List[Question], player: PlayerStats):
        self.console = console
        self.all_questions = questions
        self.player = player
        self.scoring = ScoringSystem()
        self.chapters: List[Chapter] = []
        self.load_chapters()

    def load_chapters(self):
        """Load chapter data from YAML."""
        data_path = Path(__file__).parent.parent.parent / "data" / "story" / "chapters.yaml"

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for ch_data in data.get('chapters', []):
                levels = []
                for lv_data in ch_data.get('levels', []):
                    level = Level(
                        id=lv_data['id'],
                        name=lv_data['name'],
                        description=lv_data['description'],
                        story=lv_data['story'],
                        commands=lv_data['commands'],
                        questions_needed=lv_data['questions_needed'],
                        xp_reward=lv_data['xp_reward'],
                        boss=lv_data.get('boss', False),
                        boss_name=lv_data.get('boss_name', ''),
                        boss_description=lv_data.get('boss_description', '')
                    )
                    levels.append(level)

                chapter = Chapter(
                    id=ch_data['id'],
                    name=ch_data['name'],
                    description=ch_data['description'],
                    icon=ch_data['icon'],
                    commands=ch_data['commands'],
                    levels=levels,
                    unlock_requirement=ch_data.get('unlock_requirement')
                )
                self.chapters.append(chapter)

            logger.info(f"Loaded {len(self.chapters)} chapters for story mode")

        except FileNotFoundError:
            logger.error(f"Chapters file not found: {data_path}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in chapters: {e}")
        except KeyError as e:
            logger.error(f"Missing required field in chapters: {e}")

    def is_chapter_unlocked(self, chapter: Chapter) -> bool:
        """Check if a chapter is unlocked."""
        if chapter.unlock_requirement is None:
            return True

        # Check if requirement chapter is completed
        return chapter.unlock_requirement in self.player.completed_chapters

    def is_level_unlocked(self, chapter: Chapter, level_idx: int) -> bool:
        """Check if a level is unlocked."""
        if level_idx == 0:
            return self.is_chapter_unlocked(chapter)

        # Previous level must be completed
        prev_level = chapter.levels[level_idx - 1]
        return prev_level.id in self.player.completed_levels

    def run_story_mode(self) -> bool:
        """Run the story mode interface."""
        while True:
            chapter = self.show_chapter_select()
            if chapter is None:
                return False

            level = self.show_level_select(chapter)
            if level is None:
                continue

            self.run_level(chapter, level)

    def show_chapter_select(self) -> Optional[Chapter]:
        """Show chapter selection screen."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        self.console.print("\n[bold]📖 STORY MODE[/bold]\n")

        # Show chapters
        available = []
        for i, chapter in enumerate(self.chapters):
            unlocked = self.is_chapter_unlocked(chapter)
            completed_levels = sum(1 for lv in chapter.levels if lv.id in self.player.completed_levels)
            total_levels = len(chapter.levels)

            if unlocked:
                available.append(chapter)
                status = f"[{completed_levels}/{total_levels}]"
                if completed_levels == total_levels:
                    status = "[bold green]COMPLETE[/bold green]"
                self.console.print(f"  {len(available)}. {chapter.icon} {chapter.name} {status}")
                self.console.print(f"     [dim]{chapter.description}[/dim]")
            else:
                self.console.print(f"  🔒 [dim]{chapter.name} - Complete {chapter.unlock_requirement} to unlock[/dim]")

        self.console.print(f"\n  {len(available) + 1}. ↩️  Back to Menu")

        choices = [str(i) for i in range(1, len(available) + 2)]
        choice = Prompt.ask("Select chapter", choices=choices)

        if int(choice) > len(available):
            return None

        return available[int(choice) - 1]

    def show_level_select(self, chapter: Chapter) -> Optional[Level]:
        """Show level selection for a chapter."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        self.console.print(f"\n[bold]{chapter.icon} {chapter.name}[/bold]")
        self.console.print(f"[dim]{chapter.description}[/dim]\n")

        available = []
        for i, level in enumerate(chapter.levels):
            unlocked = self.is_level_unlocked(chapter, i)
            completed = level.id in self.player.completed_levels

            if unlocked:
                available.append(level)
                if completed:
                    status = "[bold green]✓[/bold green]"
                elif level.boss:
                    status = f"[bold {Theme.WARNING}]👑 BOSS[/bold {Theme.WARNING}]"
                else:
                    status = ""

                self.console.print(f"  {len(available)}. {level.name} {status}")
                self.console.print(f"     [dim]{level.description}[/dim]")
            else:
                self.console.print(f"  🔒 [dim]{level.name} - Complete previous level[/dim]")

        self.console.print(f"\n  {len(available) + 1}. ↩️  Back to Chapters")

        choices = [str(i) for i in range(1, len(available) + 2)]
        choice = Prompt.ask("Select level", choices=choices)

        if int(choice) > len(available):
            return None

        return available[int(choice) - 1]

    def run_level(self, chapter: Chapter, level: Level):
        """Run a story level."""
        # Show story intro
        self.show_level_intro(level)

        # Get questions for this level's commands
        level_questions = [q for q in self.all_questions if q.command in level.commands]

        if len(level_questions) < level.questions_needed:
            self.console.print(f"[yellow]Not enough questions for this level yet![/yellow]")
            time.sleep(2)
            return

        # Run quiz
        quiz = QuizEngine(level_questions)
        session = PlayerSession()

        correct_needed = level.questions_needed
        correct_count = 0
        question_num = 0

        while correct_count < correct_needed:
            question_num += 1
            question = quiz.select_next_question(self.player, session)

            if not question:
                break

            result = self.run_story_question(level, question, question_num, correct_count, correct_needed)

            if result is None:  # User quit
                return

            if result:
                correct_count += 1
                self.player.xp += self.scoring.calculate_xp(question, 10, False, self.player.streak)

            self.player.record_answer(question.command, result, question.id)
            session.record_question(question.type.value, result, 0)

        # Level complete!
        self.show_level_complete(level, correct_count >= correct_needed)

        if correct_count >= correct_needed:
            if level.id not in self.player.completed_levels:
                self.player.completed_levels.append(level.id)
                self.player.xp += level.xp_reward

            # Check if chapter complete
            all_complete = all(lv.id in self.player.completed_levels for lv in chapter.levels)
            if all_complete and chapter.id not in self.player.completed_chapters:
                self.player.completed_chapters.append(chapter.id)
                self.show_chapter_complete(chapter)

    def show_level_intro(self, level: Level):
        """Show level intro with story."""
        clear_terminal()

        if level.boss:
            title = f"[bold {Theme.WARNING}]👑 BOSS BATTLE: {level.boss_name}[/bold {Theme.WARNING}]"
            border = Theme.WARNING
        else:
            title = f"[bold]{level.name}[/bold]"
            border = Theme.PANEL_BORDER_STYLE

        story_panel = Panel(
            Align.center(Text.assemble(
                (f"\n{level.story}\n\n", "italic"),
                (f"Complete {level.questions_needed} questions correctly!\n", f"bold {Theme.INFO}"),
                (f"Reward: +{level.xp_reward} XP\n", f"bold {Theme.SUCCESS}"),
            )),
            title=title,
            border_style=border,
            padding=(1, 2)
        )

        self.console.print(story_panel)
        self.console.print("\n[dim]Press ENTER to begin...[/dim]")
        input()

    def run_story_question(self, level: Level, question: Question, q_num: int,
                           correct: int, needed: int) -> Optional[bool]:
        """Run a single story question. Returns True/False for correct/wrong, None for quit."""
        clear_terminal()

        # Progress bar
        progress_text = f"Progress: {correct}/{needed}"
        bar_filled = int((correct / needed) * 20)
        bar_empty = 20 - bar_filled
        progress_bar = f"[{Theme.SUCCESS}]{'█' * bar_filled}[/{Theme.SUCCESS}][dim]{'░' * bar_empty}[/dim]"

        self.console.print(f"\n[bold]{level.name}[/bold] - Question {q_num}")
        self.console.print(f"{progress_text}  {progress_bar}\n")

        self.console.print(UIComponents.create_question_panel(question, q_num, 999))
        self.console.print("\n[dim][H] Hint  [P] Premium (40💎)  [Q] Quit level[/dim]\n")

        while True:
            answer = Prompt.ask("Your answer").strip()

            if answer.upper() == 'Q':
                return None
            elif answer.upper() == 'H':
                self.console.print(f"\n[bold {Theme.INFO}]Hint:[/bold {Theme.INFO}] {question.get_hint()}\n")
                continue
            elif answer.upper() == 'P':
                if self.player.spend_credits(PREMIUM_HINT_COST):
                    premium = question.get_premium_hint()
                    self.console.print(f"\n[bold yellow]💎 Premium Hint:[/bold yellow] {premium}\n")
                else:
                    self.console.print(f"[red]Not enough credits! Need {PREMIUM_HINT_COST}💎 (You have {self.player.credits}💎)[/red]")
                continue
            else:
                break

        is_correct = question.is_correct(answer)

        if is_correct:
            self.console.print(f"\n[bold {Theme.SUCCESS}]✓ Correct![/bold {Theme.SUCCESS}]")
        else:
            self.console.print(f"\n[bold {Theme.ERROR}]✗ Wrong![/bold {Theme.ERROR}]")
            self.console.print(f"[dim]The answer was: {question.correct_answer[0]}[/dim]")

        self.console.print(f"[dim]{question.explanation}[/dim]")

        if not is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)
        return is_correct

    def show_level_complete(self, level: Level, success: bool):
        """Show level completion screen."""
        clear_terminal()

        if success:
            panel = Panel(
                Align.center(Text.assemble(
                    ("\n🎉 LEVEL COMPLETE! 🎉\n\n", f"bold {Theme.SUCCESS}"),
                    (f"{level.name}\n\n", "bold"),
                    (f"+{level.xp_reward} XP earned!\n", f"bold {Theme.SUCCESS}"),
                )),
                border_style=Theme.SUCCESS,
                padding=(1, 2)
            )
        else:
            panel = Panel(
                Align.center(Text.assemble(
                    ("\n❌ LEVEL FAILED ❌\n\n", f"bold {Theme.ERROR}"),
                    ("Don't give up! Try again.\n", "dim"),
                )),
                border_style=Theme.ERROR,
                padding=(1, 2)
            )

        self.console.print(panel)
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()

    def show_chapter_complete(self, chapter: Chapter):
        """Show chapter completion screen."""
        clear_terminal()

        panel = Panel(
            Align.center(Text.assemble(
                ("\n🏆 CHAPTER COMPLETE! 🏆\n\n", f"bold {Theme.WARNING}"),
                (f"{chapter.icon} {chapter.name}\n\n", "bold"),
                ("You've mastered these commands:\n", "white"),
                (", ".join(chapter.commands) + "\n\n", f"bold {Theme.PRIMARY}"),
                ("Next chapter unlocked!\n", f"bold {Theme.SUCCESS}"),
            )),
            border_style=Theme.WARNING,
            padding=(1, 2)
        )

        self.console.print(panel)
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()
