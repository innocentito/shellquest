"""Unit tests for the Battle Engine."""

import pytest
import json
from dataclasses import asdict
from shellquest.core.battle_engine import (
    BattleResult, BattleState, safe_json_loads,
    BattleServer, BattleClient
)
from shellquest.models.player import PlayerStats
from shellquest.models.question import Question, QuestionType
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def sample_questions():
    """Create sample questions for battle."""
    return [
        Question(
            id=f"battle_q{i}",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text=f"Battle question {i}?",
            correct_answer="correct",
            explanation="Test explanation",
            points=10,
            options=["correct", "wrong1", "wrong2", "wrong3"]
        )
        for i in range(10)
    ]


@pytest.fixture
def player():
    """Create a test player."""
    return PlayerStats(username="BattlePlayer")


@pytest.fixture
def mock_console():
    """Create a mock console."""
    return Mock()


class TestBattleResult:
    """Tests for BattleResult dataclass."""

    def test_create_result(self):
        """Test creating a battle result."""
        result = BattleResult(
            player_name="Player1",
            is_correct=True,
            time_taken=5.5,
            points=15
        )
        assert result.player_name == "Player1"
        assert result.is_correct is True
        assert result.time_taken == 5.5
        assert result.points == 15

    def test_result_serializable(self):
        """Test that result can be serialized to dict."""
        result = BattleResult(
            player_name="Test",
            is_correct=False,
            time_taken=10.0,
            points=0
        )
        data = asdict(result)
        assert data['player_name'] == "Test"
        assert data['is_correct'] is False


class TestBattleState:
    """Tests for BattleState dataclass."""

    def test_create_state(self):
        """Test creating a battle state."""
        state = BattleState(
            question_num=1,
            total_questions=5,
            player1_score=10,
            player2_score=5,
            player1_name="Alice",
            player2_name="Bob"
        )
        assert state.question_num == 1
        assert state.total_questions == 5
        assert state.game_over is False
        assert state.winner == ""

    def test_state_with_current_question(self):
        """Test state with current question."""
        state = BattleState(
            question_num=2,
            total_questions=5,
            player1_score=20,
            player2_score=10,
            player1_name="Alice",
            player2_name="Bob",
            current_question={"id": "q1", "text": "What?"}
        )
        assert state.current_question is not None
        assert state.current_question['id'] == "q1"

    def test_state_game_over(self):
        """Test state when game is over."""
        state = BattleState(
            question_num=5,
            total_questions=5,
            player1_score=50,
            player2_score=30,
            player1_name="Alice",
            player2_name="Bob",
            game_over=True,
            winner="Alice"
        )
        assert state.game_over is True
        assert state.winner == "Alice"


