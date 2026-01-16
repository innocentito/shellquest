"""Quiz engine for question selection and answer validation."""

import random
from typing import List, Optional, Tuple
from ..models.question import Question
from ..models.player import PlayerStats, PlayerSession


class QuizEngine:
    """Manages quiz question selection and answer validation."""

    def __init__(self, question_pool: List[Question]):
        """Initialize quiz engine with a pool of questions."""
        self.question_pool = question_pool
        self.current_question: Optional[Question] = None
        self.session_questions: List[str] = []  # Question IDs asked this session

    def select_next_question(self, player: PlayerStats, session: PlayerSession) -> Optional[Question]:
        """
        Select next question using smart selection algorithm.

        Prioritizes:
        - Questions not recently asked
        - Commands player is weak in
        - Balanced question types
        """
        if not self.question_pool:
            return None

        # Calculate weights for each question
        weights = {}
        for question in self.question_pool:
            weight = 1.0

            # Avoid recently asked questions (last 20 from player history)
            recent_ids = player.recently_answered[-20:] + self.session_questions[-10:]
            if question.id in recent_ids:
                weight *= 0.1  # Very low weight (deprioritize, don't skip)

            # Prioritize weak areas (2x weight)
            if question.command in player.weak_areas:
                weight *= 2.0

            # Balance question types in session
            q_type_str = question.type.value
            type_count = session.question_types_used.get(q_type_str, 0)
            weight *= 1.0 / (1.0 + type_count * 0.3)

            # Slightly favor questions player hasn't seen yet
            if question.id not in player.recently_answered:
                weight *= 1.2

            weights[question.id] = weight

        if not weights:
            # Fallback: if all questions have been asked recently, pick any
            self.current_question = random.choice(self.question_pool)
        else:
            # Weighted random selection
            questions_and_weights = [(q, weights[q.id]) for q in self.question_pool if q.id in weights]
            if questions_and_weights:
                total_weight = sum(w for _, w in questions_and_weights)
                if total_weight <= 0:
                    self.current_question = random.choice(self.question_pool)
                else:
                    r = random.uniform(0, total_weight)
                    upto = 0
                    for question, weight in questions_and_weights:
                        upto += weight
                        if upto >= r:
                            self.current_question = question
                            break
                    else:
                        # Fallback if loop completes without break (edge case)
                        self.current_question = questions_and_weights[-1][0]
            else:
                self.current_question = random.choice(self.question_pool)

        self.session_questions.append(self.current_question.id)
        return self.current_question

    def validate_answer(self, user_answer: str) -> Tuple[bool, str]:
        """
        Validate user's answer against current question.

        Returns:
            (is_correct, explanation)
        """
        if not self.current_question:
            return False, "No current question"

        is_correct = self.current_question.is_correct(user_answer)
        explanation = self.current_question.explanation

        return is_correct, explanation

    def get_hint(self) -> str:
        """Get hint for current question."""
        if not self.current_question:
            return "No current question"

        return self.current_question.get_hint()

    def skip_question(self, player: PlayerStats, session: PlayerSession) -> Optional[Question]:
        """Skip current question and select next one."""
        return self.select_next_question(player, session)

    def get_question_display(self) -> dict:
        """Get formatted question data for display."""
        if not self.current_question:
            return {}

        q = self.current_question
        return {
            "id": q.id,
            "type": q.type.value,
            "text": q.question_text,
            "options": q.options,
            "difficulty": q.difficulty,
            "points": q.points,
            "command": q.command
        }

    def reset_session(self):
        """Reset session questions list."""
        self.session_questions = []
        self.current_question = None
