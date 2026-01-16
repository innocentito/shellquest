"""Unit tests for the ScoringSystem."""

import pytest
from shellquest.core.scoring_system import ScoringSystem
from shellquest.models.question import Question, QuestionType


@pytest.fixture
def scoring():
    """Create a ScoringSystem instance."""
    return ScoringSystem()


@pytest.fixture
def essential_question():
    """Create a basic essential difficulty question."""
    return Question(
        id="test_q1",
        type=QuestionType.MULTIPLE_CHOICE,
        command="ls",
        difficulty="essential",
        question_text="What does ls do?",
        correct_answer="Lists files",
        explanation="ls lists directory contents",
        points=10,
        options=["Lists files", "Changes directory", "Copies files", "Deletes files"]
    )


@pytest.fixture
def advanced_question():
    """Create an advanced difficulty question."""
    return Question(
        id="test_q2",
        type=QuestionType.FILL_BLANK,
        command="grep",
        difficulty="advanced",
        question_text="Fill in the blank",
        correct_answer="-r",
        explanation="grep -r for recursive",
        points=20
    )


class TestCalculateXP:
    """Tests for calculate_xp method."""

    def test_base_xp_no_modifiers(self, scoring, essential_question):
        """Test basic XP calculation with no modifiers."""
        # No streak, no hint, normal speed (>10 seconds)
        xp = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=False, streak=0)
        assert xp == 10  # base points * 1.0 diff * 1.0 streak * 1.0 speed

    def test_advanced_difficulty_multiplier(self, scoring, advanced_question):
        """Test 1.5x multiplier for advanced questions."""
        xp = scoring.calculate_xp(advanced_question, time_taken=15.0, hint_used=False, streak=0)
        assert xp == 30  # 20 points * 1.5 diff = 30

    def test_streak_bonus(self, scoring, essential_question):
        """Test streak multiplier increases XP."""
        xp_no_streak = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=False, streak=0)
        xp_streak_5 = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=False, streak=5)
        assert xp_streak_5 > xp_no_streak
        # streak 5: 1.0 + (5 * 0.2) = 2.0 multiplier
        assert xp_streak_5 == 20

    def test_streak_capped_at_3x(self, scoring, essential_question):
        """Test streak multiplier caps at 3x."""
        xp_streak_10 = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=False, streak=10)
        xp_streak_20 = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=False, streak=20)
        # Both should be capped at 3x: 10 * 3.0 = 30
        assert xp_streak_10 == 30
        assert xp_streak_20 == 30

    def test_speed_bonus_super_fast(self, scoring, essential_question):
        """Test 1.5x bonus for answers under 5 seconds."""
        xp = scoring.calculate_xp(essential_question, time_taken=3.0, hint_used=False, streak=0)
        assert xp == 15  # 10 * 1.5

    def test_speed_bonus_fast(self, scoring, essential_question):
        """Test 1.2x bonus for answers under 10 seconds."""
        xp = scoring.calculate_xp(essential_question, time_taken=7.0, hint_used=False, streak=0)
        assert xp == 12  # 10 * 1.2

    def test_hint_penalty(self, scoring, essential_question):
        """Test 50% penalty when hint is used."""
        xp_no_hint = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=False, streak=0)
        xp_with_hint = scoring.calculate_xp(essential_question, time_taken=15.0, hint_used=True, streak=0)
        assert xp_with_hint == xp_no_hint // 2
        assert xp_with_hint == 5

    def test_minimum_xp_is_1(self, scoring):
        """Test that minimum XP earned is always at least 1."""
        tiny_question = Question(
            id="tiny",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=1,
            options=["a", "b"]
        )
        # Even with hint penalty: 1 * 0.5 = 0.5 -> should be 1
        xp = scoring.calculate_xp(tiny_question, time_taken=60.0, hint_used=True, streak=0)
        assert xp >= 1

    def test_all_bonuses_combined(self, scoring, advanced_question):
        """Test all bonuses stack correctly."""
        # Advanced (1.5x) + streak 5 (2.0x) + super fast (1.5x) = 4.5x
        xp = scoring.calculate_xp(advanced_question, time_taken=3.0, hint_used=False, streak=5)
        # 20 * 1.5 * 2.0 * 1.5 = 90
        assert xp == 90


class TestLevelCalculation:
    """Tests for level calculation methods."""

    def test_level_1_at_0_xp(self, scoring):
        """Test level 1 at 0 XP."""
        assert scoring.get_level(0) == 1

    def test_level_1_at_99_xp(self, scoring):
        """Test still level 1 at 99 XP."""
        assert scoring.get_level(99) == 1

    def test_level_2_at_100_xp(self, scoring):
        """Test level 2 starts at 100 XP."""
        assert scoring.get_level(100) == 2

    def test_level_3_at_400_xp(self, scoring):
        """Test level 3 at 400 XP (sqrt(400/100) + 1 = 3)."""
        assert scoring.get_level(400) == 3

    def test_level_4_at_900_xp(self, scoring):
        """Test level 4 at 900 XP."""
        assert scoring.get_level(900) == 4

    def test_level_5_at_1600_xp(self, scoring):
        """Test level 5 at 1600 XP."""
        assert scoring.get_level(1600) == 5

    def test_high_level(self, scoring):
        """Test high level calculation."""
        # Level 10: need (10-1)^2 * 100 = 8100 XP
        assert scoring.get_level(8100) == 10


class TestXPForLevel:
    """Tests for get_xp_for_level method."""

    def test_xp_for_level_1(self, scoring):
        """Test 0 XP needed for level 1."""
        assert scoring.get_xp_for_level(1) == 0

    def test_xp_for_level_2(self, scoring):
        """Test 100 XP needed for level 2."""
        assert scoring.get_xp_for_level(2) == 100

    def test_xp_for_level_3(self, scoring):
        """Test 400 XP needed for level 3."""
        assert scoring.get_xp_for_level(3) == 400

    def test_xp_for_level_5(self, scoring):
        """Test 1600 XP needed for level 5."""
        assert scoring.get_xp_for_level(5) == 1600


class TestLevelProgress:
    """Tests for get_level_progress method."""

    def test_progress_at_level_start(self, scoring):
        """Test progress at beginning of a level."""
        level, current, needed = scoring.get_level_progress(400)
        assert level == 3
        assert current == 0  # Just hit level 3
        assert needed == 500  # 900 - 400

    def test_progress_mid_level(self, scoring):
        """Test progress mid-level."""
        level, current, needed = scoring.get_level_progress(650)
        assert level == 3
        assert current == 250  # 650 - 400
        assert needed == 250  # 900 - 650


class TestProgressPercentage:
    """Tests for get_progress_percentage method."""

    def test_0_percent_at_level_start(self, scoring):
        """Test 0% progress at level start."""
        pct = scoring.get_progress_percentage(100)
        assert pct == pytest.approx(0.0, abs=0.1)

    def test_50_percent_mid_level(self, scoring):
        """Test roughly 50% at mid-level."""
        # Level 2: 100 to 400 XP, so 250 XP is 50%
        pct = scoring.get_progress_percentage(250)
        assert pct == pytest.approx(50.0, abs=0.1)

    def test_100_percent_capped(self, scoring):
        """Test percentage is capped at 100%."""
        pct = scoring.get_progress_percentage(10000000)
        assert pct <= 100.0
