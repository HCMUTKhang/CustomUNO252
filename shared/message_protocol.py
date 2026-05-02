"""
Message protocol definitions for Client-Server communication.
API Contract between Dumb Client and Authoritative Server.
All communication via JSON over TCP sockets.
Standardized DTOs with to_dict()/from_dict() for socket transmission.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, List
from shared.enums import MessageType, CardColor, CardValue, TurnDirection


@dataclass
class CardDTO:
    """Standardized representation of a Card in network messages."""
    color: CardColor
    value: CardValue

    def to_dict(self) -> dict:
        return {"color": self.color.value, "value": self.value.value}

    @classmethod
    def from_dict(cls, data: dict) -> "CardDTO":
        return cls(color=CardColor(data["color"]), value=CardValue(data["value"]))


@dataclass
class NetworkMessage:
    """Base network message structure."""
    message_type: MessageType

    def to_dict(self) -> dict:
        """Convert message to dictionary for JSON serialization."""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return json.dumps(self.to_dict())


# =============================================================================
# CLIENT-TO-SERVER MESSAGES (Actions)
# =============================================================================

@dataclass
class JoinRoom(NetworkMessage):
    """
    Client joins a room.
    Sent when player wants to join a game room.
    """
    username: str
    player_id: Optional[int] = None  # Filled by server upon connection

    def __init__(self, username: str, player_id: Optional[int] = None):
        self.message_type = MessageType.JOIN_ROOM
        self.username = username
        self.player_id = player_id


@dataclass
class StartGame(NetworkMessage):
    """
    Host starts the game.
    Only the host can send this message.
    """
    def __init__(self):
        self.message_type = MessageType.START_GAME


@dataclass
class PlayCard(NetworkMessage):
    """
    Client plays a card.
    Must include the card played and optional fields for custom rules.
    """
    card: CardDTO
    chosen_color: Optional[CardColor] = None  # Required if playing Wild/+4
    target_player_id: Optional[int] = None  # Required if playing Rule 7 (hand swap)
    chosen_direction: Optional[TurnDirection] = None  # Required if playing Rule 0

    def __init__(self, card: CardDTO, chosen_color: Optional[CardColor] = None,
                 target_player_id: Optional[int] = None, 
                 chosen_direction: Optional[TurnDirection] = None):
        self.message_type = MessageType.PLAY_CARD
        self.card = card
        self.chosen_color = chosen_color
        self.target_player_id = target_player_id
        self.chosen_direction = chosen_direction

    def to_dict(self) -> dict:
        """Convert to dict with proper enum serialization."""
        data = super().to_dict()
        data['card'] = self.card.to_dict()
        if self.chosen_color:
            data['chosen_color'] = self.chosen_color.value
        if self.chosen_direction:
            data['chosen_direction'] = self.chosen_direction.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PlayCard":
        """Create from dict with proper enum deserialization."""
        return cls(
            card=CardDTO.from_dict(data['card']),
            chosen_color=CardColor(data['chosen_color']) if data.get('chosen_color') else None,
            target_player_id=data.get('target_player_id'),
            chosen_direction=TurnDirection(data['chosen_direction']) if data.get('chosen_direction') else None
        )


@dataclass
class DrawCard(NetworkMessage):
    """
    Client draws a card.
    Sent when player chooses to draw instead of playing.
    """
    def __init__(self):
        self.message_type = MessageType.DRAW_CARD


@dataclass
class Rule8Reaction(NetworkMessage):
    """
    Client responds to Rule 8 reaction event.
    Sent when player clicks the reaction button during Eight card event.
    """
    def __init__(self):
        self.message_type = MessageType.RULE_8_REACTION


# =============================================================================
# SERVER-TO-CLIENT MESSAGES (State & Broadcasts)
# =============================================================================

@dataclass
class GameStateUpdate(NetworkMessage):
    """
    Server broadcasts complete game state to all clients.
    This is the authoritative source of truth for all clients.
    Contains massive state payload for UI rendering.
    """
    current_turn_player_id: int
    current_play_direction: TurnDirection
    top_discard_card: CardDTO
    client_hand: List[CardDTO]  # This client's cards
    opponents_card_counts: Dict[str, int]  # e.g. {"player_id_2": 5}
    active_stacking_penalty: int = 0  # Current +2/+4 accumulation
    active_color: Optional[CardColor] = None  # Overrides top_card color if wild

    def __init__(self, current_turn_player_id: int, current_play_direction: TurnDirection,
                 top_discard_card: CardDTO, client_hand: List[CardDTO],
                 opponents_card_counts: Dict[str, int], active_stacking_penalty: int = 0,
                 active_color: Optional[CardColor] = None):
        self.message_type = MessageType.GAME_STATE_UPDATE
        self.current_turn_player_id = current_turn_player_id
        self.current_play_direction = current_play_direction
        self.top_discard_card = top_discard_card
        self.client_hand = client_hand
        self.opponents_card_counts = opponents_card_counts
        self.active_stacking_penalty = active_stacking_penalty
        self.active_color = active_color

    def to_dict(self) -> dict:
        """Convert to dict with proper enum serialization."""
        data = super().to_dict()
        data['current_play_direction'] = self.current_play_direction.value
        data['top_discard_card'] = self.top_discard_card.to_dict()
        data['client_hand'] = [card.to_dict() for card in self.client_hand]
        if self.active_color:
            data['active_color'] = self.active_color.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameStateUpdate":
        """Create from dict with proper enum deserialization."""
        return cls(
            current_turn_player_id=data['current_turn_player_id'],
            current_play_direction=TurnDirection(data['current_play_direction']),
            top_discard_card=CardDTO.from_dict(data['top_discard_card']),
            client_hand=[CardDTO.from_dict(c) for c in data['client_hand']],
            opponents_card_counts=data['opponents_card_counts'],
            active_stacking_penalty=data.get('active_stacking_penalty', 0),
            active_color=CardColor(data['active_color']) if data.get('active_color') else None
        )


@dataclass
class EventBroadcast(NetworkMessage):
    """
    Server broadcasts UI events to all clients.
    Triggers specific UI changes or notifications.
    Examples: RULE_8_STARTED, PLAYER_UNO, GAME_OVER
    """
    event_name: str  # e.g., "RULE_8_STARTED", "PLAYER_UNO", "GAME_OVER"
    event_data: dict = field(default_factory=dict)  # Flexible payload

    def __init__(self, event_name: str, event_data: dict = None):
        self.message_type = MessageType.EVENT_BROADCAST
        self.event_name = event_name
        self.event_data = event_data or {}


@dataclass
class ErrorMessage(NetworkMessage):
    """
    Server rejects an invalid client action.
    Sent to specific client who made the invalid move.
    
    Error types include:
    - ILLEGAL_MOVE: Card cannot be played on current top card
    - WRONG_TURN: It's not this player's turn
    - CANNOT_WIN_WITH_ACTION: Cannot win with Skip/Reverse/Draw Two/Draw Four
    """
    error_type: str  # e.g., "ILLEGAL_MOVE", "CANNOT_WIN_WITH_ACTION", "WRONG_TURN"
    message: str  # Human-readable error message

    def __init__(self, error_type: str, message: str):
        self.message_type = MessageType.ERROR_MESSAGE
        self.error_type = error_type
        self.message = message


# =============================================================================
# MESSAGE PARSING UTILITY
# =============================================================================

def parse_incoming_message(json_str: str) -> NetworkMessage:
    """
    Parse an incoming JSON message and return the appropriate message object.
    This is the main entry point for deserializing network messages.
    
    Args:
        json_str: JSON string received from socket
        
    Returns:
        Appropriate NetworkMessage subclass instance
        
    Raises:
        ValueError: If message format is invalid
    """
    try:
        data = json.loads(json_str)
        message_type_str = data.get('message_type')
        
        if not message_type_str:
            raise ValueError("Missing 'message_type' field")
            
        message_type = MessageType(message_type_str)

        # Route to appropriate message class based on type
        if message_type == MessageType.JOIN_ROOM:
            msg = JoinRoom(
                username=data.get('username', ''),
                player_id=data.get('player_id')
            )
            return msg
        elif message_type == MessageType.START_GAME:
            return StartGame()
        elif message_type == MessageType.PLAY_CARD:
            return PlayCard.from_dict(data)
        elif message_type == MessageType.DRAW_CARD:
            return DrawCard()
        elif message_type == MessageType.RULE_8_REACTION:
            return Rule8Reaction()
        elif message_type == MessageType.GAME_STATE_UPDATE:
            return GameStateUpdate.from_dict(data)
        elif message_type == MessageType.EVENT_BROADCAST:
            msg = EventBroadcast(
                event_name=data.get('event_name', ''),
                event_data=data.get('event_data', {})
            )
            return msg
        elif message_type == MessageType.ERROR_MESSAGE:
            msg = ErrorMessage(
                error_type=data.get('error_type', ''),
                message=data.get('message', '')
            )
            return msg
        else:
            raise ValueError(f"Unknown message type: {message_type_str}")

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except (KeyError, ValueError) as e:
        raise ValueError(f"Invalid message structure: {e}")

