"""Achievement system for gamification."""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime


@dataclass
class Achievement:
    """Represents an unlockable achievement."""

    id: str
    name: str
    description: str
    icon: str
    requirement: Dict[str, Any]
    rarity: str  # "common", "rare", "epic", "legendary"
    xp_reward: int
    credit_reward: int = 0  # Credits awarded when unlocked

    def check_requirement(self, player_stats, session) -> bool:
        """Check if the achievement requirement is met."""
        req_type = self.requirement.get("type")

        if req_type == "correct_answers":
            count = self.requirement.get("count", 1)
            return player_stats.correct_answers >= count

        elif req_type == "streak":
            count = self.requirement.get("count", 1)
            return player_stats.streak >= count or player_stats.best_streak >= count

        elif req_type == "mastery":
            difficulty = self.requirement.get("difficulty", "essential")
            percentage = self.requirement.get("percentage", 100)
            # This would need total command count from game engine
            # For now, simplified check
            if difficulty == "essential":
                mastered = sum(1 for v in player_stats.essential_progress.values() if v)
                return mastered >= (percentage / 10)  # Simplified
            else:
                mastered = sum(1 for v in player_stats.advanced_progress.values() if v)
                return mastered >= (percentage / 10)

        elif req_type == "speed":
            questions = self.requirement.get("questions", 10)
            # Would need timing data from session
            return False  # Implemented in game engine

        elif req_type == "time_of_day":
            start_hour = self.requirement.get("start_hour", 0)
            end_hour = self.requirement.get("end_hour", 24)
            current_hour = datetime.now().hour
            return start_hour <= current_hour < end_hour

        elif req_type == "perfect_sessions":
            count = self.requirement.get("count", 1)
            # Would need session history tracking
            return False  # Implemented in game engine

        elif req_type == "total_questions":
            count = self.requirement.get("count", 100)
            return player_stats.total_questions_answered >= count

        return False


class AchievementSystem:
    """Manages achievement checking and unlocking."""

    def __init__(self, achievements: List[Achievement]):
        self.achievements = achievements

    def check_achievements(self, player_stats, session) -> List[Achievement]:
        """Check and return newly unlocked achievements."""
        unlocked = []

        for achievement in self.achievements:
            # Skip already unlocked achievements
            if achievement.id in player_stats.unlocked_achievements:
                continue

            # Check if requirement is met
            if achievement.check_requirement(player_stats, session):
                unlocked.append(achievement)
                player_stats.unlocked_achievements.append(achievement.id)
                player_stats.xp += achievement.xp_reward
                player_stats.add_credits(achievement.credit_reward)

        return unlocked

    def get_achievement_by_id(self, achievement_id: str) -> Achievement:
        """Get an achievement by its ID."""
        for achievement in self.achievements:
            if achievement.id == achievement_id:
                return achievement
        return None

    def get_unlocked_count(self, player_stats) -> int:
        """Get the number of unlocked achievements."""
        return len(player_stats.unlocked_achievements)

    def get_total_count(self) -> int:
        """Get the total number of achievements."""
        return len(self.achievements)
