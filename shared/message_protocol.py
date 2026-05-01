"""
Message protocol definitions for Client-Server communication.
API Contract between Dumb Client and Authoritative Server.
All communication via JSON over TCP sockets.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, List
from shared.enums import MessageType, CardColor, TurnDirection


@dataclass
class NetworkMessage:
    """Base network message structure."""
    message_type: MessageType
    sender_id: Optional[int] = None
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        data = asdict(self)
        data['message_type'] = self.message_type.value  # Convert enum to string
        return data

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NetworkMessage':
        """Create message from dictionary (JSON deserialization)."""
        # Convert string back to enum
        if 'message_type' in data:
            data['message_type'] = MessageType(data['message_type'])
        return NetworkMessage(**data)

    @staticmethod
    def from_json(json_str: str) -> 'NetworkMessage':
        """Deserialize message from JSON string."""
        return NetworkMessage.from_dict(json.loads(json_str))


# =============================================================================
# CLIENT-TO-SERVER MESSAGES (Actions)
# =============================================================================

@dataclass
class JoinRoomMessage(NetworkMessage):
    """
    Client joins a room.
    Sent when player wants to join a game room.
    """
    player_name: str = ""
    room_code: Optional[str] = None  # Optional room code for joining specific room

    def __post_init__(self):
        self.message_type = MessageType.JOIN_ROOM


@dataclass
class StartGameMessage(NetworkMessage):
    """
    Host starts the game.
    Only the host can send this message.
    """
    room_id: str = ""

    def __post_init__(self):
        self.message_type = MessageType.START_GAME


@dataclass
class PlayCardMessage(NetworkMessage):
    """
    Client plays a card.
    Must include the card played and optional fields for custom rules.
    """
    card_index: int  # Index of card in player's hand
    chosen_color: Optional[CardColor] = None  # For Wild/Wild Draw Four cards
    target_player_id: Optional[int] = None  # For Rule 7 (hand swap)
    chosen_direction: Optional[str] = None  # For Rule 0 ("forward" or "reverse")

    def __post_init__(self):
        self.message_type = MessageType.PLAY_CARD


@dataclass
class DrawCardMessage(NetworkMessage):
    """
    Client draws a card.
    Sent when player chooses to draw instead of playing.
    """
    def __post_init__(self):
        self.message_type = MessageType.DRAW_CARD


@dataclass
class Rule8ReactionMessage(NetworkMessage):
    """
    Client responds to Rule 8 reaction event.
    Sent when player clicks the reaction button during Eight card event.
    """
    def __post_init__(self):
        self.message_type = MessageType.RULE_8_REACTION


# =============================================================================
# SERVER-TO-CLIENT MESSAGES (State & Broadcasts)
# =============================================================================

@dataclass
class GameStateUpdateMessage(NetworkMessage):
    """
    Server broadcasts complete game state to all clients.
    This is the authoritative source of truth for all clients.
    Contains massive state payload for UI rendering.
    """
    # Core game state
    current_player_id: Optional[int] = None  # Whose turn it is
    turn_direction: TurnDirection = TurnDirection.FORWARD  # Forward or reverse
    top_discard_card: Optional[Dict[str, Any]] = None  # Last played card

    # Client-specific data
    your_hand: List[Dict[str, Any]] = field(default_factory=list)  # This client's cards
    opponents_card_counts: Dict[int, int] = field(default_factory=dict)  # {player_id: card_count}

    # Pending effects (for UI display)
    active_stacking_penalty: int = 0  # Current +2/+4 accumulation
    is_reaction_event_active: bool = False  # Rule 8 event in progress
    reaction_event_time_remaining: float = 0.0  # Seconds left for Rule 8

    # Game metadata
    game_phase: str = "lobby"  # "lobby", "playing", "game_over", etc.
    winner_id: Optional[int] = None  # If game is over

    def __post_init__(self):
        self.message_type = MessageType.GAME_STATE_UPDATE


@dataclass
class EventBroadcastMessage(NetworkMessage):
    """
    Server broadcasts UI events to all clients.
    Triggers specific UI changes or notifications.
    """
    event_type: str = ""  # Event identifier
    event_data: Dict[str, Any] = field(default_factory=dict)  # Event-specific data

    def __post_init__(self):
        self.message_type = MessageType.EVENT_BROADCAST

    @property
    def is_rule_8_started(self) -> bool:
        """Check if this is a Rule 8 reaction event start."""
        return self.event_type == "RULE_8_STARTED"

    @property
    def is_player_uno(self) -> bool:
        """Check if this is a player UNO announcement."""
        return self.event_type == "PLAYER_UNO"

    @property
    def is_game_over(self) -> bool:
        """Check if this is a game over event."""
        return self.event_type == "GAME_OVER"


@dataclass
class ErrorMessage(NetworkMessage):
    """
    Server rejects an invalid client action.
    Sent to specific client who made the invalid move.
    """
    error_code: str = ""  # Error identifier
    error_description: str = ""  # Human-readable error message
    action_attempted: Optional[str] = None  # What the client tried to do

    def __post_init__(self):
        self.message_type = MessageType.ERROR_MESSAGE

    @property
    def is_illegal_card(self) -> bool:
        """Check if error is due to illegal card play."""
        return self.error_code == "ILLEGAL_CARD"

    @property
    def is_wrong_turn(self) -> bool:
        """Check if error is due to wrong player turn."""
        return self.error_code == "WRONG_TURN"

    @property
    def is_cannot_win_with_action(self) -> bool:
        """Check if error is due to trying to win with action card."""
        return self.error_code == "CANNOT_WIN_WITH_ACTION"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_join_room_message(player_name: str, room_code: Optional[str] = None) -> JoinRoomMessage:
    """Factory function to create a join room message."""
    return JoinRoomMessage(player_name=player_name, room_code=room_code)


def create_start_game_message(room_id: str, host_id: int) -> StartGameMessage:
    """Factory function to create a start game message."""
    return StartGameMessage(room_id=room_id, sender_id=host_id)


def create_play_card_message(player_id: int, card_index: int,
                           chosen_color: Optional[CardColor] = None,
                           target_player_id: Optional[int] = None,
                           chosen_direction: Optional[str] = None) -> PlayCardMessage:
    """Factory function to create a play card message."""
    return PlayCardMessage(
        sender_id=player_id,
        card_index=card_index,
        chosen_color=chosen_color,
        target_player_id=target_player_id,
        chosen_direction=chosen_direction
    )


def create_draw_card_message(player_id: int) -> DrawCardMessage:
    """Factory function to create a draw card message."""
    return DrawCardMessage(sender_id=player_id)


def create_rule_8_reaction_message(player_id: int) -> Rule8ReactionMessage:
    """Factory function to create a Rule 8 reaction message."""
    return Rule8ReactionMessage(sender_id=player_id)


def create_game_state_update(current_player_id: Optional[int] = None,
                           turn_direction: TurnDirection = TurnDirection.FORWARD,
                           top_discard_card: Optional[Dict[str, Any]] = None,
                           your_hand: Optional[List[Dict[str, Any]]] = None,
                           opponents_card_counts: Optional[Dict[int, int]] = None,
                           active_stacking_penalty: int = 0,
                           is_reaction_event_active: bool = False,
                           reaction_event_time_remaining: float = 0.0,
                           game_phase: str = "playing",
                           winner_id: Optional[int] = None) -> GameStateUpdateMessage:
    """Factory function to create a game state update message."""
    return GameStateUpdateMessage(
        current_player_id=current_player_id,
        turn_direction=turn_direction,
        top_discard_card=top_discard_card,
        your_hand=your_hand or [],
        opponents_card_counts=opponents_card_counts or {},
        active_stacking_penalty=active_stacking_penalty,
        is_reaction_event_active=is_reaction_event_active,
        reaction_event_time_remaining=reaction_event_time_remaining,
        game_phase=game_phase,
        winner_id=winner_id
    )


def create_event_broadcast(event_type: str, event_data: Optional[Dict[str, Any]] = None) -> EventBroadcastMessage:
    """Factory function to create an event broadcast message."""
    return EventBroadcastMessage(event_type=event_type, event_data=event_data or {})


def create_error_message(error_code: str, error_description: str,
                        recipient_id: int, action_attempted: Optional[str] = None) -> ErrorMessage:
    """Factory function to create an error message."""
    return ErrorMessage(
        sender_id=recipient_id,
        error_code=error_code,
        error_description=error_description,
        action_attempted=action_attempted
    )


# =============================================================================
# MESSAGE PARSING UTILITIES
# =============================================================================

def parse_incoming_message(json_str: str) -> NetworkMessage:
    """
    Parse an incoming JSON message and return the appropriate message object.
    This is the main entry point for deserializing network messages.
    """
    try:
        data = json.loads(json_str)
        message_type = MessageType(data.get('message_type'))

        # Route to appropriate message class based on type
        if message_type == MessageType.JOIN_ROOM:
            return JoinRoomMessage.from_dict(data)
        elif message_type == MessageType.START_GAME:
            return StartGameMessage.from_dict(data)
        elif message_type == MessageType.PLAY_CARD:
            return PlayCardMessage.from_dict(data)
        elif message_type == MessageType.DRAW_CARD:
            return DrawCardMessage.from_dict(data)
        elif message_type == MessageType.RULE_8_REACTION:
            return Rule8ReactionMessage.from_dict(data)
        elif message_type == MessageType.GAME_STATE_UPDATE:
            return GameStateUpdateMessage.from_dict(data)
        elif message_type == MessageType.EVENT_BROADCAST:
            return EventBroadcastMessage.from_dict(data)
        elif message_type == MessageType.ERROR_MESSAGE:
            return ErrorMessage.from_dict(data)
        else:
            # Fallback to base message for unknown types
            return NetworkMessage.from_dict(data)

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        raise ValueError(f"Invalid message format: {e}")


# Add from_dict methods to all message classes
def _add_from_dict_method(cls):
    """Add from_dict class method to a message class."""
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        # Convert string back to enum
        if 'message_type' in data:
            data['message_type'] = MessageType(data['message_type'])
        if 'chosen_color' in data and data['chosen_color'] is not None:
            data['chosen_color'] = CardColor(data['chosen_color'])
        if 'turn_direction' in data and data['turn_direction'] is not None:
            data['turn_direction'] = TurnDirection(data['turn_direction'])
        return cls(**data)
    cls.from_dict = from_dict
    return cls

# Apply from_dict methods to all message classes
JoinRoomMessage = _add_from_dict_method(JoinRoomMessage)
StartGameMessage = _add_from_dict_method(StartGameMessage)
PlayCardMessage = _add_from_dict_method(PlayCardMessage)
DrawCardMessage = _add_from_dict_method(DrawCardMessage)
Rule8ReactionMessage = _add_from_dict_method(Rule8ReactionMessage)
GameStateUpdateMessage = _add_from_dict_method(GameStateUpdateMessage)
EventBroadcastMessage = _add_from_dict_method(EventBroadcastMessage)
ErrorMessage = _add_from_dict_method(ErrorMessage)
