"""Battle mode engine for ShellQuest - LAN Multiplayer."""

import socket
import threading
import json
import time
import random
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
from rich.table import Table

from ..ui.theme import Theme
from ..ui.components import UIComponents
from ..models.player import PlayerStats
from ..models.question import Question
from ..utils import (
    logger, clear_terminal, sanitize_name,
    DEFAULT_PORT, BUFFER_SIZE, SOCKET_TIMEOUT, MAX_NAME_LENGTH
)


def safe_json_loads(data: str) -> Optional[dict]:
    """Safely parse JSON data."""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"JSON parse error: {e}")
        return None


def safe_recv(sock: socket.socket, timeout: float = SOCKET_TIMEOUT) -> Optional[str]:
    """Safely receive data from socket with timeout."""
    try:
        sock.settimeout(timeout)
        data = sock.recv(BUFFER_SIZE)
        if not data:
            return None
        return data.decode('utf-8', errors='replace')
    except socket.timeout:
        logger.warning("Socket receive timeout")
        return None
    except (socket.error, OSError) as e:
        logger.error(f"Socket receive error: {e}")
        return None


def safe_send(sock: socket.socket, data: dict) -> bool:
    """Safely send JSON data through socket."""
    try:
        json_data = json.dumps(data)
        sock.sendall(json_data.encode('utf-8'))
        return True
    except (socket.error, OSError, TypeError) as e:
        logger.error(f"Socket send error: {e}")
        return False


@dataclass
class BattleResult:
    """Result of a battle question."""
    player_name: str
    is_correct: bool
    time_taken: float
    points: int


@dataclass
class BattleState:
    """Current state of a battle."""
    question_num: int
    total_questions: int
    player1_score: int
    player2_score: int
    player1_name: str
    player2_name: str
    current_question: Optional[dict] = None
    game_over: bool = False
    winner: str = ""


