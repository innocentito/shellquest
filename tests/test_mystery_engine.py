"""Unit tests for the Mystery Engine."""

import pytest
from unittest.mock import Mock, patch
from shellquest.core.mystery_engine import (
    MysteryEngine, Challenge, Scene, Suspect, MysteryCase
)
from shellquest.models.player import PlayerStats


@pytest.fixture
def player():
    """Create a test player."""
    return PlayerStats(username="Detective")


@pytest.fixture
def mock_console():
    """Create a mock console."""
    return Mock()


class TestChallenge:
    """Tests for Challenge dataclass."""

    def test_create_challenge(self):
        """Test creating a challenge."""
        challenge = Challenge(
            id="ch1",
            context="You found a clue...",
            question_type="multiple_choice",
            question="What command lists files?",
            correct_answers=["ls"],
            hint="Think about listing...",
            success_narrative="You found the answer!",
            clue_unlocked="The victim used ls",
            options=["ls", "cd", "rm", "cat"]
        )
        assert challenge.id == "ch1"
        assert challenge.question_type == "multiple_choice"
        assert "ls" in challenge.correct_answers
        assert len(challenge.options) == 4

    def test_challenge_multiple_answers(self):
        """Test challenge with multiple correct answers."""
        challenge = Challenge(
            id="ch2",
            context="Context",
            question_type="fill_blank",
            question="List hidden files?",
            correct_answers=["ls -a", "ls -la", "ls -al"],
            hint="Use a flag",
            success_narrative="Correct!",
            clue_unlocked="Hidden files revealed",
            options=[]
        )
        assert len(challenge.correct_answers) == 3


class TestScene:
    """Tests for Scene dataclass."""

    def test_create_scene(self):
        """Test creating a scene."""
        challenges = [
            Challenge("c1", "ctx", "mc", "q1", ["a"], "h", "s", "clue1", ["a", "b"]),
            Challenge("c2", "ctx", "fb", "q2", ["b"], "h", "s", "clue2", []),
        ]
        scene = Scene(
            id="scene1",
            title="The Office",
            location="Building A",
            narrative="You enter the office...",
            objective="Find the hidden file",
            challenges=challenges
        )
        assert scene.id == "scene1"
        assert scene.title == "The Office"
        assert len(scene.challenges) == 2

    def test_scene_clue_count(self):
        """Test counting clues in a scene."""
        challenges = [
            Challenge(f"c{i}", "ctx", "mc", "q", ["a"], "h", "s", f"clue{i}", [])
            for i in range(5)
        ]
        scene = Scene("s1", "Title", "Loc", "Narr", "Obj", challenges)
        assert len(scene.challenges) == 5


class TestSuspect:
    """Tests for Suspect dataclass."""

    def test_create_suspect(self):
        """Test creating a suspect."""
        suspect = Suspect(
            id="suspect1",
            name="John Doe",
            role="System Admin",
            description="Has access to all systems",
            alibi="Was at a conference",
            motive="Wanted a promotion"
        )
        assert suspect.name == "John Doe"
        assert suspect.role == "System Admin"
        assert "conference" in suspect.alibi
        assert "promotion" in suspect.motive


class TestMysteryCase:
    """Tests for MysteryCase dataclass."""

    def test_create_case(self):
        """Test creating a mystery case."""
        case = MysteryCase(
            id="case1",
            title="The Missing Log",
            subtitle="A tale of deleted files",
            difficulty="medium",
            intro="The server logs are missing...",
            setting="Tech Company HQ",
            suspects=[
                Suspect("s1", "Alice", "Dev", "Knows commands", "Alibi 1", "Motive 1"),
                Suspect("s2", "Bob", "Admin", "Full access", "Alibi 2", "Motive 2"),
            ],
            scenes=[],
            conclusion_success="You solved it!",
            conclusion_failure="The case went cold.",
            rewards={"xp": 500}
        )
        assert case.id == "case1"
        assert case.difficulty == "medium"
        assert len(case.suspects) == 2
        assert case.rewards["xp"] == 500


class TestMysteryEngineInit:
    """Tests for MysteryEngine initialization."""

    def test_engine_init(self, mock_console, player):
        """Test mystery engine initialization."""
        engine = MysteryEngine(mock_console, player)
        assert engine.console == mock_console
        assert engine.player == player
        assert engine.clues_found == []
        assert engine.scenes_completed == 0
        assert engine.total_clues == 0


