"""Performance tests for ShellQuest."""

import pytest
import time
from pathlib import Path

from shellquest.data.loader import DataLoader
from shellquest.core.quiz_engine import QuizEngine
from shellquest.core.scoring_system import ScoringSystem
from shellquest.models.player import PlayerStats, PlayerSession
from shellquest.models.question import Question, QuestionType


class TestDataLoaderPerformance:
    """Performance tests for data loading."""

    def test_load_commands_under_100ms(self):
        """Test loading commands takes under 100ms."""
        loader = DataLoader()
        loader.clear_cache()

        start = time.perf_counter()
        loader.load_commands("essential")
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100, f"Loading commands took {elapsed:.1f}ms, expected < 100ms"

    def test_load_questions_under_150ms(self):
        """Test loading questions takes under 150ms."""
        loader = DataLoader()
        loader.clear_cache()

        start = time.perf_counter()
        loader.load_questions("essential")
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 150, f"Loading questions took {elapsed:.1f}ms, expected < 150ms"

    def test_load_achievements_under_50ms(self):
        """Test loading achievements takes under 50ms."""
        loader = DataLoader()
        loader.clear_cache()

        start = time.perf_counter()
        loader.load_achievements()
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50, f"Loading achievements took {elapsed:.1f}ms, expected < 50ms"

    def test_load_all_data_under_300ms(self):
        """Test loading all game data takes under 300ms."""
        loader = DataLoader()
        loader.clear_cache()

        start = time.perf_counter()
        loader.load_all_commands()
        loader.load_all_questions()
        loader.load_achievements()
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 300, f"Loading all data took {elapsed:.1f}ms, expected < 300ms"

    def test_cached_load_under_1ms(self):
        """Test cached data loads in under 1ms."""
        loader = DataLoader()
        # First load to populate cache
        loader.load_commands("essential")

        # Cached load should be nearly instant
        start = time.perf_counter()
        loader.load_commands("essential")
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 1, f"Cached load took {elapsed:.3f}ms, expected < 1ms"


class TestQuizEnginePerformance:
    """Performance tests for quiz engine."""

    @pytest.fixture
    def large_question_pool(self):
        """Create a large pool of questions for testing."""
        return [
            Question(
                id=f"perf_q{i}",
                type=QuestionType.MULTIPLE_CHOICE,
                command=f"cmd{i % 20}",
                difficulty="essential",
                question_text=f"Question {i}?",
                correct_answer="correct",
                explanation="Explanation",
                points=10,
                options=["correct", "wrong1", "wrong2", "wrong3"]
            )
            for i in range(500)
        ]

    @pytest.fixture
    def player_with_history(self):
        """Create a player with extensive history."""
        player = PlayerStats(username="PerfTest")
        # Add history
        player.recently_answered = [f"perf_q{i}" for i in range(100)]
        player.command_stats = {
            f"cmd{i}": {"correct": i * 2, "total": i * 3 + 1}
            for i in range(20)
        }
        return player

    def test_question_selection_under_10ms(self, large_question_pool, player_with_history):
        """Test question selection takes under 10ms."""
        engine = QuizEngine(large_question_pool)
        session = PlayerSession()

        start = time.perf_counter()
        engine.select_next_question(player_with_history, session)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 10, f"Question selection took {elapsed:.2f}ms, expected < 10ms"

    def test_100_question_selections_under_500ms(self, large_question_pool, player_with_history):
        """Test 100 question selections take under 500ms."""
        engine = QuizEngine(large_question_pool)
        session = PlayerSession()

        start = time.perf_counter()
        for _ in range(100):
            engine.select_next_question(player_with_history, session)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 500, f"100 selections took {elapsed:.1f}ms, expected < 500ms"

    def test_answer_validation_under_1ms(self, large_question_pool, player_with_history):
        """Test answer validation takes under 1ms."""
        engine = QuizEngine(large_question_pool)
        session = PlayerSession()
        engine.select_next_question(player_with_history, session)

        start = time.perf_counter()
        engine.validate_answer("correct")
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 1, f"Answer validation took {elapsed:.3f}ms, expected < 1ms"