class BattleServer:
    """Server for hosting a battle."""

    def __init__(self, console: Console, player: PlayerStats, questions: List[Question]):
        self.console = console
        self.player = player
        self.questions = questions
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.client_name: str = ""
        self.battle_questions: List[Question] = []
        self.state: Optional[BattleState] = None
        self.my_results: List[BattleResult] = []
        self.opponent_results: List[BattleResult] = []

    def get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except (socket.error, OSError):
            return "127.0.0.1"

    def host_game(self, num_questions: int = 5) -> bool:
        """Host a battle game."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', DEFAULT_PORT))
            self.server_socket.listen(1)

            local_ip = self.get_local_ip()

            clear_terminal()
            self.console.print(Panel(
                Align.center(Text.assemble(
                    ("\n⚔️ BATTLE MODE - HOST ⚔️\n\n", f"bold {Theme.WARNING}"),
                    ("Waiting for opponent...\n\n", "white"),
                    ("Share this with your opponent:\n", "dim"),
                    (f"\n  IP: {local_ip}\n", f"bold {Theme.PRIMARY}"),
                    (f"  Port: {DEFAULT_PORT}\n\n", f"bold {Theme.PRIMARY}"),
                    ("Press Ctrl+C to cancel\n", "dim"),
                )),
                border_style=Theme.WARNING
            ))

            # Wait for connection
            self.server_socket.settimeout(300)  # 5 min timeout
            self.client_socket, addr = self.server_socket.accept()
            logger.info(f"Battle connection from {addr}")

            # Receive client name with validation
            data = safe_recv(self.client_socket, timeout=30)
            if not data:
                raise ConnectionError("No data received from client")

            client_info = safe_json_loads(data)
            if not client_info or 'name' not in client_info:
                raise ValueError("Invalid client handshake")

            self.client_name = sanitize_name(client_info['name'])

            # Send host name
            if not safe_send(self.client_socket, {'name': sanitize_name(self.player.username)}):
                raise ConnectionError("Failed to send host name")

            self.console.print(f"\n[bold green]{self.client_name} has joined![/bold green]")
            time.sleep(1)

            # Select random questions
            self.battle_questions = random.sample(self.questions, min(num_questions, len(self.questions)))

            # Initialize state
            self.state = BattleState(
                question_num=0,
                total_questions=len(self.battle_questions),
                player1_score=0,
                player2_score=0,
                player1_name=self.player.username,
                player2_name=self.client_name
            )

            # Run battle
            return self.run_battle_as_host()

        except socket.timeout:
            self.console.print("[red]Timeout waiting for opponent.[/red]")
            return False
        except (ConnectionError, OSError, socket.error, ValueError) as e:
            logger.error(f"Battle host error: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            return False
        finally:
            self.cleanup()

    def run_battle_as_host(self) -> bool:
        """Run the battle as host."""
        for i, question in enumerate(self.battle_questions):
            self.state.question_num = i + 1
            # Don't send correct_answer to client - verify on host only
            self.state.current_question = {
                'id': question.id,
                'text': question.question_text,
                'options': question.options,
                'type': question.type.value,
                'command': question.command
                # NOTE: correct_answer NOT sent to client for security
            }

            # Send question to client (without answer)
            if not safe_send(self.client_socket, {
                'type': 'question',
                'data': self.state.current_question,
                'num': self.state.question_num,
                'total': self.state.total_questions,
                'scores': {
                    self.player.username: self.state.player1_score,
                    self.client_name: self.state.player2_score
                }
            }):
                logger.error("Failed to send question to client")
                return False

            # Show question and get answer
            my_result = self.show_battle_question(question, self.state.question_num, self.state.total_questions)

            # Send my result with correct answer (so client can verify/display)
            if not safe_send(self.client_socket, {
                'type': 'result',
                'data': asdict(my_result),
                'correct_answer': question.correct_answer[0]  # Send only after both answered
            }):
                logger.error("Failed to send result to client")
                return False

            # Receive opponent result
            opp_data = safe_recv(self.client_socket)
            if not opp_data:
                logger.error("No response from client")
                return False

            opp_result_data = safe_json_loads(opp_data)
            if not opp_result_data or 'data' not in opp_result_data:
                logger.error("Invalid result data from client")
                return False

            # Validate client's answer on server side
            client_answer = opp_result_data.get('answer', '')
            is_client_correct = question.is_correct(client_answer)

            # Validate time_taken - prevent cheating with impossibly fast or negative times
            client_time = opp_result_data['data'].get('time_taken', 0)
            if not isinstance(client_time, (int, float)) or client_time < 0.5:
                client_time = 60.0  # Penalize suspicious times
            client_time = min(client_time, 300.0)  # Cap at 5 minutes

            opp_result = BattleResult(
                player_name=self.client_name,
                is_correct=is_client_correct,
                time_taken=client_time,
                points=self.calculate_battle_points(is_client_correct, client_time)
            )

            # Update scores
            self.state.player1_score += my_result.points
            self.state.player2_score += opp_result.points

            # Show round result
            self.show_round_result(my_result, opp_result, question.correct_answer[0])

        # Battle complete
        self.state.game_over = True
        if self.state.player1_score > self.state.player2_score:
            self.state.winner = self.player.username
            self.player.battles_won += 1
        elif self.state.player2_score > self.state.player1_score:
            self.state.winner = self.client_name
            self.player.battles_lost += 1
        else:
            self.state.winner = "TIE"

        self.player.battles_played += 1

        # Send final state
        safe_send(self.client_socket, {
            'type': 'game_over',
            'winner': self.state.winner,
            'scores': {
                self.player.username: self.state.player1_score,
                self.client_name: self.state.player2_score
            }
        })

        self.show_battle_end()
        return True

    def show_battle_question(self, question: Question, num: int, total: int) -> BattleResult:
        """Show question and get player's answer."""
        clear_terminal()

        # Scoreboard
        scores = Table.grid(padding=(0, 4))
        scores.add_column(justify="center")
        scores.add_column(justify="center")
        scores.add_column(justify="center")
        scores.add_row(
            f"[bold]{self.player.username}[/bold]",
            "[dim]vs[/dim]",
            f"[bold]{self.client_name}[/bold]"
        )
        scores.add_row(
            f"[bold {Theme.PRIMARY}]{self.state.player1_score}[/bold {Theme.PRIMARY}]",
            "",
            f"[bold {Theme.ERROR}]{self.state.player2_score}[/bold {Theme.ERROR}]"
        )
        self.console.print(Panel(scores, title=f"[bold]Round {num}/{total}[/bold]", border_style=Theme.WARNING))

        # Question
        self.console.print(UIComponents.create_question_panel(question, num, total))

        start_time = time.time()
        answer = Prompt.ask("Your answer").strip()
        time_taken = time.time() - start_time

        # Normalize answer for validation
        user_answer = answer.lower()
        answer_to_validate = answer

        # Handle number answers for multiple choice - convert to letter index
        if question.options and len(user_answer) == 1 and user_answer in '1234':
            number_index = int(user_answer) - 1
            if 0 <= number_index < len(question.options):
                answer_to_validate = question.options[number_index]
        # Handle letter answers for multiple choice - expand to full option
        elif question.options and len(user_answer) == 1 and user_answer in 'abcd':
            letter_index = ord(user_answer) - ord('a')
            if 0 <= letter_index < len(question.options):
                answer_to_validate = question.options[letter_index]

        is_correct = question.is_correct(answer_to_validate)
        points = self.calculate_battle_points(is_correct, time_taken)

        return BattleResult(
            player_name=self.player.username,
            is_correct=is_correct,
            time_taken=time_taken,
            points=points
        )

    def calculate_battle_points(self, is_correct: bool, time_taken: float) -> int:
        """Calculate points for a battle answer."""
        if not is_correct:
            return 0

        base_points = 100
        # Speed bonus: up to 50 extra points for fast answers
        if time_taken < 5:
            speed_bonus = 50
        elif time_taken < 10:
            speed_bonus = 30
        elif time_taken < 20:
            speed_bonus = 10
        else:
            speed_bonus = 0

        return base_points + speed_bonus

    def show_round_result(self, my_result: BattleResult, opp_result: BattleResult, correct_answer: str):
        """Show the result of a round."""
        self.console.print("\n")

        # My result
        if my_result.is_correct:
            self.console.print(f"[bold {Theme.SUCCESS}]You: ✓ Correct! +{my_result.points} pts ({my_result.time_taken:.1f}s)[/bold {Theme.SUCCESS}]")
        else:
            self.console.print(f"[bold {Theme.ERROR}]You: ✗ Wrong![/bold {Theme.ERROR}]")

        # Opponent result
        if opp_result.is_correct:
            self.console.print(f"[bold {Theme.WARNING}]{opp_result.player_name}: ✓ Correct! +{opp_result.points} pts ({opp_result.time_taken:.1f}s)[/bold {Theme.WARNING}]")
        else:
            self.console.print(f"[dim]{opp_result.player_name}: ✗ Wrong![/dim]")

        self.console.print(f"\n[dim]Correct answer: {correct_answer}[/dim]")

        if not my_result.is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)

    def show_battle_end(self):
        """Show battle end screen."""
        clear_terminal()

        if self.state.winner == self.player.username:
            result_text = ("🏆 VICTORY! 🏆", f"bold {Theme.SUCCESS}")
        elif self.state.winner == "TIE":
            result_text = ("🤝 IT'S A TIE! 🤝", f"bold {Theme.WARNING}")
        else:
            result_text = ("💀 DEFEAT 💀", f"bold {Theme.ERROR}")

        panel = Panel(
            Align.center(Text.assemble(
                (f"\n{result_text[0]}\n\n", result_text[1]),
                (f"{self.player.username}: ", "white"),
                (f"{self.state.player1_score} pts\n", f"bold {Theme.PRIMARY}"),
                (f"{self.client_name}: ", "white"),
                (f"{self.state.player2_score} pts\n", f"bold {Theme.ERROR}"),
            )),
            title="[bold]⚔️ BATTLE COMPLETE ⚔️[/bold]",
            border_style=Theme.WARNING,
            padding=(1, 2)
        )

        self.console.print(panel)
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()

    def cleanup(self):
        """Clean up sockets with proper shutdown."""
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except (socket.error, OSError):
                pass  # Socket might already be closed
            try:
                self.client_socket.close()
            except (socket.error, OSError):
                pass
            self.client_socket = None

        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except (socket.error, OSError):
                pass
            try:
                self.server_socket.close()
            except (socket.error, OSError):
                pass
            self.server_socket = None

        logger.info("Battle server sockets cleaned up")


