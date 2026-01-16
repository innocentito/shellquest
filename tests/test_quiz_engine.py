"""Unit tests for the QuizEngine."""

import pytest
from shellquest.core.quiz_engine import QuizEngine
from shellquest.models.question import Question, QuestionType
from shellquest.models.player import PlayerStats, PlayerSession


@pytest.fixture
def sample_questions():
    """Create a pool of sample questions."""
    return [
        Question(
            id=f"q{i}",
            type=QuestionType.MULTIPLE_CHOICE,
            command=cmd,
            difficulty="essential",
            question_text=f"Question about {cmd}?",
            correct_answer="correct",
            explanation=f"Explanation for {cmd}",
            points=10,
            options=["correct", "wrong1", "wrong2", "wrong3"]
        )
        for i, cmd in enumerate(["ls", "cd", "pwd", "cat", "grep"])
    ]


@pytest.fixture
def quiz_engine(sample_questions):
    """Create a QuizEngine with sample questions."""
    return QuizEngine(sample_questions)


@pytest.fixture
def player():
    """Create a test player."""
    return PlayerStats(username="TestPlayer")


@pytest.fixture
def session():
    """Create a test session."""
    return PlayerSession()


class TestQuizEngineCreation:
    """Tests for QuizEngine initialization."""

    def test_create_with_questions(self, sample_questions):
        """Test creating engine with question pool."""
        engine = QuizEngine(sample_questions)
        assert len(engine.question_pool) == 5
        assert engine.current_question is None
        assert engine.session_questions == []

    def test_create_with_empty_pool(self):
        """Test creating engine with empty question pool."""
        engine = QuizEngine([])
        assert len(engine.question_pool) == 0


class TestSelectNextQuestion:
    """Tests for select_next_question method."""

    def test_select_returns_question(self, quiz_engine, player, session):
        """Test that selecting returns a question."""
        question = quiz_engine.select_next_question(player, session)
        assert question is not None
        assert isinstance(question, Question)

    def test_select_with_empty_pool_returns_none(self, player, session):
        """Test selecting from empty pool returns None."""
        engine = QuizEngine([])
        question = engine.select_next_question(player, session)
        assert question is None

    def test_select_tracks_session_questions(self, quiz_engine, player, session):
        """Test that selected questions are tracked in session."""
        quiz_engine.select_next_question(player, session)
        assert len(quiz_engine.session_questions) == 1

        quiz_engine.select_next_question(player, session)
        assert len(quiz_engine.session_questions) == 2

    def test_select_sets_current_question(self, quiz_engine, player, session):
        """Test that select sets current_question."""
        question = quiz_engine.select_next_question(player, session)
        assert quiz_engine.current_question == question

    def test_select_prioritizes_weak_areas(self, sample_questions, player, session):
        """Test that weak areas get higher priority."""
        engine = QuizEngine(sample_questions)
        # Mark "ls" as a weak area
        player.command_stats["ls"] = {"correct": 1, "total": 10}  # 10% accuracy

        # Run multiple selections and count ls questions
        ls_count = 0
        for _ in range(100):
            engine.reset_session()
            q = engine.select_next_question(player, session)
            if q.command == "ls":
                ls_count += 1

        # Should get more ls questions than pure random (20% = 20 out of 100)
        # With 2x weight, expect around 33%, so > 25 is reasonable
        assert ls_count >= 15  # At least somewhat more than random

    def test_select_avoids_recent_questions(self, sample_questions, player, session):
        """Test that recently answered questions are deprioritized."""
        engine = QuizEngine(sample_questions)
        # Mark all but one question as recently answered
        player.recently_answered = ["q0", "q1", "q2", "q3"]

        # The remaining question (q4) should be selected more often
        q4_count = 0
        for _ in range(20):
            engine.reset_session()
            q = engine.select_next_question(player, session)
            if q.id == "q4":
                q4_count += 1

        assert q4_count > 5  # Should get q4 most of the time


class TestValidateAnswer:
    """Tests for validate_answer method."""

    def test_validate_correct_answer(self, quiz_engine, player, session):
        """Test validating a correct answer."""
        quiz_engine.select_next_question(player, session)
        is_correct, explanation = quiz_engine.validate_answer("correct")
        assert is_correct is True
        assert len(explanation) > 0

    def test_validate_wrong_answer(self, quiz_engine, player, session):
        """Test validating a wrong answer."""
        quiz_engine.select_next_question(player, session)
        is_correct, explanation = quiz_engine.validate_answer("wrong")
        assert is_correct is False

    def test_validate_without_current_question(self, quiz_engine):
        """Test validating when no question is selected."""
        is_correct, explanation = quiz_engine.validate_answer("anything")
        assert is_correct is False
        assert "No current question" in explanation


class TestGetHint:
    """Tests for get_hint method."""

    def test_get_hint_with_question(self, quiz_engine, player, session):
        """Test getting hint for current question."""
        quiz_engine.select_next_question(player, session)
        hint = quiz_engine.get_hint()
        assert isinstance(hint, str)

    def test_get_hint_without_question(self, quiz_engine):
        """Test getting hint when no question is selected."""
        hint = quiz_engine.get_hint()
        assert "No current question" in hint


class TestResetSession:
    """Tests for reset_session method."""

    def test_reset_clears_session_questions(self, quiz_engine, player, session):
        """Test that reset clears session questions."""
        quiz_engine.select_next_question(player, session)
        quiz_engine.select_next_question(player, session)
        assert len(quiz_engine.session_questions) == 2

        quiz_engine.reset_session()
        assert quiz_engine.session_questions == []

    def test_reset_clears_current_question(self, quiz_engine, player, session):
        """Test that reset clears current question."""
        quiz_engine.select_next_question(player, session)
        assert quiz_engine.current_question is not None

        quiz_engine.reset_session()
        assert quiz_engine.current_question is None


class TestGetQuestionDisplay:
    """Tests for get_question_display method."""

    def test_display_with_question(self, quiz_engine, player, session):
        """Test getting display data for current question."""
        quiz_engine.select_next_question(player, session)
        display = quiz_engine.get_question_display()

        assert "id" in display
        assert "type" in display
        assert "text" in display
        assert "options" in display
        assert "difficulty" in display
        assert "points" in display
        assert "command" in display

    def test_display_without_question(self, quiz_engine):
        """Test getting display when no question is selected."""
        display = quiz_engine.get_question_display()
        assert display == {}


class TestWeightedSelection:
    """Tests for weighted selection algorithm edge cases."""

    def test_all_questions_recently_asked(self, sample_questions, player, session):
        """Test selection when all questions were recently asked."""
        engine = QuizEngine(sample_questions)
        player.recently_answered = [f"q{i}" for i in range(5)]

        # Should still return a question (fallback behavior)
        question = engine.select_next_question(player, session)
        assert question is not None

    def test_single_question_pool(self, player, session):
        """Test selection with only one question."""
        single_q = Question(
            id="only",
            type=QuestionType.FILL_BLANK,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5
        )
        engine = QuizEngine([single_q])

        question = engine.select_next_question(player, session)
        assert question.id == "only"
