"""
Enumerations for game states and card properties.
Aligned with functional requirements: Host-Authoritative, Custom Rules, Stacking.
"""

from enum import Enum


class CardColor(Enum):
    """Card color enumeration."""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    WILD = "wild"


class CardValue(Enum):
    """Card value/rank enumeration."""
    ZERO = "0"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    SKIP = "skip"
    REVERSE = "reverse"
    DRAW_TWO = "draw_two"
    WILD = "wild"
    WILD_DRAW_FOUR = "wild_draw_four"


class CardAction(Enum):
    """Card action type for rule enforcement."""
    NUMBER = "number"
    SKIP = "skip"
    REVERSE = "reverse"
    DRAW_TWO = "draw_two"
    WILD = "wild"
    WILD_DRAW_FOUR = "wild_draw_four"


class GameState(Enum):
    """Game state enumeration."""
    LOBBY = "lobby"
    WAITING = "waiting"
    PLAYING = "playing"
    REACTION_EVENT = "reaction_event"  # Rule 8: Eights reaction event
    PAUSED = "paused"
    GAME_OVER = "game_over"


class PlayerState(Enum):
    """Player state enumeration."""
    IDLE = "idle"
    TURN = "turn"
    WAITING = "waiting"
    RESPONDING_REACTION = "responding_reaction"  # Rule 8: waiting to respond to Eight
    DISCONNECTED = "disconnected"
    PENALTY_DRAW = "penalty_draw"  # Drawing penalty cards


class TurnDirection(Enum):
    """Turn order direction (affected by Reverse cards)."""
    FORWARD = "forward"
    REVERSE = "reverse"


class ReactionEventState(Enum):
    """State of a Rule 8 reaction event (Eight card played)."""
    PENDING = "pending"  # Event started, waiting for responses
    RESOLVED = "resolved"  # All responses collected or timeout
    COMPLETED = "completed"  # Penalties applied


class StackingState(Enum):
    """State of draw card stacking."""
    NONE = "none"  # No stacking active
    STACKING = "stacking"  # +2 or +4 on top of each other
    RESOLVED = "resolved"  # Player must draw accumulated cards


class MessageType(Enum):
    """Network message type enumeration - all possible messages between Client and Server."""
    # Client-to-Server messages
    JOIN_ROOM = "join_room"  # Client joins a room
    START_GAME = "start_game"  # Host starts the game
    PLAY_CARD = "play_card"  # Client plays a card
    DRAW_CARD = "draw_card"  # Client draws a card
    RULE_8_REACTION = "rule_8_reaction"  # Client responds to Rule 8 reaction event

    # Server-to-Client messages
    GAME_STATE_UPDATE = "game_state_update"  # Server broadcasts complete game state
    EVENT_BROADCAST = "event_broadcast"  # Server broadcasts UI events
    ERROR_MESSAGE = "error_message"  # Server rejects invalid client action

    # Legacy/deprecated (keeping for compatibility)
    HANDSHAKE = "handshake"
    ACTION = "action"
    STATE_UPDATE = "state_update"
    GAME_START = "game_start"
    GAME_END = "game_end"
    ERROR = "error"
    DISCONNECT = "disconnect"
    REACTION_EVENT = "reaction_event"
    REACTION_RESPONSE = "reaction_response"
    RULE_EFFECT = "rule_effect"
    STACKING_UPDATE = "stacking_update"
