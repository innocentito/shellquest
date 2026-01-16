"""Quiz mode handlers for ShellQuest."""

import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt

from ..models.player import PlayerStats, PlayerSession
from ..models.question import Question
from ..ui.components import UIComponents
from ..ui.theme import Theme
from ..utils import clear_terminal, PREMIUM_HINT_COST
from .quiz_engine import QuizEngine
from .scoring_system import ScoringSystem


class QuizHandler:
    """Handles all quiz modes."""

    def __init__(self, console: Console, scoring_system: ScoringSystem):
        self.console = console
        self.scoring = scoring_system
        self.quiz_engine: Optional[QuizEngine] = None
        self.session: Optional[PlayerSession] = None

    def run_quiz(self, player: PlayerStats, questions: list, difficulty: str,
                 num_questions: int, achievement_system, on_save) -> None:
        """Run a standard quiz session."""
        if difficulty == "mixed":
            pool = questions
        else:
            pool = [q for q in questions if q.difficulty == difficulty]

        if not pool:
            self.console.print(f"\n[bold red]No questions available![/bold red]")
            time.sleep(2)
            return

        self.quiz_engine = QuizEngine(pool)
        self.session = PlayerSession()

        for q_num in range(1, num_questions + 1):
            if not self._run_single_question(player, q_num, num_questions, achievement_system):
                break

        self._show_session_summary(player)
        on_save()

    def run_speed_round(self, player: PlayerStats, questions: list, on_save) -> None:
        """Run speed round - 60 seconds, as many as possible."""
        if not questions:
            self.console.print(f"\n[bold red]No questions available![/bold red]")
            time.sleep(2)
            return

        self.quiz_engine = QuizEngine(questions)
        self.session = PlayerSession()

        clear_terminal()
        self.console.print(Panel(
            Align.center(Text.assemble(
                ("\n⚡ SPEED ROUND ⚡\n\n", f"bold {Theme.WARNING}"),
                ("Answer as many questions as possible!\n", "white"),
                ("You have 60 seconds.\n\n", "dim"),
                ("Press ENTER to start...\n", "bold"),
            )),
            border_style=Theme.WARNING
        ))
        input()

        start_time = time.time()
        time_limit = 60
        q_num = 0

        while (time.time() - start_time) < time_limit:
            q_num += 1
            remaining = int(time_limit - (time.time() - start_time))
            if not self._run_speed_question(player, q_num, remaining):
                break

        self._show_session_summary(player)
        on_save()

    def run_practice_mode(self, player: PlayerStats, questions: list) -> None:
        """Run practice mode - no XP, free hints."""
        if not questions:
            self.console.print(f"\n[bold red]No questions available![/bold red]")
            time.sleep(2)
            return

        self.quiz_engine = QuizEngine(questions)
        self.session = PlayerSession()

        clear_terminal()
        self.console.print(Panel(
            Align.center(Text.assemble(
                ("\n🎓 PRACTICE MODE 🎓\n\n", f"bold {Theme.INFO}"),
                ("• No XP gained or lost\n", "white"),
                ("• Hints are free\n", "white"),
                ("• Learn at your own pace\n", "white"),
                ("\nPress ENTER to start...\n", "dim"),
            )),
            border_style=Theme.INFO
        ))
        input()

        q_num = 0
        while True:
            q_num += 1
            if not self._run_practice_question(player, q_num):
                break

        clear_terminal()
        self.console.print(Panel(
            Align.center(Text.assemble(
                ("\n🎓 Practice Complete!\n\n", f"bold {Theme.INFO}"),
                (f"Questions: {self.session.questions_this_session}\n", "white"),
                (f"Accuracy: {self.session.session_accuracy:.1f}%\n\n", "bold"),
            )),
            border_style=Theme.INFO
        ))
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()

    def _run_single_question(self, player: PlayerStats, q_num: int, total: int,
                             achievement_system) -> bool:
        """Run a single question in standard quiz."""
        question = self.quiz_engine.select_next_question(player, self.session)
        if not question:
            return False

        clear_terminal()
        self.console.print(UIComponents.create_header())
        _, _, xp_needed = self.scoring.get_level_progress(player.xp)
        progress_pct = self.scoring.get_progress_percentage(player.xp)
        self.console.print(UIComponents.create_stats_panel(player, xp_needed, progress_pct))
        self.console.print(UIComponents.create_question_panel(question, q_num, total))
        self.console.print(f"\n[dim][H] Hint  [P] Premium Hint ({PREMIUM_HINT_COST}💎)  [S] Skip  [Q] Quit[/dim]\n")

        start_time = time.time()
        hint_used = False

        while True:
            user_answer = Prompt.ask("Your answer").strip()

            if user_answer.upper() == 'Q':
                return False
            elif user_answer.upper() == 'S':
                self.console.print(f"[yellow]Skipped! Answer was: {question.correct_answer[0]}[/yellow]")
                player.record_answer(question.command, False, question.id)
                self.session.record_question(question.type.value, False, 0)
                self.console.print("\n[dim]Press ENTER to continue...[/dim]")
                input()
                return True
            elif user_answer.upper() == 'H':
                hint = self.quiz_engine.get_hint()
                self.console.print(f"\n[bold {Theme.INFO}]Hint:[/bold {Theme.INFO}] {hint}\n")
                hint_used = True
                continue
            elif user_answer.upper() == 'P':
                if player.spend_credits(PREMIUM_HINT_COST):
                    premium = question.get_premium_hint()
                    self.console.print(f"\n[bold {Theme.WARNING}]💎 Premium Hint:[/bold {Theme.WARNING}] {premium}\n")
                    hint_used = True
                else:
                    self.console.print(f"[red]Not enough credits! Need {PREMIUM_HINT_COST}💎[/red]")
                continue
            else:
                break

        time_taken = time.time() - start_time
        is_correct, explanation = self.quiz_engine.validate_answer(user_answer)

        xp_gained = 0
        if is_correct:
            xp_gained = self.scoring.calculate_xp(question, time_taken, hint_used, player.streak)
            player.xp += xp_gained

        player.record_answer(question.command, is_correct, question.id)
        self.session.record_question(question.type.value, is_correct, xp_gained)

        self.console.print()
        self.console.print(UIComponents.create_result_panel(
            is_correct, explanation, xp_gained,
            user_answer if not is_correct else None,
            question.correct_answer[0] if not is_correct else None
        ))

        unlocked = achievement_system.check_achievements(player, self.session)
        for achievement in unlocked:
            self.console.print(UIComponents.create_achievement_notification(achievement))

        player.level = self.scoring.get_level(player.xp)

        if not is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)
        return True

    def _run_speed_question(self, player: PlayerStats, q_num: int, time_remaining: int) -> bool:
        """Run a single speed round question."""
        question = self.quiz_engine.select_next_question(player, self.session)
        if not question:
            return False

        clear_terminal()
        self.console.print(f"[bold {Theme.WARNING}]⏱️  Time Remaining: {time_remaining}s[/bold {Theme.WARNING}]")
        self.console.print(UIComponents.create_question_panel(question, q_num, 999))

        question_start = time.time()
        user_answer = Prompt.ask("Your answer").strip()
        time_taken = time.time() - question_start

        if user_answer.upper() == 'Q':
            return False

        is_correct, _ = self.quiz_engine.validate_answer(user_answer)
        xp_gained = 0

        if is_correct:
            xp_gained = self.scoring.calculate_xp(question, time_taken, False, player.streak)
            player.xp += xp_gained
            self.console.print(f"[bold {Theme.SUCCESS}]✓ Correct! +{xp_gained} XP[/bold {Theme.SUCCESS}]")
        else:
            self.console.print(f"[bold {Theme.ERROR}]✗ Wrong![/bold {Theme.ERROR}]")
            self.console.print(f"[white]Correct answer: {question.correct_answer[0]}[/white]")

        player.record_answer(question.command, is_correct, question.id)
        self.session.record_question(question.type.value, is_correct, xp_gained)

        if not is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)
        return True

    def _run_practice_question(self, player: PlayerStats, q_num: int) -> bool:
        """Run a single practice question."""
        question = self.quiz_engine.select_next_question(player, self.session)
        if not question:
            return False

        clear_terminal()
        self.console.print(f"[bold {Theme.INFO}]🎓 Practice Mode - Question {q_num}[/bold {Theme.INFO}]")
        self.console.print(UIComponents.create_question_panel(question, q_num, 999))
        self.console.print(f"\n[dim][H] Free Hint  [P] Premium ({PREMIUM_HINT_COST}💎)  [S] Skip  [Q] Quit[/dim]\n")

        while True:
            user_answer = Prompt.ask("Your answer").strip()

            if user_answer.upper() == 'Q':
                return False
            elif user_answer.upper() == 'S':
                self.console.print(f"[yellow]Answer was: {question.correct_answer[0]}[/yellow]")
                self.console.print("\n[dim]Press ENTER to continue...[/dim]")
                input()
                return True
            elif user_answer.upper() == 'H':
                self.console.print(f"\n[bold {Theme.INFO}]Hint:[/bold {Theme.INFO}] {question.get_hint()}\n")
                continue
            elif user_answer.upper() == 'P':
                if player.spend_credits(PREMIUM_HINT_COST):
                    self.console.print(f"\n[bold {Theme.WARNING}]💎 Premium Hint:[/bold {Theme.WARNING}] {question.get_premium_hint()}\n")
                else:
                    self.console.print(f"[red]Not enough credits![/red]")
                continue
            else:
                break

        is_correct, explanation = self.quiz_engine.validate_answer(user_answer)

        if is_correct:
            self.console.print(f"\n[bold {Theme.SUCCESS}]✓ Correct![/bold {Theme.SUCCESS}]")
        else:
            self.console.print(f"\n[bold {Theme.ERROR}]✗ Incorrect[/bold {Theme.ERROR}]")
            self.console.print(f"[white]Correct answer: {question.correct_answer[0]}[/white]")

        self.console.print(f"[dim]{explanation}[/dim]")
        self.session.record_question(question.type.value, is_correct, 0)

        if not is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)
        return True

    def _show_session_summary(self, player: PlayerStats) -> None:
        """Show quiz session summary."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        summary = Panel(
            Text.assemble(
                ("\nSession Complete!\n\n", "bold"),
                (f"Questions Answered: {self.session.questions_this_session}\n", "white"),
                (f"Correct Answers: {self.session.correct_this_session}\n", Theme.SUCCESS),
                (f"Accuracy: {self.session.session_accuracy:.1f}%\n", "white"),
                (f"XP Earned: +{self.session.xp_earned_this_session}\n", f"bold {Theme.SUCCESS}"),
                (f"\nCurrent Level: {player.level} ⭐\n", f"bold {Theme.PRIMARY}"),
            ),
            title="[bold]📊 Session Summary[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE
        )

        self.console.print(summary)
        self.console.print("\n[dim]Press ENTER to return to menu...[/dim]")
        input()
