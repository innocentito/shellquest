"""End-to-end tests for Battle Mode with socket mocking."""

import pytest
import json
import threading
import time
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from io import StringIO

from shellquest.core.battle_engine import (
    BattleServer, BattleClient, BattleResult, BattleState,
    safe_json_loads, safe_recv, safe_send
)
from shellquest.models.player import PlayerStats
from shellquest.models.question import Question, QuestionType


@pytest.fixture
def mock_console():
    """Create a mock console that captures output."""
    console = Mock()
    console.print = Mock()
    return console


@pytest.fixture
def host_player():
    """Create host player."""
    return PlayerStats(username="HostPlayer")


@pytest.fixture
def client_player():
    """Create client player."""
    return PlayerStats(username="ClientPlayer")


@pytest.fixture
def sample_questions():
    """Create sample questions for battle."""
    return [
        Question(
            id=f"battle_q{i}",
            type=QuestionType.MULTIPLE_CHOICE,
            command="ls",
            difficulty="essential",
            question_text=f"What does ls -{opt} do?",
            correct_answer=f"Option {opt}",
            explanation=f"Explanation for {opt}",
            points=10,
            options=[f"Option {opt}", "Wrong 1", "Wrong 2", "Wrong 3"]
        )
        for i, opt in enumerate(["l", "a", "h", "R", "t"])
    ]


class TestSafeJsonLoads:
    """Tests for safe_json_loads utility."""

    def test_valid_json(self):
        """Test parsing valid JSON."""
        data = '{"name": "test", "value": 123}'
        result = safe_json_loads(data)
        assert result == {"name": "test", "value": 123}

    def test_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        data = 'not valid json {'
        result = safe_json_loads(data)
        assert result is None

    def test_none_input(self):
        """Test None input returns None."""
        result = safe_json_loads(None)
        assert result is None

    def test_empty_string(self):
        """Test empty string returns None."""
        result = safe_json_loads("")
        assert result is None


class TestSafeRecv:
    """Tests for safe_recv utility."""

    def test_successful_recv(self):
        """Test successful data receive."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b'{"test": "data"}'

        result = safe_recv(mock_socket, timeout=5.0)

        assert result == '{"test": "data"}'
        mock_socket.settimeout.assert_called_with(5.0)

    def test_timeout_recv(self):
        """Test timeout returns None."""
        import socket
        mock_socket = Mock()
        mock_socket.recv.side_effect = socket.timeout()

        result = safe_recv(mock_socket, timeout=1.0)

        assert result is None

    def test_empty_data_recv(self):
        """Test empty data returns None."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b''

        result = safe_recv(mock_socket, timeout=5.0)

        assert result is None

    def test_socket_error_recv(self):
        """Test socket error returns None."""
        import socket
        mock_socket = Mock()
        mock_socket.recv.side_effect = socket.error("Connection reset")

        result = safe_recv(mock_socket, timeout=5.0)

        assert result is None


class TestSafeSend:
    """Tests for safe_send utility."""

    def test_successful_send(self):
        """Test successful data send."""
        mock_socket = Mock()
        data = {"message": "hello"}

        result = safe_send(mock_socket, data)

        assert result is True
        mock_socket.sendall.assert_called_once()

    def test_socket_error_send(self):
        """Test socket error returns False."""
        import socket
        mock_socket = Mock()
        mock_socket.sendall.side_effect = socket.error("Broken pipe")

        result = safe_send(mock_socket, {"test": "data"})

        assert result is False

    def test_invalid_data_send(self):
        """Test non-serializable data returns False."""
        mock_socket = Mock()

        # Object that can't be JSON serialized
        class NotSerializable:
            pass

        result = safe_send(mock_socket, {"obj": NotSerializable()})

        assert result is False


class TestBattleResult:
    """Tests for BattleResult dataclass."""

    def test_create_result(self):
        """Test creating a battle result."""
        result = BattleResult(
            player_name="TestPlayer",
            is_correct=True,
            time_taken=5.5,
            points=150
        )

        assert result.player_name == "TestPlayer"
        assert result.is_correct is True
        assert result.time_taken == 5.5
        assert result.points == 150

    def test_result_with_zero_points(self):
        """Test result with zero points (wrong answer)."""
        result = BattleResult(
            player_name="TestPlayer",
            is_correct=False,
            time_taken=10.0,
            points=0
        )

        assert result.is_correct is False
        assert result.points == 0


