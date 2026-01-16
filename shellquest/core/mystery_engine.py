"""Murder Mystery mode engine for ShellQuest."""

import time
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn
from rich.markdown import Markdown
from rich.table import Table

from ..ui.theme import Theme
from ..ui.components import UIComponents
from ..models.player import PlayerStats
from ..utils import logger, clear_terminal, PREMIUM_HINT_COST


@dataclass
class Challenge:
    """A mystery challenge/question."""
    id: str
    context: str
    question_type: str
    question: str
    correct_answers: List[str]
    hint: str
    success_narrative: str
    clue_unlocked: str
    options: List[str] = field(default_factory=list)


@dataclass
class Scene:
    """A mystery scene."""
    id: str
    title: str
    location: str
    narrative: str
    objective: str
    challenges: List[Challenge]


@dataclass
class Suspect:
    """A mystery suspect."""
    id: str
    name: str
    role: str
    description: str
    alibi: str
    motive: str


@dataclass
class MysteryCase:
    """A complete mystery case."""
    id: str
    title: str
    subtitle: str
    difficulty: str
    intro: str
    setting: str
    suspects: List[Suspect]
    scenes: List[Scene]
    conclusion_success: str
    conclusion_failure: str
    rewards: Dict[str, Any]


class MysteryEngine:
    """Manages murder mystery gameplay."""

    def __init__(self, console: Console, player: PlayerStats):
        self.console = console
        self.player = player
        self.current_case: Optional[MysteryCase] = None
        self.clues_found: List[str] = []
        self.total_clues: int = 0
        self.start_time: float = 0
        self.scenes_completed: int = 0

    def load_case(self, case_file: str) -> Optional[MysteryCase]:
        """Load a mystery case from YAML file."""
        data_path = Path(__file__).parent.parent.parent / "data" / "mystery" / case_file

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            case_data = data['case']

            # Parse suspects
            suspects = []
            for s in data.get('suspects', []):
                suspects.append(Suspect(
                    id=s['id'],
                    name=s['name'],
                    role=s['role'],
                    description=s['description'],
                    alibi=s['alibi'],
                    motive=s['motive']
                ))

            # Parse scenes
            scenes = []
            for sc in data.get('scenes', []):
                challenges = []
                for ch in sc.get('challenges', []):
                    # Handle both single correct_answer and list of correct_answers
                    correct = ch.get('correct_answers', [ch.get('correct_answer', '')])
                    if isinstance(correct, str):
                        correct = [correct]

                    challenges.append(Challenge(
                        id=ch['id'],
                        context=ch['context'],
                        question_type=ch['question_type'],
                        question=ch['question'],
                        correct_answers=correct,
                        hint=ch['hint'],
                        success_narrative=ch['success_narrative'],
                        clue_unlocked=ch['clue_unlocked'],
                        options=ch.get('options', [])
                    ))

                scenes.append(Scene(
                    id=sc['id'],
                    title=sc['title'],
                    location=sc['location'],
                    narrative=sc['narrative'],
                    objective=sc['objective'],
                    challenges=challenges
                ))

            # Count total clues
            total_clues = sum(len(scene.challenges) for scene in scenes)

            case = MysteryCase(
                id=case_data['id'],
                title=case_data['title'],
                subtitle=case_data['subtitle'],
                difficulty=case_data['difficulty'],
                intro=case_data['intro'],
                setting=case_data['setting'],
                suspects=suspects,
                scenes=scenes,
                conclusion_success=data['conclusion']['success'],
                conclusion_failure=data['conclusion']['failure'],
                rewards=data['rewards']
            )

            self.total_clues = total_clues
            logger.info(f"Loaded mystery case: {case.title} with {len(scenes)} scenes")
            return case

        except FileNotFoundError:
            logger.error(f"Mystery case file not found: {data_path}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in mystery case: {e}")
            return None
        except KeyError as e:
            logger.error(f"Missing required field in mystery case: {e}")
            return None

    def run_mystery_mode(self) -> bool:
        """Run the mystery mode interface."""
        while True:
            case = self.show_case_select()
            if case is None:
                return False

            self.run_case(case)

    def show_case_select(self) -> Optional[MysteryCase]:
        """Show case selection screen."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        # Mystery mode header
        header = Panel(
            Align.center(Text.assemble(
                ("\n", ""),
                ("MURDER MYSTERY MODE", f"bold {Theme.ERROR}"),
                ("\n", ""),
                ("Solve crimes using your terminal skills", "dim italic"),
                ("\n", ""),
            )),
            border_style=Theme.ERROR,
            padding=(0, 2)
        )
        self.console.print(header)

        # List available cases
        cases_path = Path(__file__).parent.parent.parent / "data" / "mystery"
        case_files = list(cases_path.glob("case_*.yaml"))

        if not case_files:
            self.console.print("\n[yellow]No mystery cases available yet![/yellow]")
            self.console.print("\n[dim]Press ENTER to return...[/dim]")
            input()
            return None

        self.console.print("\n[bold]Available Cases:[/bold]\n")

        available_cases = []
        for i, case_file in enumerate(sorted(case_files), 1):
            case = self.load_case(case_file.name)
            if case:
                available_cases.append((case_file.name, case))

                # Check if solved
                solved = case.id in getattr(self.player, 'solved_mysteries', [])
                status = "[bold green]SOLVED[/bold green]" if solved else ""

                self.console.print(f"  {i}. [bold]{case.title}[/bold] {status}")
                self.console.print(f"     [dim]{case.subtitle}[/dim]")
                self.console.print(f"     [dim]Difficulty: {case.difficulty.title()}[/dim]\n")

        self.console.print(f"  {len(available_cases) + 1}. [dim]Back to Menu[/dim]")

        choices = [str(i) for i in range(1, len(available_cases) + 2)]
        choice = Prompt.ask("\nSelect a case", choices=choices)

        if int(choice) > len(available_cases):
            return None

        _, selected_case = available_cases[int(choice) - 1]
        return selected_case

    def run_case(self, case: MysteryCase):
        """Run a complete mystery case."""
        self.current_case = case
        self.clues_found = []
        self.scenes_completed = 0
        self.start_time = time.time()

        # Show intro
        self.show_intro(case)

        # Show suspects
        self.show_suspects(case)

        # Run through each scene
        for scene in case.scenes:
            if not self.run_scene(scene):
                # Player quit
                return

        # Show conclusion
        self.show_conclusion(case)

    def show_intro(self, case: MysteryCase):
        """Show case introduction."""
        clear_terminal()

        # Dramatic title reveal
        title_panel = Panel(
            Align.center(Text.assemble(
                ("\n", ""),
                ("CASE FILE", "bold dim"),
                ("\n\n", ""),
                (case.title.upper(), f"bold {Theme.ERROR}"),
                ("\n", ""),
                (f'"{case.subtitle}"', "italic"),
                ("\n", ""),
            )),
            border_style=Theme.ERROR,
            padding=(1, 4)
        )
        self.console.print(title_panel)
        time.sleep(2)

        # Show intro narrative
        clear_terminal()
        intro_panel = Panel(
            Text(case.intro.strip(), style="white"),
            title="[bold]The Call[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(1, 2)
        )
        self.console.print(intro_panel)
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()

        # Show setting
        clear_terminal()
        setting_panel = Panel(
            Text(case.setting.strip(), style="white"),
            title="[bold]The Scene[/bold]",
            border_style=Theme.INFO,
            padding=(1, 2)
        )
        self.console.print(setting_panel)
        self.console.print("\n[dim]Press ENTER to begin investigation...[/dim]")
        input()

    def show_suspects(self, case: MysteryCase):
        """Show the suspect profiles."""
        clear_terminal()

        self.console.print("\n[bold]SUSPECTS[/bold]\n")

        table = Table(show_header=True, header_style=f"bold {Theme.PRIMARY}",
                     border_style=Theme.PANEL_BORDER_STYLE)
        table.add_column("Name", style="bold")
        table.add_column("Role", style="dim")
        table.add_column("Notes", style="white")

        for suspect in case.suspects:
            table.add_row(
                suspect.name,
                suspect.role,
                suspect.description[:50] + "..."
            )

        self.console.print(table)
        self.console.print("\n[dim]Keep these suspects in mind as you investigate.[/dim]")
        self.console.print("[dim]Press ENTER to continue...[/dim]")
        input()

    def run_scene(self, scene: Scene) -> bool:
        """Run a single scene. Returns False if player quits."""
        # Scene intro
        clear_terminal()

        scene_header = Panel(
            Align.center(Text.assemble(
                ("\n", ""),
                (f"SCENE: {scene.title.upper()}", f"bold {Theme.WARNING}"),
                ("\n", ""),
                (f"Location: {scene.location}", "dim"),
                ("\n", ""),
            )),
            border_style=Theme.WARNING,
            padding=(0, 2)
        )
        self.console.print(scene_header)

        # Narrative
        self.console.print(Panel(
            Text(scene.narrative.strip(), style="white italic"),
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(1, 2)
        ))

        self.console.print(f"\n[bold {Theme.INFO}]Objective:[/bold {Theme.INFO}] {scene.objective}")
        self.console.print("\n[dim]Press ENTER to begin...[/dim]")
        input()

        # Run challenges
        for i, challenge in enumerate(scene.challenges, 1):
            result = self.run_challenge(scene, challenge, i, len(scene.challenges))
            if result is None:  # Player quit
                return False

        self.scenes_completed += 1
        return True

    def run_challenge(self, scene: Scene, challenge: Challenge,
                      num: int, total: int) -> Optional[bool]:
        """Run a single challenge. Returns None if player quits."""
        clear_terminal()

        # Progress indicator
        clues_display = f"Clues: {len(self.clues_found)}/{self.total_clues}"
        self.console.print(f"\n[bold]{scene.title}[/bold] - Challenge {num}/{total}")
        self.console.print(f"[dim]{clues_display}[/dim]\n")

        # Context
        self.console.print(Panel(
            Text(challenge.context, style="italic"),
            title="[bold]Situation[/bold]",
            border_style=Theme.INFO,
            padding=(0, 2)
        ))

        # Question
        question_text = challenge.question.strip()

        if challenge.question_type == "multiple_choice" or challenge.question_type == "what_does_it_do":
            # Show options with letters
            self.console.print(f"\n[bold]{question_text}[/bold]\n")
            for i, option in enumerate(challenge.options, 1):
                letter = chr(64 + i)  # A, B, C, D, etc.
                self.console.print(f"  {letter}) {option}")
            self.console.print(f"\n[dim][H] Hint  [P] Premium (40💎)  [Q] Quit case[/dim]\n")

            # Build dynamic prompt text
            num_options = len(challenge.options)
            letters = '/'.join([chr(65 + i) for i in range(num_options)])
            numbers = '/'.join([str(i + 1) for i in range(num_options)])
            prompt_text = f"Your answer ({letters} or {numbers})"

            while True:
                answer = Prompt.ask(prompt_text).strip()

                if answer.upper() == 'Q':
                    return None
                elif answer.upper() == 'H':
                    self.console.print(f"\n[bold {Theme.INFO}]Hint:[/bold {Theme.INFO}] {challenge.hint}\n")
                    continue
                elif answer.upper() == 'P':
                    if self.player.spend_credits(PREMIUM_HINT_COST):
                        # Generate a premium hint based on question type
                        if challenge.question_type == "multiple_choice":
                            premium = "Two of these options are clearly wrong. Focus on the remaining two."
                        else:
                            premium = "Think step by step about what the command needs to do. Start with the base command."
                        self.console.print(f"\n[bold yellow]💎 Premium Hint:[/bold yellow] {premium}\n")
                    else:
                        self.console.print(f"[red]Not enough credits! Need {PREMIUM_HINT_COST}💎 (You have {self.player.credits}💎)[/red]")
                    continue

                # Validate answer - accept letters or numbers
                normalized_answer = answer.upper()
                idx = -1

                # Check if it's a valid letter (A, B, C, D based on number of options)
                if len(normalized_answer) == 1 and normalized_answer.isalpha():
                    letter_idx = ord(normalized_answer) - ord('A')
                    # Only accept if within valid range
                    if 0 <= letter_idx < num_options:
                        idx = letter_idx
                # Check if it's a number
                elif len(normalized_answer) == 1 and normalized_answer.isdigit():
                    num_idx = int(normalized_answer) - 1
                    # Only accept if within valid range
                    if 0 <= num_idx < num_options:
                        idx = num_idx

                # If valid index was found, use it
                if idx >= 0:
                    user_answer = challenge.options[idx]
                    break

                self.console.print(f"[yellow]Please enter {letters} or {numbers}[/yellow]")

        else:
            # Command builder - free text
            self.console.print(Panel(
                Text(question_text, style=f"bold {Theme.PRIMARY}"),
                title="[bold]Your Task[/bold]",
                border_style=Theme.PRIMARY,
                padding=(0, 2)
            ))
            self.console.print(f"\n[dim][H] Hint  [P] Premium (40💎)  [Q] Quit case[/dim]\n")

            while True:
                answer = Prompt.ask("[bold]$[/bold] ").strip()

                if answer.upper() == 'Q':
                    return None
                elif answer.upper() == 'H':
                    self.console.print(f"\n[bold {Theme.INFO}]Hint:[/bold {Theme.INFO}] {challenge.hint}\n")
                    continue
                elif answer.upper() == 'P':
                    if self.player.spend_credits(PREMIUM_HINT_COST):
                        # Generate a premium hint based on question type
                        if challenge.question_type == "multiple_choice":
                            premium = "Two of these options are clearly wrong. Focus on the remaining two."
                        else:
                            premium = "Think step by step about what the command needs to do. Start with the base command."
                        self.console.print(f"\n[bold yellow]💎 Premium Hint:[/bold yellow] {premium}\n")
                    else:
                        self.console.print(f"[red]Not enough credits! Need {PREMIUM_HINT_COST}💎 (You have {self.player.credits}💎)[/red]")
                    continue
                elif answer:
                    user_answer = answer
                    break
                else:
                    self.console.print("[yellow]Please enter a command[/yellow]")

        # Check answer
        is_correct = self.check_answer(user_answer, challenge)

        if is_correct:
            self.clues_found.append(challenge.clue_unlocked)
            self.console.print(f"\n[bold {Theme.SUCCESS}]EVIDENCE FOUND![/bold {Theme.SUCCESS}]")
            self.console.print(Panel(
                Text(challenge.success_narrative.strip(), style="white"),
                border_style=Theme.SUCCESS,
                padding=(1, 2)
            ))
            self.console.print(f"\n[bold {Theme.WARNING}]+ Clue:[/bold {Theme.WARNING}] {challenge.clue_unlocked}")
        else:
            self.console.print(f"\n[bold {Theme.ERROR}]Not quite right...[/bold {Theme.ERROR}]")
            self.console.print(f"[dim]The answer was: {challenge.correct_answers[0]}[/dim]")
            # Still progress but note missed clue
            self.console.print(f"\n[yellow]You missed a clue, but the investigation continues...[/yellow]")

        if not is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)
        return is_correct

    def check_answer(self, user_answer: str, challenge: Challenge) -> bool:
        """Check if the answer is correct."""
        user_answer = user_answer.strip().lower()

        for correct in challenge.correct_answers:
            if user_answer == correct.lower():
                return True

        return False

    def show_conclusion(self, case: MysteryCase):
        """Show case conclusion."""
        clear_terminal()

        time_taken = time.time() - self.start_time
        minutes = int(time_taken // 60)
        seconds = int(time_taken % 60)
        time_str = f"{minutes}m {seconds}s"

        # Determine success
        clue_percentage = (len(self.clues_found) / self.total_clues) * 100 if self.total_clues > 0 else 0
        is_success = clue_percentage >= 60  # Need at least 60% of clues

        if is_success:
            conclusion = case.conclusion_success
            conclusion = conclusion.replace("{clues_found}", str(len(self.clues_found)))
            conclusion = conclusion.replace("{total_clues}", str(self.total_clues))
            conclusion = conclusion.replace("{time_taken}", time_str)

            panel = Panel(
                Align.center(Text(conclusion.strip(), style="white")),
                title=f"[bold {Theme.SUCCESS}]CASE CLOSED[/bold {Theme.SUCCESS}]",
                border_style=Theme.SUCCESS,
                padding=(1, 2)
            )

            # Award XP
            xp_reward = case.rewards.get('xp', 500)
            self.player.xp += xp_reward

            # Track solved mystery
            if case.id not in self.player.solved_mysteries:
                self.player.solved_mysteries.append(case.id)

        else:
            conclusion = case.conclusion_failure
            panel = Panel(
                Align.center(Text(conclusion.strip(), style="white")),
                title=f"[bold {Theme.ERROR}]CASE UNSOLVED[/bold {Theme.ERROR}]",
                border_style=Theme.ERROR,
                padding=(1, 2)
            )
            xp_reward = 50  # Consolation XP

        self.console.print(panel)

        # Show stats
        self.console.print(f"\n[bold]Investigation Summary:[/bold]")
        self.console.print(f"  Clues Found: {len(self.clues_found)}/{self.total_clues}")
        self.console.print(f"  Time Taken: {time_str}")
        self.console.print(f"  XP Earned: [bold {Theme.SUCCESS}]+{xp_reward}[/bold {Theme.SUCCESS}]")

        if self.clues_found:
            self.console.print(f"\n[bold]Evidence Collected:[/bold]")
            for clue in self.clues_found:
                self.console.print(f"  [dim]-[/dim] {clue}")

        self.console.print("\n[dim]Press ENTER to return to menu...[/dim]")
        input()
