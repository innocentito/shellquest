"""Main game engine for ShellQuest."""

import time
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from typing import Optional

from ..data.loader import DataLoader
from ..models.player import PlayerStats, PlayerSession
from ..models.achievement import AchievementSystem
from .state_manager import StateManager
from .scoring_system import ScoringSystem
from .quiz_handler import QuizHandler
from .training_handler import TrainingHandler
from ..ui.components import UIComponents
from ..ui.theme import Theme
from ..utils import logger, clear_terminal, sanitize_name
from .story_engine import StoryEngine
from .battle_engine import BattleServer, BattleClient
from .mystery_engine import MysteryEngine


class GameEngine:
    """Main game orchestrator."""

    def __init__(self):
        """Initialize game engine."""
        self.console = Console(theme=Theme.get_rich_theme())

        self.state_manager = StateManager()
        self.scoring_system = ScoringSystem()
        self.data_loader = DataLoader()

        # Load game data
        self.commands = self.data_loader.load_all_commands()
        self.questions = self.data_loader.load_all_questions()
        self.achievements_list = self.data_loader.load_achievements()
        self.achievement_system = AchievementSystem(self.achievements_list)

        # Build command-questions cache
        self.command_questions_cache = {}
        for q in self.questions:
            if q.command not in self.command_questions_cache:
                self.command_questions_cache[q.command] = []
            self.command_questions_cache[q.command].append(q)

        # Initialize handlers
        self.quiz_handler = QuizHandler(self.console, self.scoring_system)
        self.training_handler = TrainingHandler(self.console, self.scoring_system)

        # Game state
        self.player: Optional[PlayerStats] = None
        self.running = True

        logger.info(f"GameEngine initialized with {len(self.commands)} commands, {len(self.questions)} questions")

    def start(self):
        """Start the game."""
        self._show_splash()
        self._player_selection()

        while self.running:
            self._show_main_menu()

        if self.player:
            self.state_manager.save_progress(self.player)

        clear_terminal()
        self.console.print(Panel(
            Align.center(Text.assemble(
                ("\n", ""),
                ("Thanks for playing ", "bold"),
                ("ShellQuest", f"bold {Theme.PRIMARY}"),
                ("!\n\n", "bold"),
                (f"See you next time, {self.player.username}! ", Theme.SECONDARY),
                ("\n", ""),
            )),
            border_style=Theme.PANEL_BORDER_STYLE,
            padding=(1, 2)
        ))

    def _show_splash(self):
        """Show splash screen."""
        clear_terminal()
        splash = Text.assemble(
            ("\n\n", ""),
            ("    🚀 ", f"bold {Theme.PRIMARY}"),
            ("ShellQuest", f"bold {Theme.PRIMARY}"),
            (" v1.0\n", "dim"),
            ("\n    Master Bash/Zsh Commands Like a Pro\n\n", f"{Theme.SECONDARY}"),
        )
        self.console.print(Panel(Align.center(splash), border_style=Theme.PANEL_BORDER_STYLE))
        time.sleep(1)

    def _player_selection(self):
        """Handle player selection or creation."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        saved_players = self.state_manager.list_saved_players()

        if saved_players:
            self.console.print("\n[bold]Saved Players:[/bold]")
            for i, player_name in enumerate(saved_players, 1):
                self.console.print(f"  {i}. {player_name}")

            self.console.print(f"  {len(saved_players) + 1}. [bold]Create New Player[/bold]")

            choice = Prompt.ask(
                "\nSelect player or create new",
                choices=[str(i) for i in range(1, len(saved_players) + 2)]
            )

            choice_num = int(choice)
            if choice_num <= len(saved_players):
                username = saved_players[choice_num - 1]
                self.player = self.state_manager.load_progress(username)
                self.console.print(f"\n[bold green]Welcome back, {username}![/bold green]")
            else:
                self._create_new_player()
        else:
            self._create_new_player()

        time.sleep(1)

    def _create_new_player(self):
        """Create a new player."""
        username = Prompt.ask("\n[bold]Enter your username[/bold]")
        username = sanitize_name(username)
        self.player = self.state_manager.create_new_player(username)
        self.console.print(f"\n[bold green]Welcome to ShellQuest, {username}![/bold green]")

    def _show_main_menu(self):
        """Display main menu."""
        clear_terminal()
        self.player.level = self.scoring_system.get_level(self.player.xp)

        self.console.print(UIComponents.create_header(self.player))
        _, _, xp_needed = self.scoring_system.get_level_progress(self.player.xp)
        progress_pct = self.scoring_system.get_progress_percentage(self.player.xp)
        self.console.print(UIComponents.create_stats_panel(self.player, xp_needed, progress_pct))

        menu_options = [
            ("1", "🎯", "Quick Play"),
            ("2", "📖", "Story Mode"),
            ("3", "🔍", "Murder Mystery"),
            ("4", "⚔️", "Battle Mode"),
            ("5", "📊", "View Progress"),
            ("6", "🏆", "Achievements"),
            ("7", "📚", "Command Reference"),
            ("8", "⚙️", "Settings"),
            ("9", "👋", "Quit"),
        ]
        self.console.print(UIComponents.create_menu(menu_options))

        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"])

        actions = {
            "1": self._show_play_menu,
            "2": self._show_story_mode,
            "3": self._show_mystery_mode,
            "4": self._show_battle_menu,
            "5": self._show_progress,
            "6": self._show_achievements,
            "7": self._show_command_reference,
            "8": self._show_settings,
            "9": lambda: setattr(self, 'running', False),
        }
        actions[choice]()

    def _show_play_menu(self):
        """Show play mode selection menu."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        menu = Panel(
            Text.assemble(
                ("\n", ""),
                ("  1  ", f"bold {Theme.PRIMARY}"), ("🎯 Quick Quiz (10 Questions)\n", "white"),
                ("  2  ", f"bold {Theme.PRIMARY}"), ("🚀 Marathon (25 Questions)\n", "white"),
                ("  3  ", f"bold {Theme.PRIMARY}"), ("⚡ Speed Round (Time Attack)\n", "white"),
                ("  4  ", f"bold {Theme.PRIMARY}"), ("🎓 Practice Mode (No XP, Hints Free)\n", "white"),
                ("  5  ", f"bold {Theme.PRIMARY}"), ("🔀 Random Mix (All Difficulties)\n", "white"),
                ("  6  ", f"bold {Theme.PRIMARY}"), ("📝 Command Training (Pick a Command)\n", "white"),
                ("  7  ", f"bold {Theme.PRIMARY}"), ("↩️  Back to Menu\n", "white"),
                ("\n", ""),
            ),
            title="[bold]Select Game Mode[/bold]",
            border_style=Theme.PANEL_BORDER_STYLE
        )
        self.console.print(menu)

        choice = Prompt.ask("Select mode", choices=["1", "2", "3", "4", "5", "6", "7"])

        save_fn = lambda: self.state_manager.save_progress(self.player)

        if choice == "1":
            self.quiz_handler.run_quiz(self.player, self.questions, "essential", 10,
                                       self.achievement_system, save_fn)
        elif choice == "2":
            self.quiz_handler.run_quiz(self.player, self.questions, "essential", 25,
                                       self.achievement_system, save_fn)
        elif choice == "3":
            self.quiz_handler.run_speed_round(self.player, self.questions, save_fn)
        elif choice == "4":
            self.quiz_handler.run_practice_mode(self.player, self.questions)
        elif choice == "5":
            self.quiz_handler.run_quiz(self.player, self.questions, "mixed", 15,
                                       self.achievement_system, save_fn)
        elif choice == "6":
            self.training_handler.show_command_training(
                self.player, self.commands, self.command_questions_cache, save_fn
            )

    def _show_story_mode(self):
        """Show story mode."""
        story = StoryEngine(self.console, self.questions, self.player)
        story.run_story_mode()
        self.state_manager.save_progress(self.player)

    def _show_mystery_mode(self):
        """Show murder mystery mode."""
        mystery = MysteryEngine(self.console, self.player)
        mystery.run_mystery_mode()
        self.state_manager.save_progress(self.player)

    def _show_battle_menu(self):
        """Show battle mode menu."""
        clear_terminal()
        self.console.print(UIComponents.create_header())

        self.console.print(f"\n[bold]⚔️ BATTLE MODE[/bold]")
        self.console.print(f"\n[dim]Your Battle Record:[/dim]")
        self.console.print(f"  Wins: [bold green]{self.player.battles_won}[/bold green]")
        self.console.print(f"  Losses: [bold red]{self.player.battles_lost}[/bold red]")
        self.console.print(f"  Total: {self.player.battles_played}\n")

        menu = Panel(
            Text.assemble(
                ("\n", ""),
                ("  1  ", f"bold {Theme.PRIMARY}"), ("🏠 Host Game\n", "white"),
                ("  2  ", f"bold {Theme.PRIMARY}"), ("🔗 Join Game\n", "white"),
                ("  3  ", f"bold {Theme.PRIMARY}"), ("↩️  Back\n", "white"),
                ("\n", ""),
            ),
            title="[bold]Select Option[/bold]",
            border_style=Theme.WARNING
        )
        self.console.print(menu)

        choice = Prompt.ask("Select option", choices=["1", "2", "3"])

        if choice == "1":
            self._host_battle()
        elif choice == "2":
            self._join_battle()

    def _host_battle(self):
        """Host a battle game."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print("\n[bold]🏠 Host Battle[/bold]\n")

        num_questions = Prompt.ask("How many questions?", choices=["3", "5", "10"], default="5")

        server = BattleServer(self.console, self.player, self.questions)
        server.host_game(int(num_questions))
        self.state_manager.save_progress(self.player)

    def _join_battle(self):
        """Join a battle game."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print("\n[bold]🔗 Join Battle[/bold]\n")

        host_ip = Prompt.ask("Host IP")

        if host_ip.strip():
            client = BattleClient(self.console, self.player)
            client.join_game(host_ip.strip())
            self.state_manager.save_progress(self.player)

    def _show_progress(self):
        """Show player progress."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print(UIComponents.create_progress_summary(self.player))
        self.console.print("\n[dim]Press ENTER to return to menu...[/dim]")
        input()

    def _show_achievements(self):
        """Show achievements."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print("\n[bold]🏆 Achievements[/bold]\n")

        unlocked_ids = set(self.player.unlocked_achievements)

        for achievement in self.achievements_list:
            rarity_style = Theme.get_rarity_style(achievement.rarity)
            if achievement.id in unlocked_ids:
                self.console.print(f"  {achievement.icon} ", end="")
                self.console.print(f"{achievement.name}", style=f"bold {rarity_style}", end="")
                self.console.print(f" - {achievement.description}", style="dim")
            else:
                self.console.print(f"  🔒 ??? - {achievement.rarity.title()}", style="dim")

        self.console.print(f"\n[bold]Unlocked: {len(unlocked_ids)}/{len(self.achievements_list)}[/bold]")
        self.console.print("\n[dim]Press ENTER to return to menu...[/dim]")
        input()

    def _show_command_reference(self):
        """Show command reference browser."""
        while True:
            clear_terminal()
            self.console.print(UIComponents.create_header())
            self.console.print("\n[bold]📚 Command Reference[/bold]\n")

            categories = {}
            for cmd in self.commands:
                if cmd.category not in categories:
                    categories[cmd.category] = []
                categories[cmd.category].append(cmd)

            cat_list = list(categories.keys())
            for i, cat in enumerate(cat_list, 1):
                self.console.print(f"  {i}. {cat} ({len(categories[cat])} commands)")

            self.console.print(f"  {len(cat_list) + 1}. ↩️  Back")

            choice = Prompt.ask("Select category", choices=[str(i) for i in range(1, len(cat_list) + 2)])

            if int(choice) > len(cat_list):
                break

            self._show_category_commands(categories[cat_list[int(choice) - 1]])

    def _show_category_commands(self, commands):
        """Show commands in a category."""
        while True:
            clear_terminal()
            self.console.print(UIComponents.create_header())
            self.console.print(f"\n[bold]Commands[/bold]\n")

            for i, cmd in enumerate(commands, 1):
                self.console.print(f"  {i}. {cmd.name} - {cmd.description[:40]}...")

            self.console.print(f"  {len(commands) + 1}. ↩️  Back")

            choice = Prompt.ask("Select command", choices=[str(i) for i in range(1, len(commands) + 2)])

            if int(choice) > len(commands):
                break

            clear_terminal()
            self.console.print(UIComponents.create_command_card(commands[int(choice) - 1]))
            self.console.print("\n[dim]Press ENTER to go back...[/dim]")
            input()

    def _show_settings(self):
        """Show settings menu."""
        while True:
            clear_terminal()
            self.console.print(UIComponents.create_header())

            menu = Panel(
                Text.assemble(
                    ("\n", ""),
                    ("  1  ", f"bold {Theme.PRIMARY}"), ("👤 Edit Profile\n", "white"),
                    ("  2  ", f"bold {Theme.PRIMARY}"), ("🔄 Reset Progress\n", "white"),
                    ("  3  ", f"bold {Theme.PRIMARY}"), ("🏆 Reset Achievements\n", "white"),
                    ("  4  ", f"bold {Theme.PRIMARY}"), ("🗑️  Delete Account\n", "white"),
                    ("  5  ", f"bold {Theme.PRIMARY}"), ("👥 Switch Player\n", "white"),
                    ("  6  ", f"bold {Theme.PRIMARY}"), ("↩️  Back\n", "white"),
                    ("\n", ""),
                ),
                title="[bold]⚙️ Settings[/bold]",
                border_style=Theme.PANEL_BORDER_STYLE
            )
            self.console.print(menu)

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"])

            if choice == "1":
                self._edit_profile()
            elif choice == "2":
                self._reset_progress()
            elif choice == "3":
                self._reset_achievements()
            elif choice == "4":
                if self._delete_account():
                    return
            elif choice == "5":
                self._switch_player()
                return
            elif choice == "6":
                break

    def _edit_profile(self):
        """Edit player profile."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print(f"\n[bold]👤 Edit Profile[/bold]")
        self.console.print(f"\nCurrent username: [bold]{self.player.username}[/bold]\n")

        new_name = Prompt.ask("Enter new username (or press Enter to keep current)")

        if new_name.strip():
            old_name = self.player.username
            new_name = sanitize_name(new_name)
            self.player.username = new_name

            self.state_manager.save_progress(self.player)
            if old_name != new_name:
                self.state_manager.delete_save(old_name)

            self.console.print(f"\n[bold green]Username changed to: {self.player.username}[/bold green]")
        else:
            self.console.print("\n[dim]Username unchanged.[/dim]")

        time.sleep(1.5)

    def _reset_progress(self):
        """Reset player progress."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print(f"\n[bold {Theme.WARNING}]⚠️ Reset Progress[/bold {Theme.WARNING}]")
        self.console.print("\nThis will reset XP, Level, Streak, and Stats.")
        self.console.print("[bold]Achievements will be kept![/bold]")

        if Confirm.ask("\nAre you sure?", default=False):
            kept_achievements = self.player.unlocked_achievements.copy()

            self.player.xp = 0
            self.player.level = 1
            self.player.streak = 0
            self.player.best_streak = 0
            self.player.total_questions_answered = 0
            self.player.correct_answers = 0
            self.player.command_stats = {}
            self.player.essential_progress = {}
            self.player.advanced_progress = {}
            self.player.recently_answered = []
            self.player.unlocked_achievements = kept_achievements

            self.state_manager.save_progress(self.player)
            self.console.print(f"\n[bold green]Progress reset![/bold green]")
        else:
            self.console.print("\n[dim]Cancelled.[/dim]")

        time.sleep(1.5)

    def _reset_achievements(self):
        """Reset all achievements."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print(f"\n[bold {Theme.WARNING}]⚠️ Reset Achievements[/bold {Theme.WARNING}]")
        self.console.print(f"\nYou have {len(self.player.unlocked_achievements)} achievements.")

        if Confirm.ask("\nAre you sure?", default=False):
            self.player.unlocked_achievements = []
            self.state_manager.save_progress(self.player)
            self.console.print(f"\n[bold green]Achievements reset![/bold green]")
        else:
            self.console.print("\n[dim]Cancelled.[/dim]")

        time.sleep(1.5)

    def _delete_account(self) -> bool:
        """Delete player account."""
        clear_terminal()
        self.console.print(UIComponents.create_header())
        self.console.print(f"\n[bold {Theme.ERROR}]🗑️ Delete Account[/bold {Theme.ERROR}]")
        self.console.print(f"\n[bold]Player: {self.player.username}[/bold]")
        self.console.print(f"[bold red]This cannot be undone![/bold red]")

        confirm_name = Prompt.ask(f"\nType '{self.player.username}' to confirm")

        if confirm_name == self.player.username:
            self.state_manager.delete_save(self.player.username)
            self.console.print(f"\n[bold green]Account deleted.[/bold green]")
            time.sleep(1.5)

            self.player = None
            self._player_selection()
            return True
        else:
            self.console.print("\n[dim]Cancelled.[/dim]")
            time.sleep(1.5)
            return False

    def _switch_player(self):
        """Switch to a different player."""
        self.state_manager.save_progress(self.player)
        self.console.print("\n[dim]Saving...[/dim]")
        time.sleep(0.5)
        self._player_selection()