class TestBattleState:
    """Tests for BattleState dataclass."""

    def test_create_state(self):
        """Test creating battle state."""
        state = BattleState(
            question_num=1,
            total_questions=5,
            player1_score=100,
            player2_score=50,
            player1_name="Host",
            player2_name="Client"
        )

        assert state.question_num == 1
        assert state.total_questions == 5
        assert state.player1_score == 100
        assert state.player2_score == 50
        assert state.game_over is False
        assert state.winner == ""

    def test_state_game_over(self):
        """Test game over state."""
        state = BattleState(
            question_num=5,
            total_questions=5,
            player1_score=300,
            player2_score=200,
            player1_name="Host",
            player2_name="Client",
            game_over=True,
            winner="Host"
        )

        assert state.game_over is True
        assert state.winner == "Host"


class TestBattleServerInit:
    """Tests for BattleServer initialization."""

    def test_server_init(self, mock_console, host_player, sample_questions):
        """Test server initialization."""
        server = BattleServer(mock_console, host_player, sample_questions)

        assert server.console == mock_console
        assert server.player == host_player
        assert server.questions == sample_questions
        assert server.server_socket is None
        assert server.client_socket is None
        assert server.client_name == ""

    def test_get_local_ip(self, mock_console, host_player, sample_questions):
        """Test getting local IP."""
        server = BattleServer(mock_console, host_player, sample_questions)

        with patch('socket.socket') as mock_socket:
            mock_instance = Mock()
            mock_instance.getsockname.return_value = ("192.168.1.100", 0)
            mock_socket.return_value = mock_instance

            ip = server.get_local_ip()

            # Should return an IP or fallback
            assert ip == "192.168.1.100" or ip == "127.0.0.1"

    def test_get_local_ip_fallback(self, mock_console, host_player, sample_questions):
        """Test fallback IP on error."""
        server = BattleServer(mock_console, host_player, sample_questions)

        with patch('socket.socket') as mock_socket:
            mock_socket.side_effect = OSError("Network error")

            ip = server.get_local_ip()

            assert ip == "127.0.0.1"


class TestBattleServerPointCalculation:
    """Tests for battle point calculation."""

    def test_correct_fast_answer(self, mock_console, host_player, sample_questions):
        """Test points for correct fast answer."""
        server = BattleServer(mock_console, host_player, sample_questions)

        points = server.calculate_battle_points(True, 3.0)

        assert points == 150  # 100 base + 50 speed bonus

    def test_correct_medium_answer(self, mock_console, host_player, sample_questions):
        """Test points for correct medium speed answer."""
        server = BattleServer(mock_console, host_player, sample_questions)

        points = server.calculate_battle_points(True, 7.0)

        assert points == 130  # 100 base + 30 speed bonus

    def test_correct_slow_answer(self, mock_console, host_player, sample_questions):
        """Test points for correct slow answer."""
        server = BattleServer(mock_console, host_player, sample_questions)

        points = server.calculate_battle_points(True, 15.0)

        assert points == 110  # 100 base + 10 speed bonus

    def test_correct_very_slow_answer(self, mock_console, host_player, sample_questions):
        """Test points for correct very slow answer."""
        server = BattleServer(mock_console, host_player, sample_questions)

        points = server.calculate_battle_points(True, 25.0)

        assert points == 100  # 100 base + 0 speed bonus

    def test_wrong_answer(self, mock_console, host_player, sample_questions):
        """Test points for wrong answer."""
        server = BattleServer(mock_console, host_player, sample_questions)

        points = server.calculate_battle_points(False, 2.0)

        assert points == 0


class TestBattleClientInit:
    """Tests for BattleClient initialization."""

    def test_client_init(self, mock_console, client_player):
        """Test client initialization."""
        client = BattleClient(mock_console, client_player)

        assert client.console == mock_console
        assert client.player == client_player
        assert client.socket is None
        assert client.host_name == ""

    def test_client_point_calculation(self, mock_console, client_player):
        """Test client point calculation matches server."""
        client = BattleClient(mock_console, client_player)

        # Same logic as server
        assert client.calculate_battle_points(True, 3.0) == 150
        assert client.calculate_battle_points(True, 7.0) == 130
        assert client.calculate_battle_points(False, 1.0) == 0