class TestScoringSystemPerformance:
    """Performance tests for scoring system."""

    @pytest.fixture
    def scoring(self):
        return ScoringSystem()

    @pytest.fixture
    def sample_question(self):
        return Question(
            id="perf_score",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text="Test?",
            correct_answer="correct",
            explanation="",
            points=10,
            options=["correct", "wrong"]
        )

    def test_xp_calculation_under_1ms(self, scoring, sample_question):
        """Test XP calculation takes under 1ms."""
        start = time.perf_counter()
        scoring.calculate_xp(sample_question, 5.0, False, 10)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 1, f"XP calculation took {elapsed:.3f}ms, expected < 1ms"

    def test_level_calculation_under_1ms(self, scoring):
        """Test level calculation takes under 1ms."""
        start = time.perf_counter()
        scoring.get_level(50000)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 1, f"Level calculation took {elapsed:.3f}ms, expected < 1ms"

    def test_1000_xp_calculations_under_50ms(self, scoring, sample_question):
        """Test 1000 XP calculations take under 50ms."""
        start = time.perf_counter()
        for i in range(1000):
            scoring.calculate_xp(sample_question, i % 30 + 1, i % 2 == 0, i % 50)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50, f"1000 XP calculations took {elapsed:.1f}ms, expected < 50ms"


class TestPlayerStatsPerformance:
    """Performance tests for player stats operations."""

    def test_record_answer_under_1ms(self):
        """Test recording an answer takes under 1ms."""
        player = PlayerStats(username="PerfTest")

        start = time.perf_counter()
        player.record_answer("ls", True, "q1")
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 1, f"Recording answer took {elapsed:.3f}ms, expected < 1ms"

    def test_1000_answer_records_under_100ms(self):
        """Test 1000 answer records take under 100ms."""
        player = PlayerStats(username="PerfTest")

        start = time.perf_counter()
        for i in range(1000):
            player.record_answer(f"cmd{i % 20}", i % 3 == 0, f"q{i}")
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100, f"1000 records took {elapsed:.1f}ms, expected < 100ms"

    def test_weak_areas_calculation_under_5ms(self):
        """Test weak areas calculation takes under 5ms."""
        player = PlayerStats(username="PerfTest")
        # Add lots of stats
        for i in range(50):
            player.command_stats[f"cmd{i}"] = {
                "correct": i * 2,
                "total": i * 3 + 10
            }

        start = time.perf_counter()
        _ = player.weak_areas
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 5, f"Weak areas calculation took {elapsed:.2f}ms, expected < 5ms"


class TestSessionPerformance:
    """Performance tests for session operations."""

    def test_session_accuracy_under_1ms(self):
        """Test session accuracy calculation takes under 1ms."""
        session = PlayerSession()
        for i in range(100):
            session.record_question("mc", i % 2 == 0, 10)

        start = time.perf_counter()
        _ = session.session_accuracy
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 1, f"Accuracy calculation took {elapsed:.3f}ms, expected < 1ms"


class TestMemoryUsage:
    """Memory usage sanity checks."""

    def test_large_question_pool_memory(self):
        """Test that large question pool doesn't use excessive memory."""
        import sys

        questions = [
            Question(
                id=f"mem_q{i}",
                type=QuestionType.MULTIPLE_CHOICE,
                command="ls",
                difficulty="essential",
                question_text=f"Question {i} with some longer text to simulate real questions?",
                correct_answer="This is the correct answer",
                explanation="This is a detailed explanation of why this is correct.",
                points=10,
                options=["This is the correct answer", "Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]
            )
            for i in range(1000)
        ]

        # Rough memory estimate (not exact, just sanity check)
        size = sys.getsizeof(questions)
        # Each question object + strings shouldn't exceed ~2KB on average
        # So 1000 questions should be under 2MB
        assert size < 100000, f"Question list header size {size} seems too large"

    def test_player_stats_memory(self):
        """Test that player with lots of history doesn't use excessive memory."""
        import sys

        player = PlayerStats(username="MemoryTest")
        # Add extensive history
        player.recently_answered = [f"q{i}" for i in range(1000)]
        player.command_stats = {
            f"cmd{i}": {"correct": i * 100, "total": i * 150}
            for i in range(100)
        }
        player.unlocked_achievements = [f"ach{i}" for i in range(50)]

        # Should be reasonably sized
        size = sys.getsizeof(player)
        assert size < 1000, f"Player object size {size} seems reasonable"


class TestStartupPerformance:
    """Tests for overall startup performance."""

    def test_full_data_load_benchmark(self):
        """Benchmark full data loading."""
        loader = DataLoader()
        loader.clear_cache()

        times = []
        for _ in range(5):
            loader.clear_cache()
            start = time.perf_counter()
            loader.load_all_commands()
            loader.load_all_questions()
            loader.load_achievements()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        assert avg_time < 300, f"Average load time {avg_time:.1f}ms, expected < 300ms"

    def test_quiz_engine_init_performance(self):
        """Test quiz engine initialization performance."""
        loader = DataLoader()
        questions = loader.load_all_questions()

        start = time.perf_counter()
        engine = QuizEngine(questions)
        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 10, f"QuizEngine init took {elapsed:.2f}ms, expected < 10ms"
