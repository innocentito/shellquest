"""Question data models for the quiz system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Optional
import random


class QuestionType(Enum):
    """Types of questions available in the quiz."""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    WHAT_DOES_IT_DO = "what_does_it_do"
    FIX_ERROR = "fix_error"
    COMMAND_BUILDER = "command_builder"
    OUTPUT_PREDICTION = "output_prediction"


@dataclass
class Question:
    """Represents a quiz question."""

    id: str
    type: QuestionType
    command: str
    difficulty: str  # "essential" or "advanced"
    question_text: str
    correct_answer: Union[str, List[str]]
    explanation: str
    points: int
    options: Optional[List[str]] = None
    hint: Optional[str] = None
    premium_hint: Optional[str] = None

    def __post_init__(self):
        """Convert type string to QuestionType enum if needed."""
        if isinstance(self.type, str):
            self.type = QuestionType(self.type)

        # Ensure correct_answer is a list for easier comparison
        if isinstance(self.correct_answer, str):
            self.correct_answer = [self.correct_answer]

        # Shuffle multiple choice options to prevent answer patterns
        if self.options and len(self.options) > 1:
            random.shuffle(self.options)

    def is_correct(self, user_answer: str) -> bool:
        """Check if the user's answer is correct."""
        normalized_user_answer = user_answer.strip().lower()

        # For multiple choice, accept letter answers (a, b, c, d) or numbers (1, 2, 3, 4)
        if self.options and len(normalized_user_answer) == 1:
            letter_index = -1
            if normalized_user_answer in 'abcd':
                letter_index = ord(normalized_user_answer) - ord('a')
            elif normalized_user_answer in '1234':
                letter_index = int(normalized_user_answer) - 1

            if 0 <= letter_index < len(self.options):
                selected_option = self.options[letter_index].strip().lower()
                for correct in self.correct_answer:
                    if selected_option == correct.strip().lower():
                        return True
                return False

        # Direct answer comparison
        for correct in self.correct_answer:
            normalized_correct = correct.strip().lower()
            if normalized_user_answer == normalized_correct:
                return True

        return False

    def get_hint(self) -> str:
        """Returns the hint for this question."""
        return self.hint if self.hint else "No hint available for this question."

    def get_premium_hint(self) -> str:
        """Returns the premium hint for this question.

        If a premium_hint is set, returns it directly.
        Otherwise, generates a generic helpful hint based on the question type.

        Returns:
            str: A premium hint that provides more helpful guidance than the basic hint.
        """
        if self.premium_hint:
            return self.premium_hint

        # Generate generic helpful hints based on question type
        generic_hints = {
            QuestionType.MULTIPLE_CHOICE: (
                "Two of these options are clearly wrong. Focus on the remaining two."
            ),
            QuestionType.FILL_BLANK: (
                "Think about the most common flags and options for this command. "
                "The answer is likely a frequently used option."
            ),
            QuestionType.WHAT_DOES_IT_DO: (
                "Break down the command into its parts: the base command, flags, and arguments. "
                "Consider what each part does individually."
            ),
            QuestionType.FIX_ERROR: (
                "Look carefully at the syntax. Common issues include missing quotes, "
                "incorrect flag usage, or wrong argument order."
            ),
            QuestionType.COMMAND_BUILDER: (
                "Start with the base command, then add the necessary flags in order. "
                "Remember that flag order can sometimes matter."
            ),
            QuestionType.OUTPUT_PREDICTION: (
                "Mentally trace through the command step by step. "
                "Consider what the input is and how each part of the command transforms it."
            ),
        }

        return generic_hints.get(
            self.type,
            "Consider the command's primary purpose and most common use cases."
        )

    def get_display_text(self) -> str:
        """Returns formatted question text for display."""
        return self.question_text
