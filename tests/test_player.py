"""Unit tests for PlayerStats and PlayerSession models."""

import pytest
from shellquest.models.player import PlayerStats, PlayerSession


class TestPlayerStatsCreation:
    """Tests for PlayerStats creation."""

    def test_create_player_with_username(self):
        """Test creating a player with just a username."""
        player = PlayerStats(username="TestUser")
        assert player.username == "TestUser"
        assert player.level == 1
        assert player.xp == 0
        assert player.credits == 100

    def test_default_values(self):
        """Test all default values are set correctly."""
        player = PlayerStats(username="Test")
        assert player.total_questions_answered == 0
        assert player.correct_answers == 0
        assert player.streak == 0
        assert player.best_streak == 0
        assert player.battles_won == 0
        assert player.battles_lost == 0
        assert player.essential_progress == {}
        assert player.advanced_progress == {}
        assert player.unlocked_achievements == []


class TestAccuracy:
    """Tests for accuracy property."""

    def test_accuracy_zero_questions(self):
        """Test accuracy is 0 when no questions answered."""
        player = PlayerStats(username="Test")
        assert player.accuracy == 0.0

    def test_accuracy_100_percent(self):
        """Test 100% accuracy."""
        player = PlayerStats(username="Test")
        player.total_questions_answered = 10
        player.correct_answers = 10
        assert player.accuracy == 100.0

    def test_accuracy_50_percent(self):
        """Test 50% accuracy."""
        player = PlayerStats(username="Test")
        player.total_questions_answered = 10
        player.correct_answers = 5
        assert player.accuracy == 50.0


class TestRecordAnswer:
    """Tests for record_answer method."""

    def test_record_correct_answer(self):
        """Test recording a correct answer."""
        player = PlayerStats(username="Test")
        initial_credits = player.credits

        player.record_answer("ls", True, "q1")

        assert player.total_questions_answered == 1
        assert player.correct_answers == 1
        assert player.streak == 1
        assert player.credits == initial_credits + 10

    def test_record_wrong_answer(self):
        """Test recording a wrong answer."""
        player = PlayerStats(username="Test")
        initial_credits = player.credits

        player.record_answer("ls", False, "q1")

        assert player.total_questions_answered == 1
        assert player.correct_answers == 0
        assert player.streak == 0
        assert player.credits == initial_credits  # No credits for wrong

    def test_streak_increases_on_correct(self):
        """Test streak increases with consecutive correct answers."""
        player = PlayerStats(username="Test")

        player.record_answer("ls", True, "q1")
        player.record_answer("cd", True, "q2")
        player.record_answer("pwd", True, "q3")

        assert player.streak == 3
        assert player.best_streak == 3

    def test_streak_resets_on_wrong(self):
        """Test streak resets on wrong answer."""
        player = PlayerStats(username="Test")

        player.record_answer("ls", True, "q1")
        player.record_answer("cd", True, "q2")
        player.record_answer("pwd", False, "q3")

        assert player.streak == 0
        assert player.best_streak == 2

    def test_command_stats_tracked(self):
        """Test command statistics are tracked."""
        player = PlayerStats(username="Test")

        player.record_answer("ls", True, "q1")
        player.record_answer("ls", True, "q2")
        player.record_answer("ls", False, "q3")

        assert player.command_stats["ls"]["total"] == 3
        assert player.command_stats["ls"]["correct"] == 2

    def test_recently_answered_limited_to_50(self):
        """Test recently answered list is capped at 50."""
        player = PlayerStats(username="Test")

        for i in range(60):
            player.record_answer("ls", True, f"q{i}")

        assert len(player.recently_answered) == 50
        assert player.recently_answered[0] == "q10"
        assert player.recently_answered[-1] == "q59"


class TestWeakAndStrongAreas:
    """Tests for weak_areas and strong_areas properties."""

    def test_weak_areas_below_60_percent(self):
        """Test commands with <60% accuracy are weak areas."""
        player = PlayerStats(username="Test")
        player.command_stats["grep"] = {"correct": 1, "total": 5}  # 20%

        assert "grep" in player.weak_areas

    def test_strong_areas_above_90_percent(self):
        """Test commands with >=90% accuracy are strong areas."""
        player = PlayerStats(username="Test")
        player.command_stats["ls"] = {"correct": 9, "total": 10}  # 90%

        assert "ls" in player.strong_areas

    def test_needs_minimum_3_attempts(self):
        """Test that areas need at least 3 attempts to be classified."""
        player = PlayerStats(username="Test")
        player.command_stats["ls"] = {"correct": 0, "total": 2}

        assert "ls" not in player.weak_areas
        assert "ls" not in player.strong_areas