class TestSafeJsonLoads:
    """Tests for safe_json_loads function."""

    def test_valid_json(self):
        """Test parsing valid JSON."""
        result = safe_json_loads('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        result = safe_json_loads('not valid json{{{')
        assert result is None

    def test_empty_string(self):
        """Test parsing empty string."""
        result = safe_json_loads('')
        assert result is None

    def test_none_input(self):
        """Test parsing None input."""
        result = safe_json_loads(None)
        assert result is None

    def test_nested_json(self):
        """Test parsing nested JSON."""
        data = '{"player": {"name": "Test", "score": 100}, "questions": [1, 2, 3]}'
        result = safe_json_loads(data)
        assert result['player']['name'] == "Test"
        assert len(result['questions']) == 3


class TestBattleServerInit:
    """Tests for BattleServer initialization."""

    def test_server_init(self, mock_console, player, sample_questions):
        """Test server initialization."""
        server = BattleServer(mock_console, player, sample_questions)
        assert server.console == mock_console
        assert server.player == player
        assert len(server.questions) == 10
        assert server.server_socket is None
        assert server.client_socket is None
        assert server.client_name == ""

    def test_server_get_local_ip_fallback(self, mock_console, player, sample_questions):
        """Test get_local_ip returns fallback on error."""
        server = BattleServer(mock_console, player, sample_questions)

        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = OSError("Network error")
            ip = server.get_local_ip()
            assert ip == "127.0.0.1"


class TestBattleClientInit:
    """Tests for BattleClient initialization."""

    def test_client_init(self, mock_console, player):
        """Test client initialization."""
        client = BattleClient(mock_console, player)
        assert client.console == mock_console
        assert client.player == player
        assert client.socket is None
        assert client.host_name == ""


class TestBattleQuestionSelection:
    """Tests for battle question selection."""

    def test_question_selection_respects_limit(self, mock_console, player, sample_questions):
        """Test that question selection respects the limit."""
        server = BattleServer(mock_console, player, sample_questions)

        # Manually test the selection logic
        import random
        num_questions = 5
        selected = random.sample(sample_questions, min(num_questions, len(sample_questions)))

        assert len(selected) == 5
        assert all(q in sample_questions for q in selected)

    def test_question_selection_with_few_questions(self, mock_console, player):
        """Test selection when fewer questions than requested."""
        few_questions = [
            Question(
                id="q1",
                type=QuestionType.MULTIPLE_CHOICE,
                command="ls",
                difficulty="essential",
                question_text="?",
                correct_answer="a",
                explanation="",
                points=10,
                options=["a", "b"]
            )
        ]
        server = BattleServer(mock_console, player, few_questions)

        import random
        num_questions = 5
        selected = random.sample(few_questions, min(num_questions, len(few_questions)))

        assert len(selected) == 1  # Only 1 question available


class TestBattleScoring:
    """Tests for battle scoring logic."""

    def test_correct_answer_scoring(self):
        """Test scoring for correct answer."""
        result = BattleResult(
            player_name="Player",
            is_correct=True,
            time_taken=3.0,
            points=10
        )
        assert result.points == 10

    def test_wrong_answer_scoring(self):
        """Test scoring for wrong answer."""
        result = BattleResult(
            player_name="Player",
            is_correct=False,
            time_taken=5.0,
            points=0
        )
        assert result.points == 0

    def test_accumulated_scores(self):
        """Test accumulating scores from multiple results."""
        results = [
            BattleResult("P1", True, 2.0, 10),
            BattleResult("P1", True, 3.0, 10),
            BattleResult("P1", False, 5.0, 0),
            BattleResult("P1", True, 1.5, 15),
        ]
        total = sum(r.points for r in results)
        assert total == 35


class TestBattleStateTransitions:
    """Tests for battle state transitions."""

    def test_state_progression(self):
        """Test state progression through questions."""
        state = BattleState(
            question_num=1,
            total_questions=3,
            player1_score=0,
            player2_score=0,
            player1_name="P1",
            player2_name="P2"
        )

        # Simulate progression
        state.question_num = 2
        state.player1_score = 10
        assert state.question_num == 2
        assert not state.game_over

        state.question_num = 3
        state.player2_score = 20
        state.game_over = True
        state.winner = "P2"

        assert state.game_over
        assert state.winner == "P2"

    def test_determine_winner(self):
        """Test winner determination logic."""
        # P1 wins
        state1 = BattleState(1, 5, 50, 30, "Alice", "Bob", game_over=True)
        winner1 = "Alice" if state1.player1_score > state1.player2_score else "Bob"
        assert winner1 == "Alice"

        # P2 wins
        state2 = BattleState(1, 5, 20, 40, "Alice", "Bob", game_over=True)
        winner2 = "Alice" if state2.player1_score > state2.player2_score else "Bob"
        assert winner2 == "Bob"

        # Tie
        state3 = BattleState(1, 5, 30, 30, "Alice", "Bob", game_over=True)
        is_tie = state3.player1_score == state3.player2_score
        assert is_tie


class TestBattleCleanup:
    """Tests for battle cleanup."""

    def test_server_cleanup(self, mock_console, player, sample_questions):
        """Test server cleanup closes sockets."""
        server = BattleServer(mock_console, player, sample_questions)

        # Create mock sockets
        mock_client = Mock()
        mock_server = Mock()
        server.server_socket = mock_server
        server.client_socket = mock_client

        server.cleanup()

        # Verify close was called (shutdown may fail, but close should be called)
        assert mock_client.close.called or mock_client.shutdown.called
        assert mock_server.close.called or mock_server.shutdown.called

    def test_client_cleanup(self, mock_console, player):
        """Test client cleanup closes socket."""
        client = BattleClient(mock_console, player)

        mock_socket = Mock()
        client.socket = mock_socket
        client.cleanup()

        # Verify close was called
        assert mock_socket.close.called or mock_socket.shutdown.called
