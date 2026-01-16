"""Unit tests for the Story Engine."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from shellquest.core.story_engine import StoryEngine, Level, Chapter
from shellquest.models.player import PlayerStats
from shellquest.models.question import Question, QuestionType


@pytest.fixture
def sample_questions():
    """Create sample questions."""
    commands = ["ls", "cd", "pwd", "cat", "grep"]
    return [
        Question(
            id=f"story_q{i}",
            type=QuestionType.MULTIPLE_CHOICE,
            command=cmd,
            difficulty="essential",
            question_text=f"Question about {cmd}?",
            correct_answer="correct",
            explanation=f"Explanation for {cmd}",
            points=10,
            options=["correct", "wrong1", "wrong2", "wrong3"]
        )
        for i, cmd in enumerate(commands)
    ]


@pytest.fixture
def player():
    """Create a test player."""
    return PlayerStats(username="StoryPlayer")


@pytest.fixture
def mock_console():
    """Create a mock console."""
    return Mock()


class TestLevel:
    """Tests for Level dataclass."""

    def test_create_level(self):
        """Test creating a level."""
        level = Level(
            id="level_1",
            name="Introduction",
            description="Learn the basics",
            story="Once upon a time...",
            commands=["ls", "cd"],
            questions_needed=3,
            xp_reward=100
        )
        assert level.id == "level_1"
        assert level.name == "Introduction"
        assert len(level.commands) == 2
        assert level.questions_needed == 3
        assert level.xp_reward == 100
        assert level.boss is False

    def test_create_boss_level(self):
        """Test creating a boss level."""
        level = Level(
            id="boss_1",
            name="Final Challenge",
            description="Face the boss",
            story="The final battle begins...",
            commands=["grep", "awk"],
            questions_needed=5,
            xp_reward=500,
            boss=True,
            boss_name="The Regex Master",
            boss_description="Master of pattern matching"
        )
        assert level.boss is True
        assert level.boss_name == "The Regex Master"
        assert level.xp_reward == 500


class TestChapter:
    """Tests for Chapter dataclass."""

    def test_create_chapter(self):
        """Test creating a chapter."""
        levels = [
            Level("l1", "Level 1", "First", "Story", ["ls"], 2, 50),
            Level("l2", "Level 2", "Second", "Story", ["cd"], 3, 75),
        ]
        chapter = Chapter(
            id="chapter_1",
            name="Getting Started",
            description="Learn basic commands",
            icon="📚",
            commands=["ls", "cd"],
            levels=levels
        )
        assert chapter.id == "chapter_1"
        assert chapter.name == "Getting Started"
        assert len(chapter.levels) == 2
        assert chapter.unlock_requirement is None

    def test_chapter_with_unlock_requirement(self):
        """Test chapter with unlock requirement."""
        chapter = Chapter(
            id="chapter_2",
            name="Advanced",
            description="Advanced commands",
            icon="🚀",
            commands=["grep"],
            levels=[],
            unlock_requirement="chapter_1"
        )
        assert chapter.unlock_requirement == "chapter_1"


class TestStoryEngineInit:
    """Tests for StoryEngine initialization."""

    def test_engine_init(self, mock_console, sample_questions, player):
        """Test story engine initialization."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)
            assert engine.console == mock_console
            assert engine.player == player
            assert len(engine.all_questions) == 5


