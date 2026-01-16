"""Player data models for tracking progress and statistics."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class PlayerStats:
    """Tracks player progress and statistics."""

    username: str
    level: int = 1
    xp: int = 0
    total_questions_answered: int = 0
    correct_answers: int = 0
    streak: int = 0
    best_streak: int = 0
    time_played: float = 0.0  # in seconds
    last_played: str = field(default_factory=lambda: datetime.now().isoformat())

    # Progress tracking
    essential_progress: Dict[str, bool] = field(default_factory=dict)
    advanced_progress: Dict[str, bool] = field(default_factory=dict)

    # Achievement tracking
    unlocked_achievements: List[str] = field(default_factory=list)

    # Command statistics: {command: {"correct": int, "total": int}}
    command_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Recently answered questions (IDs)
    recently_answered: List[str] = field(default_factory=list)

    # Story mode progress
    completed_levels: List[str] = field(default_factory=list)
    completed_chapters: List[str] = field(default_factory=list)

    # Battle mode stats
    battles_won: int = 0
    battles_lost: int = 0
    battles_played: int = 0

    # Mystery mode progress
    solved_mysteries: List[str] = field(default_factory=list)

    # Credits system
    credits: int = 100

    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.total_questions_answered) * 100

    @property
    def weak_areas(self) -> List[str]:
        """Identify commands that need more practice."""
        weak = []
        for command, stats in self.command_stats.items():
            if stats["total"] >= 3:  # At least 3 attempts
                accuracy = stats["correct"] / stats["total"]
                if accuracy < 0.6:  # Less than 60% accuracy
                    weak.append(command)
        return weak

    @property
    def strong_areas(self) -> List[str]:
        """Identify well-mastered commands."""
        strong = []
        for command, stats in self.command_stats.items():
            if stats["total"] >= 3:
                accuracy = stats["correct"] / stats["total"]
                if accuracy >= 0.9:  # 90% or better
                    strong.append(command)
        return strong

    def update_time_played(self, seconds: float):
        """Add time to total time played."""
        self.time_played += seconds

    def record_answer(self, command: str, is_correct: bool, question_id: str):
        """Record a question answer."""
        self.total_questions_answered += 1

        if is_correct:
            self.correct_answers += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.add_credits(10)  # Award 10 credits for correct answers
        else:
            self.streak = 0

        # Update command statistics
        if command not in self.command_stats:
            self.command_stats[command] = {"correct": 0, "total": 0}

        self.command_stats[command]["total"] += 1
        if is_correct:
            self.command_stats[command]["correct"] += 1

        # Track recently answered questions (max 50)
        self.recently_answered.append(question_id)
        if len(self.recently_answered) > 50:
            self.recently_answered = self.recently_answered[-50:]

        self.last_played = datetime.now().isoformat()

    def mark_command_mastered(self, command: str, difficulty: str):
        """Mark a command as mastered."""
        if difficulty == "essential":
            self.essential_progress[command] = True
        elif difficulty == "advanced":
            self.advanced_progress[command] = True

    def get_mastery_percentage(self, difficulty: str, total_commands: int) -> float:
        """Get mastery percentage for a difficulty level."""
        if total_commands == 0:
            return 0.0

        if difficulty == "essential":
            mastered = sum(1 for v in self.essential_progress.values() if v)
        else:
            mastered = sum(1 for v in self.advanced_progress.values() if v)

        return (mastered / total_commands) * 100

    def add_credits(self, amount: int):
        """Add credits to the player's balance."""
        self.credits += amount

    def spend_credits(self, amount: int) -> bool:
        """Spend credits if the player has enough.

        Returns True if successful, False if not enough credits.
        """
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False

    def can_afford(self, amount: int) -> bool:
        """Check if the player has enough credits."""
        return self.credits >= amount


@dataclass
class PlayerSession:
    """Tracks current session data."""

    questions_this_session: int = 0
    correct_this_session: int = 0
    xp_earned_this_session: int = 0
    session_start: str = field(default_factory=lambda: datetime.now().isoformat())
    question_types_used: Dict[str, int] = field(default_factory=dict)

    @property
    def session_accuracy(self) -> float:
        """Calculate session accuracy."""
        if self.questions_this_session == 0:
            return 0.0
        return (self.correct_this_session / self.questions_this_session) * 100

    def record_question(self, question_type: str, is_correct: bool, xp_gained: int):
        """Record a question in the session."""
        self.questions_this_session += 1
        if is_correct:
            self.correct_this_session += 1
        self.xp_earned_this_session += xp_gained

        # Track question types
        if question_type not in self.question_types_used:
            self.question_types_used[question_type] = 0
        self.question_types_used[question_type] += 1