class TestAnswerChecking:
    """Tests for answer checking logic."""

    def test_check_correct_answer(self, mock_console, player):
        """Test checking a correct answer."""
        engine = MysteryEngine(mock_console, player)
        challenge = Challenge(
            id="test",
            context="ctx",
            question_type="fill_blank",
            question="What command?",
            correct_answers=["ls", "LS"],
            hint="hint",
            success_narrative="success",
            clue_unlocked="clue",
            options=[]
        )

        assert engine.check_answer("ls", challenge) is True
        assert engine.check_answer("LS", challenge) is True
        assert engine.check_answer("  ls  ", challenge) is True

    def test_check_wrong_answer(self, mock_console, player):
        """Test checking a wrong answer."""
        engine = MysteryEngine(mock_console, player)
        challenge = Challenge(
            id="test",
            context="ctx",
            question_type="fill_blank",
            question="What command?",
            correct_answers=["ls"],
            hint="hint",
            success_narrative="success",
            clue_unlocked="clue",
            options=[]
        )

        assert engine.check_answer("cd", challenge) is False
        assert engine.check_answer("wrong", challenge) is False

    def test_check_answer_case_insensitive(self, mock_console, player):
        """Test case insensitive answer checking."""
        engine = MysteryEngine(mock_console, player)
        challenge = Challenge(
            id="test",
            context="",
            question_type="mc",
            question="?",
            correct_answers=["grep"],
            hint="",
            success_narrative="",
            clue_unlocked="",
            options=[]
        )

        assert engine.check_answer("GREP", challenge) is True
        assert engine.check_answer("Grep", challenge) is True
        assert engine.check_answer("gReP", challenge) is True

    def test_no_substring_exploit(self, mock_console, player):
        """Test that substring matching is NOT allowed (bug fix)."""
        engine = MysteryEngine(mock_console, player)
        challenge = Challenge(
            id="test",
            context="",
            question_type="mc",
            question="?",
            correct_answers=["ls"],
            hint="",
            success_narrative="",
            clue_unlocked="",
            options=[]
        )

        # "ls" should not match in "false" - this was a bug
        assert engine.check_answer("false", challenge) is False
        assert engine.check_answer("als", challenge) is False
        assert engine.check_answer("lsof", challenge) is False


class TestClueTracking:
    """Tests for clue tracking."""

    def test_clue_collection(self, mock_console, player):
        """Test collecting clues."""
        engine = MysteryEngine(mock_console, player)

        engine.clues_found.append("Clue 1")
        engine.clues_found.append("Clue 2")

        assert len(engine.clues_found) == 2
        assert "Clue 1" in engine.clues_found

    def test_clue_percentage(self, mock_console, player):
        """Test calculating clue percentage."""
        engine = MysteryEngine(mock_console, player)
        engine.total_clues = 10

        engine.clues_found = ["c1", "c2", "c3", "c4", "c5", "c6"]
        percentage = (len(engine.clues_found) / engine.total_clues) * 100

        assert percentage == 60.0


class TestCaseCompletion:
    """Tests for case completion logic."""

    def test_success_threshold(self, mock_console, player):
        """Test success threshold (60% clues)."""
        engine = MysteryEngine(mock_console, player)
        engine.total_clues = 10

        # 60% = success
        engine.clues_found = list(range(6))
        pct = (len(engine.clues_found) / engine.total_clues) * 100
        assert pct >= 60

        # 50% = failure
        engine.clues_found = list(range(5))
        pct = (len(engine.clues_found) / engine.total_clues) * 100
        assert pct < 60

    def test_mystery_tracking(self, player):
        """Test that solved mysteries are tracked."""
        assert len(player.solved_mysteries) == 0

        player.solved_mysteries.append("case1")
        assert "case1" in player.solved_mysteries

        player.solved_mysteries.append("case2")
        assert len(player.solved_mysteries) == 2


class TestSceneProgression:
    """Tests for scene progression."""

    def test_scenes_completed_progression(self, mock_console, player):
        """Test scenes_completed increases."""
        engine = MysteryEngine(mock_console, player)

        assert engine.scenes_completed == 0
        engine.scenes_completed += 1
        assert engine.scenes_completed == 1

    def test_reset_for_new_case(self, mock_console, player):
        """Test state resets for new case."""
        engine = MysteryEngine(mock_console, player)

        # Simulate playing a case
        engine.scenes_completed = 3
        engine.clues_found = ["c1", "c2"]
        engine.total_clues = 5

        # Reset for new case
        engine.scenes_completed = 0
        engine.clues_found = []
        engine.total_clues = 0

        assert engine.scenes_completed == 0
        assert len(engine.clues_found) == 0
        assert engine.total_clues == 0
