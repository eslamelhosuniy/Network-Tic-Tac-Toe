import logging
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "game.log")

def _make_logger(name="game", path=LOG_PATH, max_bytes=5 * 1024 * 1024, backups=5):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backups, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

class GameLogger:
    def __init__(self, logger=None):
        self._log = logger or _make_logger()

    def _record(self, level, event_type, player=None, details=None, **meta):
        entry = {
            "time": datetime.utcnow().isoformat() + "Z",
            "event": event_type,
            "player": player,
            "details": details,
            "meta": meta
        }
        self._log.log(level, json.dumps(entry, ensure_ascii=False))

    def info(self, event_type, player=None, details=None, **meta):
        self._record(logging.INFO, event_type, player, details, **meta)

    def warning(self, event_type, player=None, details=None, **meta):
        self._record(logging.WARNING, event_type, player, details, **meta)

    def error(self, event_type, player=None, details=None, **meta):
        self._record(logging.ERROR, event_type, player, details, **meta)

    # تسجيل حركة TicTacToe
    def tictactoe_move(self, player_symbol, move_position, player_addr=None):
        details = f"Player {player_symbol} chose cell {move_position}"
        self.info("tictactoe_move", player=player_addr, details=details)

    # تسجيل الفائز أو التعادل
    def tictactoe_winner(self, winner_symbol=None, winner_addr=None):
        if winner_symbol is None:
            details = "Game ended in a draw"
            self.info("tictactoe_result", player=None, details=details)
        else:
            details = f"Player {winner_symbol} won the game"
            self.info("tictactoe_result", player=winner_addr, details=details)

    # تسجيل QUIT
    def player_quit(self, player_symbol, player_addr=None):
        details = f"Player {player_symbol} quit the game"
        self.info("player_quit", player=player_addr, details=details)

logger = GameLogger()
logger.info("game_start", details="Game server started")