class BattleClient:
    """Client for joining a battle."""

    def __init__(self, console: Console, player: PlayerStats):
        self.console = console
        self.player = player
        self.socket: Optional[socket.socket] = None
        self.host_name: str = ""
        self.state: Optional[BattleState] = None

    def join_game(self, host_ip: str, port: int = DEFAULT_PORT) -> bool:
        """Join a battle game."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)

            # Validate IP/hostname format
            # IPv4: digits and dots only, max 15 chars (xxx.xxx.xxx.xxx)
            # Hostname: alphanumeric, dots, hyphens, max 253 chars
            host_ip = host_ip.strip()
            if len(host_ip) > 253:
                raise ValueError("Host address too long")
            is_ipv4 = re.match(r'^(\d{1,3}\.){3}\d{1,3}$', host_ip)
            is_hostname = re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$', host_ip)
            if not is_ipv4 and not is_hostname:
                raise ValueError("Invalid host IP or hostname format")

            self.console.print(f"\n[dim]Connecting to {host_ip}:{port}...[/dim]")

            self.socket.connect((host_ip, port))
            logger.info(f"Connected to battle host at {host_ip}:{port}")

            # Send my name (sanitized)
            if not safe_send(self.socket, {'name': sanitize_name(self.player.username)}):
                raise ConnectionError("Failed to send player name")

            # Receive host name
            data = safe_recv(self.socket, timeout=30)
            if not data:
                raise ConnectionError("No response from host")

            host_info = safe_json_loads(data)
            if not host_info or 'name' not in host_info:
                raise ValueError("Invalid host handshake")

            self.host_name = sanitize_name(host_info['name'])

            self.console.print(f"\n[bold green]Connected to {self.host_name}![/bold green]")
            time.sleep(1)

            # Initialize state
            self.state = BattleState(
                question_num=0,
                total_questions=0,
                player1_score=0,
                player2_score=0,
                player1_name=self.host_name,
                player2_name=self.player.username
            )

            # Run battle
            return self.run_battle_as_client()

        except socket.timeout:
            self.console.print("[red]Connection timed out.[/red]")
            return False
        except ConnectionRefusedError:
            self.console.print("[red]Connection refused. Is the host running?[/red]")
            return False
        except (ConnectionError, OSError, socket.error, ValueError) as e:
            logger.error(f"Battle client error: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
            return False
        finally:
            self.cleanup()

    def run_battle_as_client(self) -> bool:
        """Run the battle as client."""
        while True:
            data = safe_recv(self.socket)
            if not data:
                logger.warning("Connection lost to host")
                break

            message = safe_json_loads(data)
            if not message:
                logger.error("Invalid message from host")
                continue

            if message['type'] == 'question':
                # Update state
                self.state.question_num = message['num']
                self.state.total_questions = message['total']
                self.state.player1_score = message['scores'].get(self.host_name, 0)
                self.state.player2_score = message['scores'].get(self.player.username, 0)

                # Show question and get answer (returns result AND raw answer)
                question_data = message['data']
                my_result, raw_answer = self.show_battle_question(question_data, message['num'], message['total'])

                # Receive host result first (contains correct answer now)
                host_result_data = safe_recv(self.socket)
                if not host_result_data:
                    logger.error("No result from host")
                    break

                host_result_msg = safe_json_loads(host_result_data)
                if not host_result_msg or 'data' not in host_result_msg:
                    logger.error("Invalid result from host")
                    break

                host_result = BattleResult(**host_result_msg['data'])
                correct_answer = host_result_msg.get('correct_answer', '')

                # Send my result WITH raw answer for server-side validation
                if not safe_send(self.socket, {
                    'type': 'result',
                    'data': asdict(my_result),
                    'answer': raw_answer  # Server will validate this
                }):
                    logger.error("Failed to send result")
                    break

                # Show round result (server validated, we use their correct_answer)
                self.show_round_result(my_result, host_result, correct_answer)

            elif message['type'] == 'game_over':
                self.state.winner = message.get('winner', '')
                self.state.player1_score = message['scores'].get(self.host_name, 0)
                self.state.player2_score = message['scores'].get(self.player.username, 0)

                if self.state.winner == self.player.username:
                    self.player.battles_won += 1
                elif self.state.winner != "TIE":
                    self.player.battles_lost += 1

                self.player.battles_played += 1

                self.show_battle_end()
                break

        return True

    def show_battle_question(self, question_data: dict, num: int, total: int) -> Tuple[BattleResult, str]:
        """Show question and get player's answer. Returns (result, raw_answer)."""
        clear_terminal()

        # Scoreboard
        scores = Table.grid(padding=(0, 4))
        scores.add_column(justify="center")
        scores.add_column(justify="center")
        scores.add_column(justify="center")
        scores.add_row(
            f"[bold]{self.host_name}[/bold]",
            "[dim]vs[/dim]",
            f"[bold]{self.player.username}[/bold]"
        )
        scores.add_row(
            f"[bold {Theme.ERROR}]{self.state.player1_score}[/bold {Theme.ERROR}]",
            "",
            f"[bold {Theme.PRIMARY}]{self.state.player2_score}[/bold {Theme.PRIMARY}]"
        )
        self.console.print(Panel(scores, title=f"[bold]Round {num}/{total}[/bold]", border_style=Theme.WARNING))

        # Question panel
        q_text = Text()
        q_text.append(f"\n{question_data['text']}\n\n", style="bold white")

        if question_data.get('options'):
            for i, option in enumerate(question_data['options']):
                letter = chr(65 + i)
                q_text.append(f"  {letter}) ", style=Theme.PRIMARY)
                q_text.append(f"{option}\n", style="white")

        self.console.print(Panel(q_text, title=f"[bold]Question {num}[/bold]", border_style=Theme.PANEL_BORDER_STYLE))

        start_time = time.time()
        answer = Prompt.ask("Your answer").strip()
        time_taken = time.time() - start_time

        # Normalize answer for sending to server
        user_answer = answer.lower()
        answer_to_send = answer  # Raw answer to send for server validation

        # Handle number answers for multiple choice - convert to option text
        if question_data.get('options') and len(user_answer) == 1 and user_answer in '1234':
            number_index = int(user_answer) - 1
            if 0 <= number_index < len(question_data['options']):
                answer_to_send = question_data['options'][number_index]
        # Handle letter answers for multiple choice - expand to full option
        elif question_data.get('options') and len(user_answer) == 1 and user_answer in 'abcd':
            letter_index = ord(user_answer) - ord('a')
            if 0 <= letter_index < len(question_data['options']):
                answer_to_send = question_data['options'][letter_index]

        # Client doesn't validate - just marks as pending (server will validate)
        # This is a local estimate only, server has authoritative answer
        points = 0  # Will be determined by server

        result = BattleResult(
            player_name=self.player.username,
            is_correct=False,  # Server will determine this
            time_taken=time_taken,
            points=points
        )

        return result, answer_to_send

    def calculate_battle_points(self, is_correct: bool, time_taken: float) -> int:
        """Calculate points for a battle answer."""
        if not is_correct:
            return 0

        base_points = 100
        if time_taken < 5:
            speed_bonus = 50
        elif time_taken < 10:
            speed_bonus = 30
        elif time_taken < 20:
            speed_bonus = 10
        else:
            speed_bonus = 0

        return base_points + speed_bonus

    def show_round_result(self, my_result: BattleResult, opp_result: BattleResult, correct_answer: str):
        """Show the result of a round."""
        self.console.print("\n")

        if my_result.is_correct:
            self.console.print(f"[bold {Theme.SUCCESS}]You: ✓ Correct! +{my_result.points} pts ({my_result.time_taken:.1f}s)[/bold {Theme.SUCCESS}]")
        else:
            self.console.print(f"[bold {Theme.ERROR}]You: ✗ Wrong![/bold {Theme.ERROR}]")

        if opp_result.is_correct:
            self.console.print(f"[bold {Theme.WARNING}]{opp_result.player_name}: ✓ Correct! +{opp_result.points} pts ({opp_result.time_taken:.1f}s)[/bold {Theme.WARNING}]")
        else:
            self.console.print(f"[dim]{opp_result.player_name}: ✗ Wrong![/dim]")

        self.console.print(f"\n[dim]Correct answer: {correct_answer}[/dim]")

        if not my_result.is_correct:
            self.console.print("\n[dim]Press ENTER to continue...[/dim]")
            input()
        else:
            time.sleep(1.5)

    def show_battle_end(self):
        """Show battle end screen."""
        clear_terminal()

        if self.state.winner == self.player.username:
            result_text = ("🏆 VICTORY! 🏆", f"bold {Theme.SUCCESS}")
        elif self.state.winner == "TIE":
            result_text = ("🤝 IT'S A TIE! 🤝", f"bold {Theme.WARNING}")
        else:
            result_text = ("💀 DEFEAT 💀", f"bold {Theme.ERROR}")

        panel = Panel(
            Align.center(Text.assemble(
                (f"\n{result_text[0]}\n\n", result_text[1]),
                (f"{self.host_name}: ", "white"),
                (f"{self.state.player1_score} pts\n", f"bold {Theme.ERROR}"),
                (f"{self.player.username}: ", "white"),
                (f"{self.state.player2_score} pts\n", f"bold {Theme.PRIMARY}"),
            )),
            title="[bold]⚔️ BATTLE COMPLETE ⚔️[/bold]",
            border_style=Theme.WARNING,
            padding=(1, 2)
        )

        self.console.print(panel)
        self.console.print("\n[dim]Press ENTER to continue...[/dim]")
        input()

    def cleanup(self):
        """Clean up socket with proper shutdown."""
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except (socket.error, OSError):
                pass  # Socket might already be closed
            try:
                self.socket.close()
            except (socket.error, OSError):
                pass
            self.socket = None

        logger.info("Battle client socket cleaned up")
