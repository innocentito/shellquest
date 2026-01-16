"""Training mode handler for ShellQuest."""

import time
from typing import Optional, Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt

from ..models.player import PlayerStats, PlayerSession
from ..models.command import Command
from ..ui.components import UIComponents
from ..ui.theme import Theme
from ..utils import clear_terminal, PREMIUM_HINT_COST
from .quiz_engine import QuizEngine
from .scoring_system import ScoringSystem


class TrainingHandler:
    """Handles command training mode."""

    def __init__(self, console: Console, scoring_system: ScoringSystem):
        self.console = console
        self.scoring = scoring_system
        self.quiz_engine: Optional[QuizEngine] = None
        self.session: Optional[PlayerSession] = None

    def show_command_training(self, player: PlayerStats, commands: List[Command],
                              command_questions_cache: Dict, on_save) -> None:
        """Show command training selection menu."""
        while True:
            clear_terminal()
            self.console.print(UIComponents.create_header())
            self.console.print("\n[bold]📝 Command Training[/bold]")
            self.console.print("[dim]Select a command to practice[/dim]\n")

            categories = {
                "Navigation": ["cd", "pwd", "ls"],
                "File Viewing": ["cat", "head", "tail", "less"],
                "File Operations": ["cp", "mv", "rm", "touch", "mkdir"],
                "Search": ["grep", "find"],
                "Text Processing": ["sort", "uniq", "wc", "cut", "awk", "sed"],
                "Permissions & System": ["chmod", "echo", "man", "ps", "kill"],
                "Network": ["curl", "wget", "ping", "ssh"],
                "Archives": ["tar", "zip", "gzip"]
            }

            available_commands = []
            idx = 1

            for category, cmds in categories.items():
                cat_cmds = [(c, len(command_questions_cache.get(c, [])))
                           for c in cmds if c in command_questions_cache]
                if cat_cmds:
                    self.console.print(f"\n[bold {Theme.PRIMARY}]{category}[/bold {Theme.PRIMARY}]")
                    for cmd, count in cat_cmds:
                        mastery = self._get_command_mastery(player, cmd)
                        icon = self._get_mastery_icon(mastery)
                        self.console.print(f"  {idx}. {icon} [bold]{cmd}[/bold] [dim]({count} questions)[/dim]")
                        available_commands.append(cmd)
                        idx += 1

            # Other commands not in categories
            sorted_commands = sorted(command_questions_cache.items(), key=lambda x: len(x[1]), reverse=True)
            other_cmds = [(c, len(qs)) for c, qs in sorted_commands
                         if c not in sum(categories.values(), [])]
            if other_cmds:
                self.console.print(f"\n[bold {Theme.PRIMARY}]Other[/bold {Theme.PRIMARY}]")
                for cmd, count in other_cmds:
                    mastery = self._get_command_mastery(player, cmd)
                    icon = self._get_mastery_icon(mastery)
                    self.console.print(f"  {idx}. {icon} [bold]{cmd}[/bold] [dim]({count} questions)[/dim]")
                    available_commands.append(cmd)
                    idx += 1

            self.console.print(f"\n  {idx}. ↩️  Back to Menu")
            self.console.print("\n[dim]Legend: 🟢 Mastered  🟡 Learning  🔴 Needs Practice  ⚪ Not Started[/dim]\n")

            choices = [str(i) for i in range(1, idx + 1)]
            choice = Prompt.ask("Select command", choices=choices)

            if int(choice) >= idx:
                break

            selected_command = available_commands[int(choice) - 1]
            self._run_command_training(
                player, selected_command,
                command_questions_cache[selected_command],
                commands, on_save
            )

    def _run_command_training(self, player: PlayerStats, command: str,
                              questions: list, all_commands: List[Command], on_save) -> None:
        """Run training for a specific command."""
        clear_terminal()

        cmd_info = next((c for c in all_commands if c.name == command), None)

        intro_parts = [
            ("\n", ""),
            (f"📝 Training: ", "bold"),
            (f"{command}\n\n", f"bold {Theme.PRIMARY}"),
        ]

        if cmd_info:
            intro_parts.extend([
                (f"{cmd_info.description}\n", "white"),
                (f"\nSyntax: ", "bold"),
                (f"{cmd_info.syntax}\n", f"{Theme.INFO}"),
            ])

        intro_parts.extend([
            (f"\n{len(questions)} questions available\n", "dim"),
            (f"Answer up to 40 questions to master this command!\n\n", "white"),
            ("Press ENTER to start...\n", "dim"),
        ])

        self.console.print(Panel(
            Align.center(Text.assemble(*intro_parts)),
            border_style=Theme.PRIMARY
        ))
        input()

        self.quiz_engine = QuizEngine(questions)
        self.session = PlayerSession()

        num_questions = min(40, len(questions))
        correct_count = 0

        for q_num in range(1, num_questions + 1):
            result = self._run_training_question(player, command, q_num, num_questions, correct_count)
            if result is None:
                break
            if result:
                correct_count += 1

        self._show_training_summary(player, command, correct_count, self.session.questions_this_session)
        on_save()

    def _run_training_question(self, player: PlayerStats, command: str,
                               q_num: int, total: int, correct: int) -> Optional[bool]:
        """Run a single training question."""
        question = self.quiz_engine.select_next_question(player, self.session)
        if not question:
            return None

        clear_terminal()

        progress_pct = int((q_num / total) * 100)
        bar_filled = int(progress_pct / 5)
        bar_empty = 20 - bar_filled
        progress_bar = f"[{Theme.SUCCESS}]{'█' * bar_filled}[/{Theme.SUCCESS}][dim]{'░' * bar_empty}[/dim]"

        self.console.print(f"\n[bold]📝 {command} Training[/bold] - Question {q_num}/{total}")
        self.console.print(f"Correct: {correct}/{q_num - 1}  {progress_bar}  {progress_pct}%\n")

        self.console.print(UIComponents.create_question_panel(question, q_num, total))
        self.console.print(f"\n[dim][H] Hint  [P] Premium Hint ({PREMIUM_HINT_COST}💎)  [S] Skip  [Q] Quit[/dim]\n")

        start_time = time.time()
        hint_used = False

        while True:
            user_answer = Prompt.ask("Your answer").strip()

            if user_answer.upper() == 'Q':
                return None
            elif user_answer.upper() == 'S':
                self.console.print(f"[yellow]Skipped! Answer was: {question.correct_answer[0]}[/yellow]")
                player.record_answer(command, False, question.id)
                self.session.record_question(question.type.value, False, 0)
                time.sleep(1.5)
                return False
            elif user_answer.upper() == 'H':
                self.console.print(f"\n[bold {Theme.INFO}]Hint:[/bold {Theme.INFO}] {question.get_hint()}\n")
                hint_used = True
                continue
            elif user_answer.upper() == 'P':
                if player.spend_credits(PREMIUM_HINT_COST):
                    self.console.print(f"\n[bold {Theme.WARNING}]💎 Premium Hint:[/bold {Theme.WARNING}] {question.get_premium_hint()}\n")
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
            self.console.print(f"\n[bold {Theme.SUCCESS}]✓ Correct! +{xp_gained} XP[/bold {Theme.SUCCESS}]")
        else:
            self.console.print(f"\n[bold {Theme.ERROR}]✗ Incorrect[/bold {Theme.ERROR}]")
            self.console.print(f"[white]Answer: {question.correct_answer[0]}[/white]")

        self.console.print(f"[dim]{explanation}[/dim]")

        player.record_answer(command, is_correct, question.id)
        self.session.record_question(question.type.value, is_correct, xp_gained)

        time.sleep(1.2)
        return is_correct

    def _show_training_summary(self, player: PlayerStats, command: str,
                               correct: int, total: int) -> None:
        """Show training session summary."""
        clear_terminal()

        accuracy = (correct / total * 100) if total > 0 else 0

        if accuracy >= 90:
            grade = ("🏆 MASTERED!", Theme.WARNING)
            msg = "Outstanding! You've mastered this command!"
        elif accuracy >= 70:
            grade = ("⭐ GREAT!", Theme.SUCCESS)
            msg = "Great job! Keep practicing to master it!"
        elif accuracy >= 50:
            grade = ("📈 GOOD PROGRESS", Theme.INFO)
            msg = "You're getting there! Practice more."
        else:
            grade = ("📚 KEEP LEARNING", Theme.SECONDARY)
            msg = "Don't give up! Review and try again."

        summary = Panel(
            Align.center(Text.assemble(
                (f"\n{grade[0]}\n\n", f"bold {grade[1]}"),
                (f"Command: ", "white"),
                (f"{command}\n\n", f"bold {Theme.PRIMARY}"),
                (f"Questions: {total}\n", "white"),
                (f"Correct: {correct}\n", Theme.SUCCESS),
                (f"Accuracy: {accuracy:.1f}%\n\n", "bold"),
                (f"{msg}\n\n", "dim"),
                (f"XP Earned: +{self.session.xp_earned_this_session}\n", f"bold {Theme.SUCCESS}"),
            )),
            title=f"[bold]📝 {command} Training Complete[/bold]",
            border_style=grade[1]
        )

        self.console.print(summary)
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()

    def _get_command_mastery(self, player: PlayerStats, command: str) -> str:
        """Get mastery level for a command."""
        if command not in player.command_stats:
            return "not_started"

        stats = player.command_stats[command]
        if stats["total"] < 5:
            return "not_started"

        accuracy = stats["correct"] / stats["total"]
        if accuracy >= 0.9:
            return "mastered"
        elif accuracy >= 0.6:
            return "learning"
        else:
            return "needs_practice"

    def _get_mastery_icon(self, mastery: str) -> str:
        """Get icon for mastery level."""
        icons = {
            "mastered": "🟢",
            "learning": "🟡",
            "needs_practice": "🔴",
            "not_started": "⚪"
        }
        return icons.get(mastery, "⚪")