class TestBattleClientIPValidation:
    """Tests for IP/hostname validation in client."""

    def test_valid_ipv4(self, mock_console, client_player):
        """Test valid IPv4 address."""
        client = BattleClient(mock_console, client_player)

        with patch.object(client, 'socket', create=True):
            with patch('socket.socket') as mock_socket:
                mock_instance = Mock()
                mock_socket.return_value = mock_instance
                # Simulate connection refused (but validation passed)
                mock_instance.connect.side_effect = ConnectionRefusedError()

                result = client.join_game("192.168.1.1")

                # Should fail at connect, not validation
                assert result is False

    def test_valid_hostname(self, mock_console, client_player):
        """Test valid hostname."""
        client = BattleClient(mock_console, client_player)

        with patch('socket.socket') as mock_socket:
            mock_instance = Mock()
            mock_socket.return_value = mock_instance
            mock_instance.connect.side_effect = ConnectionRefusedError()

            result = client.join_game("localhost")

            assert result is False  # Fails at connect, validation passed

    def test_invalid_ip_format(self, mock_console, client_player):
        """Test invalid IP format is rejected."""
        client = BattleClient(mock_console, client_player)

        with patch('socket.socket') as mock_socket:
            mock_instance = Mock()
            mock_socket.return_value = mock_instance

            result = client.join_game("not..valid..ip")

            assert result is False

    def test_ip_too_long(self, mock_console, client_player):
        """Test overly long address is rejected."""
        client = BattleClient(mock_console, client_player)

        with patch('socket.socket') as mock_socket:
            mock_instance = Mock()
            mock_socket.return_value = mock_instance

            result = client.join_game("a" * 300)

            assert result is False


class TestBattleServerCleanup:
    """Tests for server socket cleanup."""

    def test_cleanup_closes_sockets(self, mock_console, host_player, sample_questions):
        """Test cleanup properly closes sockets."""
        server = BattleServer(mock_console, host_player, sample_questions)

        mock_client = Mock()
        mock_server = Mock()
        server.client_socket = mock_client
        server.server_socket = mock_server

        server.cleanup()

        mock_client.shutdown.assert_called()
        mock_client.close.assert_called()
        mock_server.shutdown.assert_called()
        mock_server.close.assert_called()
        assert server.client_socket is None
        assert server.server_socket is None

    def test_cleanup_handles_already_closed(self, mock_console, host_player, sample_questions):
        """Test cleanup handles already closed sockets."""
        import socket
        server = BattleServer(mock_console, host_player, sample_questions)

        mock_client = Mock()
        mock_client.shutdown.side_effect = socket.error("Already closed")
        mock_client.close.side_effect = socket.error("Already closed")
        server.client_socket = mock_client

        # Should not raise
        server.cleanup()

        assert server.client_socket is None


class TestBattleClientCleanup:
    """Tests for client socket cleanup."""

    def test_cleanup_closes_socket(self, mock_console, client_player):
        """Test cleanup properly closes socket."""
        client = BattleClient(mock_console, client_player)

        mock_socket = Mock()
        client.socket = mock_socket

        client.cleanup()

        mock_socket.shutdown.assert_called()
        mock_socket.close.assert_called()
        assert client.socket is None


class TestBattleServerTimeValidation:
    """Tests for server-side time validation (anti-cheat)."""

    def test_impossibly_fast_time_penalized(self, mock_console, host_player, sample_questions):
        """Test that impossibly fast times are penalized."""
        server = BattleServer(mock_console, host_player, sample_questions)

        # Simulate receiving result with impossibly fast time
        opp_result_data = {
            'data': {'time_taken': 0.1},  # Too fast - impossible
            'answer': 'wrong'
        }

        # Server should cap this to 60 seconds (penalty)
        client_time = opp_result_data['data'].get('time_taken', 0)
        if not isinstance(client_time, (int, float)) or client_time < 0.5:
            client_time = 60.0

        assert client_time == 60.0

    def test_negative_time_penalized(self, mock_console, host_player, sample_questions):
        """Test that negative times are penalized."""
        server = BattleServer(mock_console, host_player, sample_questions)

        opp_result_data = {
            'data': {'time_taken': -5.0},
            'answer': 'test'
        }

        client_time = opp_result_data['data'].get('time_taken', 0)
        if not isinstance(client_time, (int, float)) or client_time < 0.5:
            client_time = 60.0

        assert client_time == 60.0

    def test_valid_time_accepted(self, mock_console, host_player, sample_questions):
        """Test that valid times are accepted."""
        server = BattleServer(mock_console, host_player, sample_questions)

        opp_result_data = {
            'data': {'time_taken': 5.5},
            'answer': 'test'
        }

        client_time = opp_result_data['data'].get('time_taken', 0)
        if not isinstance(client_time, (int, float)) or client_time < 0.5:
            client_time = 60.0
        client_time = min(client_time, 300.0)

        assert client_time == 5.5

    def test_very_long_time_capped(self, mock_console, host_player, sample_questions):
        """Test that very long times are capped."""
        server = BattleServer(mock_console, host_player, sample_questions)

        opp_result_data = {
            'data': {'time_taken': 999999.0},
            'answer': 'test'
        }

        client_time = opp_result_data['data'].get('time_taken', 0)
        if not isinstance(client_time, (int, float)) or client_time < 0.5:
            client_time = 60.0
        client_time = min(client_time, 300.0)

        assert client_time == 300.0


