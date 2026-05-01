"""
Message protocol definitions for Client-Server communication.
Defines the structure of all network messages.
Aligned with functional requirements: Host-Authoritative, Custom Rules, Reaction Events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from shared.enums import MessageType


@dataclass
class NetworkMessage:
    """Base network message structure."""
    message_type: MessageType
    sender_id: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    
    def to_json(self) -> str:
        """Serialize message to JSON string."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'NetworkMessage':
        """Deserialize message from JSON string."""
        pass


@dataclass
class HandshakeMessage(NetworkMessage):
    """Handshake message for initial connection."""
    player_name: str = ""
    player_id: Optional[int] = None
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'HandshakeMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class ActionMessage(NetworkMessage):
    """
    Player action message (play card, draw, etc.).
    Host validates all actions before accepting.
    """
    action_type: str = ""  # "play_card", "draw", "pass", etc.
    card_index: Optional[int] = None  # Index in player's hand
    target_color: Optional[str] = None  # For Wild cards
    target_player_id: Optional[int] = None  # For Rule 7 (hand swap)
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'ActionMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class StateUpdateMessage(NetworkMessage):
    """
    Server broadcasts updated game state to all clients.
    Host authoritative - this is the truth for all clients.
    """
    game_state: Dict[str, Any] = field(default_factory=dict)
    players: List[Dict[str, Any]] = field(default_factory=list)
    current_player_id: Optional[int] = None
    last_card_played: Optional[Dict[str, Any]] = None
    draw_pile_count: int = 0
    discard_pile_count: int = 0
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'StateUpdateMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class GameStartMessage(NetworkMessage):
    """
    Server signals game has started.
    Contains initial player order and first player.
    """
    room_id: str = ""
    players: List[Dict[str, Any]] = field(default_factory=list)
    starting_player_id: int = 0
    initial_discard_card: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'GameStartMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class GameEndMessage(NetworkMessage):
    """
    Server signals game has ended.
    Contains winner and final scores.
    """
    winner_id: int = 0
    final_scores: Dict[int, int] = field(default_factory=dict)
    reason: str = ""  # "player_won", "player_disconnected", etc.
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'GameEndMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class ErrorMessage(NetworkMessage):
    """
    Error message from server (invalid action, disconnection, etc.).
    Server rejects invalid client actions.
    """
    error_code: int = 0
    error_description: str = ""
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'ErrorMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class DisconnectMessage(NetworkMessage):
    """Disconnect notification."""
    reason: str = ""  # "player_quit", "connection_lost", etc.
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'DisconnectMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class ReactionEventMessage(NetworkMessage):
    """
    Rule 8: Server broadcasts reaction event start (Eight card played).
    All clients must show reaction button and collect responses.
    """
    triggered_by_player_id: int = 0  # Player who played the Eight
    triggered_card: Dict[str, Any] = field(default_factory=dict)  # The Eight
    timeout_seconds: float = 3.0  # Reaction window duration
    all_player_ids: List[int] = field(default_factory=list)  # All eligible responders
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'ReactionEventMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class ReactionResponseMessage(NetworkMessage):
    """
    Client sends reaction response to Eight card.
    Timestamp recorded by server to determine last responder.
    """
    reaction_event_id: Optional[int] = None  # ID of the reaction event
    did_respond: bool = True  # True = player reacted, False = timeout
    response_time: float = 0.0  # Server-recorded timestamp
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'ReactionResponseMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class RuleEffectMessage(NetworkMessage):
    """
    Special rule effects: hand swap (Rule 7), hand pass (Rule 0), etc.
    Server broadcasts the outcome to all players.
    """
    rule_type: str = ""  # "rule_0_pass", "rule_7_swap", etc.
    initiating_player_id: int = 0  # Player who triggered the rule
    target_player_id: Optional[int] = None  # Target of the rule effect
    affected_players: List[int] = field(default_factory=list)  # All affected players
    effect_data: Dict[str, Any] = field(default_factory=dict)  # Rule-specific data
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'RuleEffectMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class StackingUpdateMessage(NetworkMessage):
    """
    Stacking Rule: Server broadcasts stacking state update.
    When +2 or +4 is played on top of another, accumulates.
    """
    is_stacking: bool = False
    accumulated_penalty: int = 0  # Total cards to draw
    last_card_played: Optional[Dict[str, Any]] = None  # Last +2 or +4
    responder_player_id: Optional[int] = None  # Player who must draw
    stacking_chain: List[Dict[str, Any]] = field(default_factory=list)  # History of +2/+4 cards
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'StackingUpdateMessage':
        """Deserialize from JSON."""
        pass


@dataclass
class PenaltyDrawMessage(NetworkMessage):
    """
    Server notifies player of penalty draw (timeout, stacking, etc.).
    Specifies number of cards and reason.
    """
    player_id: int = 0
    penalty_count: int = 0
    reason: str = ""  # "stacking", "rule_8_last_responder", "draw_four_stacking", etc.
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        pass
    
    @staticmethod
    def from_json(json_str: str) -> 'PenaltyDrawMessage':
        """Deserialize from JSON."""
        pass
