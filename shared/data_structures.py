"""
Data structures shared between Client and Server.
Aligned with functional requirements: Host-Authoritative, Custom Rules, Stacking, Reaction Events.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from shared.enums import (
    CardColor, CardValue, CardAction, GameState, PlayerState, 
    TurnDirection, ReactionEventState, StackingState
)


@dataclass
class Card:
    """Represents a single UNO card."""
    color: CardColor
    value: CardValue
    
    @property
    def action_type(self) -> CardAction:
        """Get the action type of this card."""
        pass
    
    def to_dict(self) -> dict:
        """Convert card to dictionary for JSON serialization."""
        pass
    
    @staticmethod
    def from_dict(data: dict) -> 'Card':
        """Create card from dictionary (JSON deserialization)."""
        pass


@dataclass
class Player:
    """Represents a player in the game."""
    player_id: int
    name: str
    hand: List[Card] = field(default_factory=list)
    state: PlayerState = PlayerState.IDLE
    score: int = 0
    is_host: bool = False
    is_connected: bool = True
    
    def to_dict(self) -> dict:
        """Convert player to dictionary for JSON serialization."""
        pass
    
    @staticmethod
    def from_dict(data: dict) -> 'Player':
        """Create player from dictionary (JSON deserialization)."""
        pass


@dataclass
class StackingState:
    """Tracks the state of +2/+4 card stacking (Stacking Rule)."""
    is_active: bool = False
    accumulated_penalty: int = 0  # Total cards to draw
    last_card_played: Optional[Card] = None  # Last +2 or +4 played
    responder_player_id: Optional[int] = None  # Player who must draw
    
    def to_dict(self) -> dict:
        """Serialize stacking state."""
        pass
    
    @staticmethod
    def from_dict(data: dict) -> 'StackingState':
        """Deserialize stacking state."""
        pass


@dataclass
class ReactionEvent:
    """
    Tracks a Rule 8 reaction event (Eight card played).
    All players must click a reaction button within timeout.
    Last responder draws 2 cards.
    """
    is_active: bool = False
    triggered_by_player_id: Optional[int] = None  # Player who played the Eight
    triggered_card: Optional[Card] = None  # The Eight card
    event_start_time: float = 0.0  # Timestamp when event started
    timeout_seconds: float = 3.0  # Reaction window duration
    responders: Dict[int, float] = field(default_factory=dict)  # player_id -> response_time
    state: ReactionEventState = ReactionEventState.PENDING
    penalty_drawer_id: Optional[int] = None  # Last responder (to draw 2 cards)
    
    def to_dict(self) -> dict:
        """Serialize reaction event."""
        pass
    
    @staticmethod
    def from_dict(data: dict) -> 'ReactionEvent':
        """Deserialize reaction event."""
        pass


@dataclass
class GameStatus:
    """Represents the current game status (Host-Authoritative)."""
    game_state: GameState
    current_player_id: Optional[int] = None
    current_turn_count: int = 0
    last_card_played: Optional[Card] = None
    draw_pile_count: int = 0
    discard_pile_count: int = 0
    turn_direction: TurnDirection = TurnDirection.FORWARD
    
    # Rule state tracking
    stacking_state: StackingState = field(default_factory=StackingState)
    reaction_event: ReactionEvent = field(default_factory=ReactionEvent)
    
    # Active wild card color (after Wild/Wild Draw Four played)
    active_wild_color: Optional[CardColor] = None
    
    # Rule 7 hand swap tracking
    rule_7_swap_target: Optional[int] = None  # Target player for hand swap
    
    def to_dict(self) -> dict:
        """Convert game status to dictionary for JSON serialization."""
        pass
    
    @staticmethod
    def from_dict(data: dict) -> 'GameStatus':
        """Create game status from dictionary (JSON deserialization)."""
        pass


@dataclass
class GameRoom:
    """Represents a game room/session (Host-Authoritative)."""
    room_id: str
    host_id: int
    players: List[Player] = field(default_factory=list)
    status: GameStatus = field(default_factory=lambda: GameStatus(GameState.LOBBY))
    max_players: int = 4
    created_at: float = 0.0
    started_at: Optional[float] = None
    
    # Custom rule enablement
    enable_rule_0: bool = True  # Play in Order
    enable_rule_7: bool = True  # Hand Swap
    enable_rule_8: bool = True  # Reaction Event
    enable_stacking: bool = True  # Stacking +2/+4
    
    # Game configuration
    reverse_as_skip_two_player: bool = False  # 2-player Reverse behavior
    cannot_win_with_action_card: bool = True  # Win condition rule
    
    def to_dict(self) -> dict:
        """Convert game room to dictionary for JSON serialization."""
        pass
    
    @staticmethod
    def from_dict(data: dict) -> 'GameRoom':
        """Create game room from dictionary (JSON deserialization)."""
        pass
    
    def get_player_count(self) -> int:
        """Get number of connected players."""
        pass
    
    def is_full(self) -> bool:
        """Check if room is at max capacity."""
        pass