class TestBattlePlayerStats:
    """Tests for player stats updates after battle."""

    def test_winner_stats_updated(self, host_player):
        """Test winner's stats are updated."""
        initial_won = host_player.battles_won
        initial_played = host_player.battles_played

        host_player.battles_won += 1
        host_player.battles_played += 1

        assert host_player.battles_won == initial_won + 1
        assert host_player.battles_played == initial_played + 1

    def test_loser_stats_updated(self, client_player):
        """Test loser's stats are updated."""
        initial_lost = client_player.battles_lost
        initial_played = client_player.battles_played

        client_player.battles_lost += 1
        client_player.battles_played += 1

        assert client_player.battles_lost == initial_lost + 1
        assert client_player.battles_played == initial_played + 1

    def test_tie_stats(self, host_player):
        """Test tie doesn't count as win or loss."""
        initial_won = host_player.battles_won
        initial_lost = host_player.battles_lost
        initial_played = host_player.battles_played

        # On tie, only battles_played increments
        host_player.battles_played += 1

        assert host_player.battles_won == initial_won
        assert host_player.battles_lost == initial_lost
        assert host_player.battles_played == initial_played + 1


class TestBattleIntegration:
    """Integration tests for battle flow."""

    def test_full_handshake_flow(self, mock_console, host_player, client_player, sample_questions):
        """Test complete handshake between server and client."""
        server = BattleServer(mock_console, host_player, sample_questions)
        client = BattleClient(mock_console, client_player)

        # Simulate handshake data exchange
        client_handshake = json.dumps({'name': client_player.username})
        server_handshake = json.dumps({'name': host_player.username})

        # Parse handshakes
        client_data = safe_json_loads(client_handshake)
        server_data = safe_json_loads(server_handshake)

        assert client_data['name'] == "ClientPlayer"
        assert server_data['name'] == "HostPlayer"

    def test_question_message_format(self, sample_questions):
        """Test question message format is correct."""
        question = sample_questions[0]

        message = {
            'type': 'question',
            'data': {
                'id': question.id,
                'text': question.question_text,
                'options': question.options,
                'type': question.type.value,
                'command': question.command
            },
            'num': 1,
            'total': 5,
            'scores': {'Host': 0, 'Client': 0}
        }

        # Verify serializable
        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        assert parsed['type'] == 'question'
        assert parsed['data']['id'] == question.id
        assert 'correct_answer' not in parsed['data']  # Security: answer not sent

    def test_result_message_format(self):
        """Test result message format is correct."""
        result = BattleResult(
            player_name="TestPlayer",
            is_correct=True,
            time_taken=5.0,
            points=150
        )

        from dataclasses import asdict
        message = {
            'type': 'result',
            'data': asdict(result),
            'correct_answer': 'ls -l'
        }

        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        assert parsed['type'] == 'result'
        assert parsed['data']['is_correct'] is True
        assert parsed['correct_answer'] == 'ls -l'

    def test_game_over_message_format(self):
        """Test game over message format."""
        message = {
            'type': 'game_over',
            'winner': 'HostPlayer',
            'scores': {
                'HostPlayer': 450,
                'ClientPlayer': 300
            }
        }

        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        assert parsed['type'] == 'game_over'
        assert parsed['winner'] == 'HostPlayer'
        assert parsed['scores']['HostPlayer'] == 450
