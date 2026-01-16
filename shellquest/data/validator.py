"""Data validation utilities."""

from typing import List
from ..models.command import Command
from ..models.question import Question


class DataValidator:
    """Validates loaded data for consistency."""

    @staticmethod
    def validate_commands(commands: List[Command]) -> bool:
        """Validate command data."""
        if not commands:
            return False

        for cmd in commands:
            if not cmd.name or not cmd.description:
                return False
            if cmd.difficulty not in ["essential", "advanced"]:
                return False

        return True

    @staticmethod
    def validate_questions(questions: List[Question], commands: List[Command]) -> bool:
        """Validate question data."""
        if not questions:
            return False

        command_names = {cmd.name for cmd in commands}

        for q in questions:
            if not q.id or not q.question_text:
                return False
            if q.command not in command_names:
                print(f"Warning: Question {q.id} references unknown command '{q.command}'")
            if q.points <= 0:
                return False

        return True
