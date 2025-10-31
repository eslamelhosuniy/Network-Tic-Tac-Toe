from server_logger import logger

class ServerError(Exception):
    pass

class PlayerDisconnectedError(ServerError):
    def __init__(self, player_addr, message="Player disconnected"):
        self.player_addr = player_addr
        super().__init__(f"{message}: {player_addr}")
        logger.warning("player_disconnected", player=player_addr, details=message)

class PlayerQuitError(ServerError):
    def __init__(self, player_addr, message="Player quit"):
        self.player_addr = player_addr
        super().__init__(f"{message}: {player_addr}")
        logger.info("player_quit", player=player_addr, details=message)

class InvalidMessageError(ServerError):
    def __init__(self, player_addr, message="Invalid message"):
        self.player_addr = player_addr
        super().__init__(f"{message}: {player_addr}")
        logger.warning("invalid_message", player=player_addr, details=message)

class TimeoutWaitingPlayerError(ServerError):
    def __init__(self, player_addr, message="Timeout waiting for player"):
        self.player_addr = player_addr
        super().__init__(f"{message}: {player_addr}")
        logger.warning("timeout_waiting_player", player=player_addr, details=message)
