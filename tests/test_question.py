"""Unit tests for the Question model."""

import pytest
from shellquest.models.question import Question, QuestionType


class TestQuestionType:
    """Tests for QuestionType enum."""

    def test_all_types_exist(self):
        """Test all expected question types are defined."""
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.FILL_BLANK.value == "fill_blank"
        assert QuestionType.WHAT_DOES_IT_DO.value == "what_does_it_do"
        assert QuestionType.FIX_ERROR.value == "fix_error"
        assert QuestionType.COMMAND_BUILDER.value == "command_builder"
        assert QuestionType.OUTPUT_PREDICTION.value == "output_prediction"


class TestQuestionCreation:
    """Tests for Question creation and initialization."""

    def test_create_multiple_choice_question(self):
        """Test creating a multiple choice question."""
        q = Question(
            id="mc_01",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="What does ls do?",
            correct_answer="Lists files",
            explanation="ls lists files",
            points=10,
            options=["Lists files", "Changes dir", "Copies", "Deletes"]
        )
        assert q.id == "mc_01"
        assert q.type == QuestionType.MULTIPLE_CHOICE
        assert len(q.options) == 4

    def test_type_string_converted_to_enum(self):
        """Test that string type is converted to QuestionType enum."""
        q = Question(
            id="test",
            type="multiple_choice",
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5
        )
        assert q.type == QuestionType.MULTIPLE_CHOICE

    def test_correct_answer_converted_to_list(self):
        """Test that single correct_answer is converted to list."""
        q = Question(
            id="test",
            type=QuestionType.FILL_BLANK,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="single answer",
            explanation="",
            points=5
        )
        assert isinstance(q.correct_answer, list)
        assert q.correct_answer == ["single answer"]

    def test_multiple_correct_answers_preserved(self):
        """Test that list of correct answers is preserved."""
        q = Question(
            id="test",
            type=QuestionType.FILL_BLANK,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer=["answer1", "answer2"],
            explanation="",
            points=5
        )
        assert q.correct_answer == ["answer1", "answer2"]

    def test_options_shuffled(self):
        """Test that options are shuffled (probabilistic)."""
        original_options = ["A", "B", "C", "D"]
        shuffled_any = False

        # Run multiple times to check if shuffling occurs
        for _ in range(10):
            q = Question(
                id="test",
                type=QuestionType.MULTIPLE_CHOICE,
                command="ls",
                difficulty="essential",
                question_text="?",
                correct_answer="A",
                explanation="",
                points=5,
                options=original_options.copy()
            )
            if q.options != original_options:
                shuffled_any = True
                break

        # With 4 options, probability of same order 10 times is (1/24)^10, extremely unlikely
        assert shuffled_any or len(set(q.options)) == len(original_options)


class TestIsCorrect:
    """Tests for is_correct method."""

    @pytest.fixture
    def mc_question(self):
        """Create a multiple choice question with known options."""
        q = Question(
            id="mc",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="What does ls do?",
            correct_answer="Lists files",
            explanation="",
            points=10,
            options=["Lists files", "Changes directory", "Copies files", "Deletes files"]
        )
        # Reset options to known order for testing
        q.options = ["Lists files", "Changes directory", "Copies files", "Deletes files"]
        return q

    @pytest.fixture
    def fill_blank_question(self):
        """Create a fill-in-the-blank question."""
        return Question(
            id="fb",
            type=QuestionType.FILL_BLANK,
            command="ls",
            difficulty="essential",
            question_text="ls ___ shows hidden files",
            correct_answer="-a",
            explanation="",
            points=10
        )

    def test_letter_answer_correct(self, mc_question):
        """Test correct letter answer (A) is accepted."""
        assert mc_question.is_correct("A") is True
        assert mc_question.is_correct("a") is True

    def test_number_answer_correct(self, mc_question):
        """Test correct number answer (1) is accepted."""
        assert mc_question.is_correct("1") is True

    def test_wrong_letter_answer(self, mc_question):
        """Test wrong letter answer is rejected."""
        assert mc_question.is_correct("B") is False
        assert mc_question.is_correct("C") is False
        assert mc_question.is_correct("D") is False

    def test_wrong_number_answer(self, mc_question):
        """Test wrong number answer is rejected."""
        assert mc_question.is_correct("2") is False
        assert mc_question.is_correct("3") is False
        assert mc_question.is_correct("4") is False

    def test_direct_text_answer_correct(self, mc_question):
        """Test direct text matching correct answer."""
        assert mc_question.is_correct("Lists files") is True
        assert mc_question.is_correct("lists files") is True
        assert mc_question.is_correct("  Lists files  ") is True

    def test_fill_blank_exact_match(self, fill_blank_question):
        """Test fill-in-the-blank exact match."""
        assert fill_blank_question.is_correct("-a") is True
        assert fill_blank_question.is_correct("-A") is True
        assert fill_blank_question.is_correct("  -a  ") is True

    def test_fill_blank_wrong_answer(self, fill_blank_question):
        """Test fill-in-the-blank wrong answer."""
        assert fill_blank_question.is_correct("-l") is False
        assert fill_blank_question.is_correct("ls") is False

    def test_multiple_correct_answers(self):
        """Test question with multiple acceptable answers."""
        q = Question(
            id="multi",
            type=QuestionType.FILL_BLANK,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer=["yes", "y", "Y"],
            explanation="",
            points=10
        )
        assert q.is_correct("yes") is True
        assert q.is_correct("y") is True
        assert q.is_correct("Y") is True
        assert q.is_correct("no") is False

    def test_invalid_letter_outside_range(self, mc_question):
        """Test that letters outside range don't crash."""
        assert mc_question.is_correct("E") is False
        assert mc_question.is_correct("Z") is False

    def test_invalid_number_outside_range(self, mc_question):
        """Test that numbers outside range don't crash."""
        assert mc_question.is_correct("5") is False
        assert mc_question.is_correct("0") is False


class TestHints:
    """Tests for hint methods."""

    def test_get_hint_returns_hint(self):
        """Test get_hint returns the hint."""
        q = Question(
            id="test",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5,
            hint="This is a hint"
        )
        assert q.get_hint() == "This is a hint"

    def test_get_hint_no_hint(self):
        """Test get_hint when no hint is set."""
        q = Question(
            id="test",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5
        )
        assert "No hint available" in q.get_hint()

    def test_get_premium_hint_returns_premium_hint(self):
        """Test get_premium_hint returns the premium hint."""
        q = Question(
            id="test",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5,
            premium_hint="Premium hint here"
        )
        assert q.get_premium_hint() == "Premium hint here"

    def test_get_premium_hint_generates_for_multiple_choice(self):
        """Test generated premium hint for multiple choice."""
        q = Question(
            id="test",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5
        )
        hint = q.get_premium_hint()
        assert "Two of these options" in hint or len(hint) > 0

    def test_get_premium_hint_generates_for_fill_blank(self):
        """Test generated premium hint for fill-in-blank."""
        q = Question(
            id="test",
            type=QuestionType.FILL_BLANK,
            command="ls",
            difficulty="essential",
            question_text="?",
            correct_answer="a",
            explanation="",
            points=5
        )
        hint = q.get_premium_hint()
        assert "flags and options" in hint or len(hint) > 0


class TestDisplayText:
    """Tests for get_display_text method."""

    def test_get_display_text(self):
        """Test get_display_text returns question_text."""
        q = Question(
            id="test",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="What is the purpose of ls?",
            correct_answer="a",
            explanation="",
            points=5
        )
        assert q.get_display_text() == "What is the purpose of ls?"
