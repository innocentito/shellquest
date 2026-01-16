"""Reusable UI components for ShellQuest."""

from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.tree import Tree
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from typing import Dict, List
from .theme import Theme
from ..models.player import PlayerStats
from ..models.question import Question
from ..models.achievement import Achievement
from ..models.command import Command


class UIComponents:
    """Collection of reusable UI components."""

    @staticmethod
    def create_header(player: PlayerStats = None) -> Panel:
        """Create beautiful header panel."""
        title = Text()
        title.append("🚀 ", style="bold")
        title.append("ShellQuest", style=f"bold {Theme.PRIMARY}")
        title.append(" v1.0", style="dim")

        subtitle = Text()
        subtitle.append("Master Bash/Zsh Like a Pro", style=Theme.SECONDARY)

        header_text = Text()
        header_text.append(title)
        header_text.append("\n")
        header_text.append(subtitle)

        return Panel(
            Align.center(header_text),
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(0, 2)
        )

    @staticmethod
    def create_stats_panel(player: PlayerStats, xp_needed: int, progress_pct: float) -> Panel:
        """Create player statistics panel."""
        stats_table = Table.grid(padding=(0, 2))
        stats_table.add_column(justify="left")
        stats_table.add_column(justify="right")

        # Player name and level
        stats_table.add_row(
            Text(player.username, style="bold"),
            Text(f"Level {player.level} ⭐", style=Theme.PRIMARY)
        )

        # XP Progress bar
        xp_text = f"XP: {player.xp}/{player.xp + xp_needed}"
        bar_width = 30
        filled = int((progress_pct / 100) * bar_width)
        empty = bar_width - filled
        progress_bar = "█" * filled + "░" * empty
        stats_table.add_row(
            Text(xp_text, style="dim"),
            Text(f"[{progress_bar}] {progress_pct:.0f}%", style=Theme.SUCCESS)
        )

        # Streak and Accuracy
        streak_emoji = "🔥" if player.streak > 0 else ""
        streak_text = f"Streak: {player.streak} {streak_emoji}"
        accuracy_text = f"Accuracy: {player.accuracy:.0f}%"

        stats_table.add_row(
            Text(streak_text, style=Theme.get_streak_color(player.streak)),
            Text(accuracy_text, style="dim")
        )

        # Credits display
        credits_text = f"Credits: {player.credits}💎"
        stats_table.add_row(
            Text(credits_text, style=Theme.WARNING),
            Text("", style="dim")  # Empty right column for balance
        )

        return Panel(
            stats_table,
            title="[bold]Player Stats[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(0, 1)
        )

    @staticmethod
    def create_question_panel(question: Question, question_num: int, total: int) -> Panel:
        """Create question display panel."""
        # Question header
        header_parts = []
        header_parts.append(f"Question {question_num}/{total}")
        header_parts.append(f"Type: {question.type.value.replace('_', ' ').title()}")
        header_parts.append(f"Points: {question.points}")

        header = " • ".join(header_parts)

        # Question text
        q_text = Text()
        q_text.append(f"\n{question.question_text}\n\n", style="bold white")

        # Options (for multiple choice)
        if question.options:
            for i, option in enumerate(question.options):
                letter = chr(65 + i)  # A, B, C, D
                q_text.append(f"  {letter}) ", style=Theme.PRIMARY)
                q_text.append(f"{option}\n", style="white")

            # Add input instruction for multiple choice
            num_options = len(question.options)
            letters = '/'.join([chr(65 + i) for i in range(num_options)])
            numbers = '/'.join([str(i + 1) for i in range(num_options)])
            q_text.append(f"\n[dim]💡 Enter {letters} or {numbers}[/dim]\n", style="dim")

        q_text.append("\n")

        difficulty_badge = "⭐" if question.difficulty == "essential" else "🚀"
        title = f"[{Theme.get_difficulty_style(question.difficulty)}]{difficulty_badge} {header}[/]"

        return Panel(
            q_text,
            title=title,
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(0, 2)
        )

    @staticmethod
    def create_result_panel(is_correct: bool, explanation: str, xp_gained: int, user_answer: str = None, correct_answer: str = None) -> Panel:
        """Create result display panel.

        Args:
            is_correct: Whether the answer was correct
            explanation: Explanation text for the answer
            xp_gained: XP points gained (only used if correct)
            user_answer: What the user answered (shown if incorrect)
            correct_answer: What the correct answer was (shown if incorrect)
        """
        if is_correct:
            title_text = Text("✓ CORRECT! ✓", style=f"bold {Theme.SUCCESS}")
            border_style = Theme.SUCCESS
        else:
            title_text = Text("✗ INCORRECT ✗", style=f"bold {Theme.ERROR}")
            border_style = Theme.ERROR

        content = Text()
        content.append("\n", style="bold")
        content.append(explanation, style="white")
        content.append("\n\n")

        if is_correct:
            content.append(f"XP Earned: +{xp_gained}", style=f"bold {Theme.SUCCESS}")
        else:
            content.append("Better luck next time!\n\n", style="dim")

            if user_answer is not None:
                content.append("Your answer: ", style="dim")
                content.append(f"{user_answer}\n", style=f"bold {Theme.ERROR}")

            if correct_answer is not None:
                content.append("Correct answer: ", style="dim")
                content.append(f"{correct_answer}", style=f"bold {Theme.SUCCESS}")

        content.append("\n")

        return Panel(
            Align.center(content),
            title=title_text,
            border_style=border_style,
            padding=(0, 2)
        )

    @staticmethod
    def create_xp_breakdown(base_xp: int, multipliers: Dict[str, float], total_xp: int) -> Panel:
        """Create XP breakdown panel."""
        breakdown = Table.grid(padding=(0, 2))
        breakdown.add_column(justify="left")
        breakdown.add_column(justify="right")

        breakdown.add_row("Base Points:", f"{base_xp}", style="white")

        for mult_name, mult_value in multipliers.items():
            if mult_value != 1.0:
                bonus = int(base_xp * (mult_value - 1.0))
                sign = "+" if bonus >= 0 else ""
                breakdown.add_row(
                    f"{mult_name}:",
                    f"{sign}{bonus}",
                    style=Theme.SUCCESS if bonus > 0 else Theme.ERROR
                )

        breakdown.add_row("─" * 20, "─" * 10, style="dim")
        breakdown.add_row(
            "Total XP:",
            f"{total_xp}",
            style=f"bold {Theme.SUCCESS}"
        )

        return Panel(
            breakdown,
            title="[bold]Rewards[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE
        )

    @staticmethod
    def create_achievement_notification(achievement: Achievement) -> Panel:
        """Create achievement unlock notification."""
        content = Text()
        content.append(f"\n{achievement.icon} ", style="bold")
        content.append(f"{achievement.name}\n", style=f"bold {Theme.get_rarity_style(achievement.rarity)}")
        content.append(f"{achievement.description}\n\n", style="white")
        content.append(f"+{achievement.xp_reward} Bonus XP!\n", style=f"bold {Theme.SUCCESS}")

        return Panel(
            Align.center(content),
            title="[bold]🎉 Achievement Unlocked! 🎉[/bold]",
            border_style=Theme.WARNING,
            padding=(0, 2)
        )

    @staticmethod
    def create_menu(options: List[tuple]) -> Panel:
        """
        Create menu panel.

        Args:
            options: List of (number, emoji, text) tuples
        """
        menu_text = Text("\n")

        for num, emoji, text in options:
            menu_text.append(f"  {num}  ", style=Theme.PRIMARY)
            menu_text.append(f"{emoji} {text}\n", style="white")

        menu_text.append("\n")

        return Panel(
            menu_text,
            title="[bold]Main Menu[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(0, 2)
        )

    @staticmethod
    def create_command_card(command: Command) -> Panel:
        """Create detailed command reference card."""
        content = Text()

        # Syntax
        content.append("Syntax: ", style="bold")
        content.append(f"{command.syntax}\n\n", style=Theme.PRIMARY)

        # Description
        content.append(f"{command.description}\n\n", style="white")

        # Common options
        if command.common_options:
            content.append("Common Options:\n", style="bold")
            for opt in command.common_options[:3]:  # Limit to 3
                content.append(f"  {opt.name}", style=Theme.SECONDARY)
                content.append(f"  {opt.description}\n", style="dim")
            content.append("\n")

        # Examples
        if command.examples:
            content.append("Examples:\n", style="bold")
            for ex in command.examples[:2]:  # Limit to 2
                content.append(f"  $ {ex.command}\n", style=Theme.PRIMARY)
                content.append(f"    {ex.explanation}\n", style="dim")

        return Panel(
            content,
            title=f"[bold]{command.name}[/bold]",
            subtitle=f"[dim]{command.category}[/dim]",
            border_style=Theme.PANEL_BORDER_STYLE
        )

    @staticmethod
    def create_progress_summary(player: PlayerStats) -> Panel:
        """Create progress summary panel."""
        content = Text()

        content.append("\nOverall Progress\n\n", style="bold")

        # Essential commands progress
        essential_mastered = sum(1 for v in player.essential_progress.values() if v)
        content.append("Essential Commands: ", style="white")
        content.append(f"{essential_mastered} mastered\n", style=Theme.SUCCESS)

        # Advanced commands progress
        advanced_mastered = sum(1 for v in player.advanced_progress.values() if v)
        content.append("Advanced Commands: ", style="white")
        content.append(f"{advanced_mastered} mastered\n", style=Theme.WARNING)

        content.append("\n")

        # Stats
        content.append(f"Total Questions: {player.total_questions_answered}\n", style="dim")
        content.append(f"Correct Answers: {player.correct_answers}\n", style="dim")
        content.append(f"Best Streak: {player.best_streak} 🔥\n", style="dim")

        # Achievements
        content.append(f"\nAchievements: {len(player.unlocked_achievements)}\n", style="dim")

        return Panel(
            content,
            title="[bold]📊 Your Progress[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE
        )
