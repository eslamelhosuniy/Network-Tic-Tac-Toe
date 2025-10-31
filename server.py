import socket
import threading
import traceback
from logic import TicTacToe
from logicExceptions import (
    InvalidMoveError, OutOfRangeError, CellOccupiedError,
    NotYourTurnError, GameOverError, PlayerNotRecognizedError
)
from serverExceptions import (
    PlayerDisconnectedError, PlayerQuitError,
    InvalidMessageError, TimeoutWaitingPlayerError
)
from server_logger import logger

HOST = "127.0.0.1"
PORT = 5000
BUFFER = 1024
MOVE_TIMEOUT_SECONDS = 30

clients_waiting = []
lock = threading.Lock()

def safe_send(sock, text):
    try:
        if not isinstance(text, str):
            text = str(text)
        sock.sendall(text.encode())
    except Exception as e:
        try: addr = sock.getpeername()
        except Exception: addr = ("unknown", 0)
        raise PlayerDisconnectedError(addr, f"send failed: {e}")

def recv_with_timeout(sock, timeout_seconds):
    try:
        sock.settimeout(timeout_seconds)
        data = sock.recv(BUFFER)
        if not data:
            try: addr = sock.getpeername()
            except Exception: addr = ("unknown", 0)
            raise PlayerDisconnectedError(addr, "client closed connection")
        return data.decode().strip()
    except socket.timeout:
        try: addr = sock.getpeername()
        except Exception: addr = ("unknown", 0)
        raise TimeoutWaitingPlayerError(addr, f"Timed out after {timeout_seconds} seconds")
    except PlayerDisconnectedError: raise
    except Exception as e:
        try: addr = sock.getpeername()
        except Exception: addr = ("unknown", 0)
        raise PlayerDisconnectedError(addr, f"recv failed: {e}")
    finally:
        try: sock.settimeout(None)
        except Exception: pass

def handle_game(p1, p2):
    game = TicTacToe(p1, p2)
    try:
        safe_send(p1, f"Game start! You are {game.symbols[p1]}\n")
        safe_send(p2, f"Game start! You are {game.symbols[p2]}\n")
    except PlayerDisconnectedError as e:
        try: p1.close(); p2.close()
        except: pass
        return

    while True:
        try:
            board_text = game.print_board()
            for s in (p1, p2):
                safe_send(s, board_text + "\n")

            current = game.turn
            other = p2 if current == p1 else p1

            safe_send(current, "Your move (0-8) or QUIT:\n")
            safe_send(other, "Waiting for opponent...\n")

            move_text = recv_with_timeout(current, MOVE_TIMEOUT_SECONDS)

            if move_text.upper() == "QUIT":
                current_symbol = game.symbols[current]
                logger.player_quit(current_symbol, current.getpeername())
                raise PlayerQuitError(current.getpeername(), "Player quit")

            if move_text.upper().startswith("MOVE "):
                parts = move_text.split()
                if len(parts) != 2 or not parts[1].isdigit():
                    raise InvalidMessageError(current.getpeername(), f"Malformed MOVE: {move_text}")
                move_arg = parts[1]
            elif move_text.isdigit():
                move_arg = move_text
            else:
                safe_send(current, f"Invalid move format: {move_text}\n")
                continue

            try:
                game.make_move(current, move_arg)
                current_symbol = game.symbols[current]
                logger.tictactoe_move(current_symbol, move_arg, current.getpeername())
            except (InvalidMoveError, OutOfRangeError, CellOccupiedError, NotYourTurnError) as e:
                logger.warning(type(e).__name__, player=current.getpeername(), details=str(e))
                safe_send(current, f"ERROR: {type(e).__name__}: {e}\n")
                continue
            except PlayerNotRecognizedError as e:
                logger.warning("PlayerNotRecognizedError", player=current.getpeername(), details=str(e))
                safe_send(current, f"ERROR: Player not recognized: {e}\n")
                break
            except GameOverError:
                break

            if getattr(game, "winner", None):
                winner = game.winner
                if winner == "Draw":
                    for s in (p1, p2):
                        safe_send(s, "Game over! It's a draw.\n")
                    logger.tictactoe_winner()
                else:
                    for s in (p1, p2):
                        try:
                            sym = game.symbols[s]
                            if sym == winner: safe_send(s, "You win!\n")
                            else: safe_send(s, "You lose!\n")
                        except Exception: pass
                    winner_addr = p1.getpeername() if game.symbols[p1] == winner else p2.getpeername()
                    logger.tictactoe_winner(winner, winner_addr)
                break

        except (TimeoutWaitingPlayerError, PlayerQuitError, PlayerDisconnectedError) as e:
            try:
                remaining = p2 if e.player_addr == p1.getpeername() else p1
                safe_send(remaining, "OPPONENT_LEFT - you win\n")
                remaining_symbol = game.symbols[remaining]
                logger.tictactoe_winner(remaining_symbol, remaining.getpeername())
            except Exception: pass
            break

        except InvalidMessageError as e:
            try: safe_send(current, f"INVALID_MESSAGE: {e}\n")
            except Exception: pass
            continue
        except Exception as e:
            logger.error("UnexpectedServerError", player=None, details=str(e))
            traceback.print_exc()
            break

    for s in (p1, p2):
        try:
            s.close()
        except Exception:
            pass

    print("Game session ended.")


def client_thread(conn, addr):
    print(f"Connected by {addr}")
    try:
        conn.send("Welcome! Waiting for opponent...\n".encode())
    except Exception:
        conn.close()
        return

    with lock:
        clients_waiting.append(conn)
        if len(clients_waiting) >= 2:
            p1 = clients_waiting.pop(0)
            p2 = clients_waiting.pop(0)
            threading.Thread(target=handle_game, args=(p1, p2), daemon=True).start()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server running on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
