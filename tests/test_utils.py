"""Unit tests for utility functions."""

import pytest
from shellquest.utils import (
    sanitize_name,
    truncate_string,
    format_duration,
    calculate_percentage,
    PREMIUM_HINT_COST,
    MAX_NAME_LENGTH,
    DEFAULT_PORT,
    CREDITS_PER_CORRECT_ANSWER,
    DEFAULT_STARTING_CREDITS
)


class TestSanitizeName:
    """Tests for sanitize_name function."""

    def test_normal_name(self):
        """Test normal name passes through."""
        assert sanitize_name("Alice") == "Alice"
        assert sanitize_name("Bob123") == "Bob123"

    def test_whitespace_trimmed(self):
        """Test whitespace is trimmed."""
        assert sanitize_name("  Alice  ") == "Alice"
        assert sanitize_name("\tBob\n") == "Bob"

    def test_control_characters_removed(self):
        """Test control characters are removed."""
        assert sanitize_name("Alice\x00Bob") == "AliceBob"
        assert sanitize_name("\x1fTest\x7f") == "Test"

    def test_rich_markup_removed(self):
        """Test Rich markup tags are removed."""
        assert sanitize_name("[bold]Alice[/bold]") == "Alice"
        assert sanitize_name("[red]Bob[/red]") == "Bob"
        assert sanitize_name("[link=http://evil.com]Click[/link]") == "Click"

    def test_length_limited(self):
        """Test name is limited to MAX_NAME_LENGTH."""
        long_name = "A" * 100
        result = sanitize_name(long_name)
        assert len(result) == MAX_NAME_LENGTH

    def test_empty_name_becomes_player(self):
        """Test empty name defaults to 'Player'."""
        assert sanitize_name("") == "Player"
        assert sanitize_name("   ") == "Player"
        assert sanitize_name("[bold][/bold]") == "Player"

    def test_combined_sanitization(self):
        """Test all sanitizations work together."""
        dangerous = "[red]\x00  Evil\x1f  [/red]"
        assert sanitize_name(dangerous) == "Evil"

    def test_path_traversal_removed(self):
        """Test path traversal characters are removed."""
        assert sanitize_name("../../../etc/passwd") == "etcpasswd"
        assert sanitize_name("..\\..\\windows") == "windows"
        assert sanitize_name("user.name") == "username"

    def test_dangerous_filesystem_chars_removed(self):
        """Test dangerous filesystem characters are removed."""
        assert sanitize_name('file:name') == "filename"
        assert sanitize_name('user*name') == "username"
        assert sanitize_name('test<>file') == "testfile"


class TestTruncateString:
    """Tests for truncate_string function."""

    def test_short_string_unchanged(self):
        """Test short strings are not modified."""
        assert truncate_string("Hello", 10) == "Hello"
        assert truncate_string("Hi", 50) == "Hi"

    def test_long_string_truncated(self):
        """Test long strings are truncated with suffix."""
        assert truncate_string("Hello World", 8) == "Hello..."
        assert truncate_string("This is a long string", 10) == "This is..."

    def test_exact_length(self):
        """Test string at exact length is unchanged."""
        assert truncate_string("Hello", 5) == "Hello"

    def test_custom_suffix(self):
        """Test custom suffix works."""
        assert truncate_string("Hello World", 9, suffix=">>") == "Hello W>>"


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_seconds_only(self):
        """Test formatting seconds."""
        assert format_duration(30) == "30.0s"
        assert format_duration(5.5) == "5.5s"

    def test_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        assert format_duration(90) == "1m 30s"
        assert format_duration(125) == "2m 5s"

    def test_exact_minute(self):
        """Test exact minute formatting."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(120) == "2m 0s"


class TestCalculatePercentage:
    """Tests for calculate_percentage function."""

    def test_normal_percentage(self):
        """Test normal percentage calculation."""
        assert calculate_percentage(50, 100) == 50.0
        assert calculate_percentage(1, 4) == 25.0

    def test_zero_total(self):
        """Test zero total returns 0."""
        assert calculate_percentage(5, 0) == 0.0

    def test_100_percent(self):
        """Test 100% calculation."""
        assert calculate_percentage(10, 10) == 100.0


class TestConstants:
    """Tests for centralized constants."""

    def test_premium_hint_cost(self):
        """Test premium hint cost is defined."""
        assert PREMIUM_HINT_COST == 40

    def test_max_name_length(self):
        """Test max name length is defined."""
        assert MAX_NAME_LENGTH == 32

    def test_default_port(self):
        """Test default port is defined."""
        assert DEFAULT_PORT == 5555

    def test_credits_per_correct(self):
        """Test credits per correct answer is defined."""
        assert CREDITS_PER_CORRECT_ANSWER == 10

    def test_default_starting_credits(self):
        """Test default starting credits is defined."""
        assert DEFAULT_STARTING_CREDITS == 100
