"""Utility functions and helpers for ShellQuest."""

import logging
import os
import sys
import re
from pathlib import Path
from typing import Optional
from functools import wraps
from rich.console import Console


# ============================================================================
# CONSTANTS - Centralized configuration values
# ============================================================================

MAX_NAME_LENGTH = 32
PREMIUM_HINT_COST = 40
DEFAULT_STARTING_CREDITS = 100
CREDITS_PER_CORRECT_ANSWER = 10
DEFAULT_PORT = 5555
BUFFER_SIZE = 8192
SOCKET_TIMEOUT = 60

# Configure logging
LOG_DIR = Path.home() / ".shellquest" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str = "shellquest", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    # File handler - detailed logs
    log_file = LOG_DIR / "shellquest.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()


class ShellQuestError(Exception):
    """Base exception for ShellQuest."""
    pass


class DataLoadError(ShellQuestError):
    """Raised when data loading fails."""
    pass


class SaveError(ShellQuestError):
    """Raised when saving progress fails."""
    pass


class LoadError(ShellQuestError):
    """Raised when loading progress fails."""
    pass


def safe_path(path: Path) -> Path:
    """
    Ensure a path is safe and exists.

    Args:
        path: Path to validate

    Returns:
        Validated path
    """
    path = Path(path).resolve()
    return path


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def calculate_percentage(value: int, total: int) -> float:
    """
    Safely calculate a percentage.

    Args:
        value: Numerator
        total: Denominator

    Returns:
        Percentage (0-100) or 0 if total is 0
    """
    if total == 0:
        return 0.0
    return (value / total) * 100


def clear_terminal(include_scrollback: bool = True):
    """
    Clear the terminal screen.

    Args:
        include_scrollback: If True, also clears scrollback buffer
                           (no history visible when scrolling up)
    """
    if include_scrollback:
        # ANSI escape sequences:
        # \033[2J - Clear entire screen
        # \033[3J - Clear scrollback buffer
        # \033[H  - Move cursor to home position
        if sys.platform == "win32":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[3J\033[H")
            sys.stdout.flush()
    else:
        # Just clear visible area (Rich console default behavior)
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def sanitize_name(name: str) -> str:
    """
    Sanitize player name to prevent injection attacks.

    Args:
        name: Raw input name from user

    Returns:
        Sanitized name safe for display and storage
    """
    # Remove any control characters first
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
    # Remove Rich markup tags to prevent formatting injection
    # Match [tag], [tag=value], [/tag] patterns
    name = re.sub(r'\[/?[a-zA-Z_][a-zA-Z0-9_]*(?:=[^\]]+)?\]', '', name)
    # Remove path traversal characters and dangerous filesystem chars
    name = re.sub(r'[\\/:*?"<>|.]', '', name)
    # Trim whitespace and limit length
    name = name.strip()[:MAX_NAME_LENGTH]
    return name if name else "Player"
