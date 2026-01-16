"""Entry point for ShellQuest."""

import sys
from rich.console import Console

from .utils import logger


def main():
    """Main entry point for the game."""
    console = Console()

    try:
        logger.info("ShellQuest starting...")

        from .core.game_engine import GameEngine
        game = GameEngine()
        game.start()

        logger.info("ShellQuest exited normally")

    except KeyboardInterrupt:
        console.print("\n\n[bold]Game interrupted. Progress saved. Goodbye![/bold]\n")
        logger.info("ShellQuest interrupted by user")
        sys.exit(0)

    except ImportError as e:
        console.print(f"\n[bold red]Missing dependency:[/bold red] {e}\n")
        console.print("Try running: [bold]pip install rich pyyaml[/bold]\n")
        logger.error(f"Import error: {e}")
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[bold red]An error occurred:[/bold red] {e}\n")
        console.print("[dim]Check ~/.shellquest/logs/shellquest.log for details.[/dim]\n")
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
