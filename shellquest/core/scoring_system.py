"""Scoring and leveling system for ShellQuest."""

from ..models.question import Question


class ScoringSystem:
    """Handles XP calculation, leveling, and score multipliers."""

    XP_BASE = 100  # XP needed for level 1
    XP_EXPONENT = 0.5  # Square root progression

    def __init__(self):
        pass

    def calculate_xp(self, question: Question, time_taken: float,
                     hint_used: bool, streak: int) -> int:
        """
        Calculate XP earned for a question.

        Args:
            question: The question that was answered
            time_taken: Time in seconds to answer
            hint_used: Whether a hint was used
            streak: Current correct answer streak

        Returns:
            Total XP earned
        """
        base_xp = question.points

        # Difficulty multiplier
        diff_mult = 1.5 if question.difficulty == "advanced" else 1.0

        # Streak bonus (max 3x at streak 10+)
        streak_mult = min(1.0 + (streak * 0.2), 3.0)

        # Speed bonus
        if time_taken < 5:
            speed_mult = 1.5  # Super fast
        elif time_taken < 10:
            speed_mult = 1.2  # Fast
        else:
            speed_mult = 1.0  # Normal

        # Hint penalty
        hint_mult = 0.5 if hint_used else 1.0

        total = int(base_xp * diff_mult * streak_mult * speed_mult * hint_mult)
        return max(total, 1)  # Minimum 1 XP

    def get_level(self, xp: int) -> int:
        """
        Calculate level from XP.
        Level = floor(sqrt(XP / 100))
        L1: 100 XP, L2: 400 XP, L3: 900 XP, L4: 1600 XP, etc.
        """
        if xp < self.XP_BASE:
            return 1
        return int((xp / self.XP_BASE) ** self.XP_EXPONENT) + 1

    def get_xp_for_level(self, level: int) -> int:
        """Get total XP needed to reach a specific level."""
        if level <= 1:
            return 0
        return int(((level - 1) ** 2) * self.XP_BASE)

    def get_xp_for_next_level(self, current_level: int) -> int:
        """Get XP needed to reach next level."""
        return self.get_xp_for_level(current_level + 1)

    def get_level_progress(self, xp: int) -> tuple:
        """
        Get level progress information.

        Returns:
            (current_level, current_xp_in_level, xp_needed_for_next)
        """
        level = self.get_level(xp)
        xp_for_current_level = self.get_xp_for_level(level)
        xp_for_next_level = self.get_xp_for_next_level(level)

        current_xp_in_level = xp - xp_for_current_level
        xp_needed = xp_for_next_level - xp

        return (level, current_xp_in_level, xp_needed)

    def get_progress_percentage(self, xp: int) -> float:
        """Get percentage progress towards next level."""
        level = self.get_level(xp)
        xp_for_current = self.get_xp_for_level(level)
        xp_for_next = self.get_xp_for_next_level(level)

        if xp_for_next == xp_for_current:
            return 100.0

        progress = ((xp - xp_for_current) / (xp_for_next - xp_for_current)) * 100
        return min(progress, 100.0)
