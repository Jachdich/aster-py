from enum import Enum, auto

class ConnectionMode(Enum):
    """How to authenticate with the aster server."""
    LOGIN = auto()
    REGISTER = auto()
    NEITHER = auto()