class TestChapterUnlocking:
    """Tests for chapter unlocking logic."""

    def test_first_chapter_unlocked(self, mock_console, sample_questions, player):
        """Test that first chapter is always unlocked."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            chapter = Chapter(
                id="chapter_1",
                name="First",
                description="",
                icon="",
                commands=[],
                levels=[],
                unlock_requirement=None
            )

            assert engine.is_chapter_unlocked(chapter) is True

    def test_chapter_locked_without_requirement(self, mock_console, sample_questions, player):
        """Test chapter is locked when requirement not met."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            chapter = Chapter(
                id="chapter_2",
                name="Second",
                description="",
                icon="",
                commands=[],
                levels=[],
                unlock_requirement="chapter_1"
            )

            # Player hasn't completed chapter_1
            assert engine.is_chapter_unlocked(chapter) is False

    def test_chapter_unlocked_with_requirement(self, mock_console, sample_questions, player):
        """Test chapter unlocks when requirement is met."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            # Player completed chapter_1
            player.completed_chapters.append("chapter_1")

            chapter = Chapter(
                id="chapter_2",
                name="Second",
                description="",
                icon="",
                commands=[],
                levels=[],
                unlock_requirement="chapter_1"
            )

            assert engine.is_chapter_unlocked(chapter) is True


class TestLevelUnlocking:
    """Tests for level unlocking logic."""

    def test_first_level_unlocked(self, mock_console, sample_questions, player):
        """Test first level is always unlocked."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            chapter = Chapter(
                id="ch1",
                name="Chapter",
                description="",
                icon="",
                commands=[],
                levels=[
                    Level("l1", "Level 1", "", "", [], 3, 50),
                    Level("l2", "Level 2", "", "", [], 3, 50),
                ]
            )

            assert engine.is_level_unlocked(chapter, 0) is True

    def test_subsequent_level_locked(self, mock_console, sample_questions, player):
        """Test subsequent levels are locked initially."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            chapter = Chapter(
                id="ch1",
                name="Chapter",
                description="",
                icon="",
                commands=[],
                levels=[
                    Level("l1", "Level 1", "", "", [], 3, 50),
                    Level("l2", "Level 2", "", "", [], 3, 50),
                ]
            )

            assert engine.is_level_unlocked(chapter, 1) is False

    def test_level_unlocked_after_previous(self, mock_console, sample_questions, player):
        """Test level unlocks after completing previous."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            # Player completed l1
            player.completed_levels.append("l1")

            chapter = Chapter(
                id="ch1",
                name="Chapter",
                description="",
                icon="",
                commands=[],
                levels=[
                    Level("l1", "Level 1", "", "", [], 3, 50),
                    Level("l2", "Level 2", "", "", [], 3, 50),
                ]
            )

            assert engine.is_level_unlocked(chapter, 1) is True


class TestQuestionFiltering:
    """Tests for question filtering by commands."""

    def test_filter_questions_by_command(self, mock_console, sample_questions, player):
        """Test filtering questions for specific commands."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            # Filter for 'ls' command only
            filtered = [q for q in engine.all_questions if q.command == "ls"]
            assert len(filtered) == 1
            assert filtered[0].command == "ls"

    def test_filter_questions_multiple_commands(self, mock_console, sample_questions, player):
        """Test filtering for multiple commands."""
        with patch.object(StoryEngine, 'load_chapters'):
            engine = StoryEngine(mock_console, sample_questions, player)

            commands = ["ls", "cd", "pwd"]
            filtered = [q for q in engine.all_questions if q.command in commands]
            assert len(filtered) == 3


class TestProgressTracking:
    """Tests for story progress tracking."""

    def test_mark_level_complete(self, player):
        """Test marking a level as complete."""
        level = Level("test_level", "Test", "", "", [], 3, 100)

        # Simulate completing level
        player.completed_levels.append(level.id)
        player.xp += level.xp_reward

        assert level.id in player.completed_levels
        assert player.xp == 100

    def test_mark_chapter_complete(self, player):
        """Test marking a chapter as complete."""
        chapter = Chapter("test_chapter", "Test", "", "", [], [])

        player.completed_chapters.append(chapter.id)

        assert chapter.id in player.completed_chapters

    def test_progress_persists(self, player):
        """Test that progress accumulates correctly."""
        levels = [
            Level("l1", "Level 1", "", "", [], 2, 50),
            Level("l2", "Level 2", "", "", [], 3, 75),
            Level("l3", "Level 3", "", "", [], 4, 100),
        ]

        for level in levels:
            player.completed_levels.append(level.id)
            player.xp += level.xp_reward

        assert len(player.completed_levels) == 3
        assert player.xp == 225  # 50 + 75 + 100


class TestBossLevel:
    """Tests for boss level handling."""

    def test_boss_level_properties(self):
        """Test boss level has correct properties."""
        boss = Level(
            id="boss",
            name="Boss Fight",
            description="The final challenge",
            story="You face the ultimate test...",
            commands=["awk", "sed"],
            questions_needed=10,
            xp_reward=1000,
            boss=True,
            boss_name="The Shell Master",
            boss_description="Knows all commands"
        )

        assert boss.boss is True
        assert boss.questions_needed == 10
        assert boss.xp_reward == 1000
        assert "Shell Master" in boss.boss_name

    def test_boss_reward_higher(self):
        """Test boss levels have higher rewards."""
        normal = Level("l1", "Normal", "", "", ["ls"], 3, 50)
        boss = Level("b1", "Boss", "", "", ["ls"], 5, 200, boss=True)

        assert boss.xp_reward > normal.xp_reward
        assert boss.questions_needed > normal.questions_needed
