"""Command data model for shell commands."""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class CommandOption:
    """Represents a command-line option or flag."""
    name: str
    description: str


@dataclass
class CommandExample:
    """Represents an example usage of a command."""
    command: str
    explanation: str


@dataclass
class Command:
    """Represents a shell command with its metadata and documentation."""

    name: str
    category: str
    difficulty: str  # "essential" or "advanced"
    syntax: str
    description: str
    common_options: List[CommandOption] = field(default_factory=list)
    examples: List[CommandExample] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_commands: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"

    def get_full_info(self) -> Dict:
        """Returns all command information as a dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "difficulty": self.difficulty,
            "syntax": self.syntax,
            "description": self.description,
            "common_options": [(opt.name, opt.description) for opt in self.common_options],
            "examples": [(ex.command, ex.explanation) for ex in self.examples],
            "tags": self.tags,
            "related_commands": self.related_commands,
            "tips": self.tips,
        }