class TestCreditsSystem:
    """Tests for credits system."""

    def test_initial_credits(self):
        """Test player starts with 100 credits."""
        player = PlayerStats(username="Test")
        assert player.credits == 100

    def test_add_credits(self):
        """Test adding credits."""
        player = PlayerStats(username="Test")
        player.add_credits(50)
        assert player.credits == 150

    def test_spend_credits_success(self):
        """Test spending credits when affordable."""
        player = PlayerStats(username="Test")
        result = player.spend_credits(40)
        assert result is True
        assert player.credits == 60

    def test_spend_credits_insufficient(self):
        """Test spending credits when not enough."""
        player = PlayerStats(username="Test")
        player.credits = 30
        result = player.spend_credits(40)
        assert result is False
        assert player.credits == 30  # Unchanged

    def test_can_afford_true(self):
        """Test can_afford returns True when sufficient."""
        player = PlayerStats(username="Test")
        assert player.can_afford(100) is True
        assert player.can_afford(50) is True

    def test_can_afford_false(self):
        """Test can_afford returns False when insufficient."""
        player = PlayerStats(username="Test")
        assert player.can_afford(150) is False


class TestMastery:
    """Tests for mastery tracking."""

    def test_mark_essential_mastered(self):
        """Test marking an essential command as mastered."""
        player = PlayerStats(username="Test")
        player.mark_command_mastered("ls", "essential")
        assert player.essential_progress["ls"] is True

    def test_mark_advanced_mastered(self):
        """Test marking an advanced command as mastered."""
        player = PlayerStats(username="Test")
        player.mark_command_mastered("awk", "advanced")
        assert player.advanced_progress["awk"] is True

    def test_get_mastery_percentage(self):
        """Test mastery percentage calculation."""
        player = PlayerStats(username="Test")
        player.essential_progress = {"ls": True, "cd": True, "pwd": False}

        pct = player.get_mastery_percentage("essential", 10)
        assert pct == 20.0  # 2 out of 10

    def test_get_mastery_percentage_zero_commands(self):
        """Test mastery percentage with zero commands."""
        player = PlayerStats(username="Test")
        pct = player.get_mastery_percentage("essential", 0)
        assert pct == 0.0


class TestPlayerSession:
    """Tests for PlayerSession."""

    def test_create_session(self):
        """Test creating a session."""
        session = PlayerSession()
        assert session.questions_this_session == 0
        assert session.correct_this_session == 0
        assert session.xp_earned_this_session == 0

    def test_session_accuracy_no_questions(self):
        """Test session accuracy with no questions."""
        session = PlayerSession()
        assert session.session_accuracy == 0.0

    def test_session_accuracy_calculated(self):
        """Test session accuracy calculation."""
        session = PlayerSession()
        session.questions_this_session = 10
        session.correct_this_session = 7
        assert session.session_accuracy == 70.0

    def test_record_question_correct(self):
        """Test recording a correct question."""
        session = PlayerSession()
        session.record_question("multiple_choice", True, 15)

        assert session.questions_this_session == 1
        assert session.correct_this_session == 1
        assert session.xp_earned_this_session == 15
        assert session.question_types_used["multiple_choice"] == 1

    def test_record_question_wrong(self):
        """Test recording a wrong question."""
        session = PlayerSession()
        session.record_question("fill_blank", False, 0)

        assert session.questions_this_session == 1
        assert session.correct_this_session == 0
        assert session.xp_earned_this_session == 0

    def test_question_types_tracked(self):
        """Test question types are tracked."""
        session = PlayerSession()
        session.record_question("multiple_choice", True, 10)
        session.record_question("multiple_choice", True, 10)
        session.record_question("fill_blank", True, 15)

        assert session.question_types_used["multiple_choice"] == 2
        assert session.question_types_used["fill_blank"] == 1
