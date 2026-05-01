"""
Game engine for managing core game logic.
Handles turn progression, card validation, game state, and win conditions.
This is the authoritative source of truth for game state (Host-Authoritative model).
All clients trust the host's decisions on game state and rule enforcement.
"""

from typing import List, Optional, Tuple, Callable, Dict
from shared.data_structures import Card, Player, GameStatus, ReactionEvent, StackingState
from shared.enums import (
    GameState, PlayerState, CardColor, CardValue, TurnDirection, 
    ReactionEventState as ReactionStateEnum, CardAction
)
from server.deck import Deck
from server.player import PlayerManager
from server.rules import RuleEngine


class GameEngine:
    """
    Central game logic engine (Host-Authoritative).
    Handles all game mechanics, turn progression, and rule application.
    Communicates game state changes via broadcast callback.
    All authority over game state flows through this engine.
    """
    
    def __init__(self, state_update_callback: Callable, enable_rule_0: bool = True,
                 enable_rule_7: bool = True, enable_rule_8: bool = True,
                 enable_stacking: bool = True, cannot_win_with_action: bool = True):
        """
        Initialize the game engine.
        
        Args:
            state_update_callback: Callback to broadcast game state updates
            enable_rule_0: Enable Play in Order (pass entire hand)
            enable_rule_7: Enable Sevens (hand swap)
            enable_rule_8: Enable Eights (reaction event)
            enable_stacking: Enable draw card stacking
            cannot_win_with_action: Disallow action cards as final card
        """
        pass
    
    def start_game(self, players: List[Player]) -> bool:
        """
        Initialize and start a new game.
        Shuffles deck, deals initial hands, selects starting player.
        
        Args:
            players: List of Player objects to play
        
        Returns:
            True if game started successfully
        """
        pass
    
    def end_game(self) -> Optional[int]:
        """
        End the current game and determine winner.
        Calculates final scores, cleans up state.
        
        Returns:
            ID of winning player or None if error
        """
        pass
    
    def next_turn(self):
        """
        Progress to the next player's turn.
        Handles turn direction (forward/reverse), skipped players.
        Updates current player and broadcasts state.
        """
        pass
    
    def attempt_play_card(self, player_id: int, card_index: int,
                         target_color: Optional[CardColor] = None,
                         target_player_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Attempt to play a card from a player's hand.
        Host-authoritative validation: rejects illegal plays.
        
        Validation steps:
        1. Verify it's the correct player's turn
        2. Verify card exists in player's hand
        3. Verify card is legal (RuleEngine.is_valid_play)
        4. Check win condition (cannot win with action card if rule enabled)
        5. Handle special rules (Rule 0, 7, 8) if applicable
        6. Handle stacking if applicable
        7. Execute the play and progress turn
        
        Args:
            player_id: ID of player attempting to play
            card_index: Index of card in player's hand
            target_color: Target color for wild cards
            target_player_id: Target player for Rule 7 (hand swap)
            
        Returns:
            Tuple: (success, error_message)
            success: True if card was played successfully
            error_message: Reason for rejection if failed
        """
        pass
    
    def attempt_draw_card(self, player_id: int) -> Tuple[bool, Card]:
        """
        Handle player's draw action (when no legal play available).
        
        Process:
        1. Draw one card from draw pile
        2. Add to player's hand
        3. Check if drawn card is playable
        4. If playable, allow immediate play same turn
        5. If not playable, end turn
        
        Args:
            player_id: ID of player drawing
            
        Returns:
            Tuple: (drawn_card_playable, drawn_card)
            drawn_card_playable: True if player can play it immediately
            drawn_card: The card that was drawn
        """
        pass
    
    def draw_cards_penalty(self, player_id: int, count: int, reason: str):
        """
        Apply penalty draw (from +2, +4, Rule 8, stacking, etc.).
        Player draws specified number of cards and loses turn.
        
        Args:
            player_id: ID of player drawing penalty
            count: Number of cards to draw
            reason: Reason for penalty ("draw_two", "draw_four_stacking", "rule_8_reaction", etc.)
        """
        pass
    
    def skip_player(self):
        """Skip the current player's turn and move to next player."""
        pass
    
    def reverse_turn_order(self):
        """Reverse the direction of play (due to reverse card)."""
        pass
    
    def apply_wild_card(self, player_id: int, target_color: CardColor):
        """
        Apply wild card effect (change active color for discard pile).
        
        Args:
            player_id: ID of player playing wild card
            target_color: New color for discard pile
        """
        pass
    
    def trigger_reaction_event_rule_8(self, triggered_by_player_id: int,
                                      triggered_card: Card) -> ReactionEvent:
        """
        Trigger Rule 8 reaction event (Eight card played).
        All players must respond within timeout.
        Last responder draws 2 cards.
        
        Host responsibilities:
        1. Create ReactionEvent object
        2. Broadcast ReactionEventMessage to all clients
        3. Set timeout (3 seconds)
        4. Collect responses
        5. Resolve after timeout
        
        Args:
            triggered_by_player_id: ID of player who played Eight
            triggered_card: The Eight card
            
        Returns:
            ReactionEvent object for tracking
        """
        pass
    
    def submit_reaction_response(self, player_id: int, reaction_event: ReactionEvent,
                                current_time: float) -> bool:
        """
        Record a player's response to reaction event.
        Called when client sends ReactionResponseMessage.
        
        Args:
            player_id: ID of responding player
            reaction_event: The active reaction event
            current_time: Server timestamp of response
            
        Returns:
            True if response was recorded
        """
        pass
    
    def resolve_reaction_event(self, reaction_event: ReactionEvent,
                               current_time: float) -> Optional[int]:
        """
        Resolve reaction event after timeout.
        Determines last responder (who draws 2 cards).
        
        Args:
            reaction_event: The reaction event to resolve
            current_time: Current server time
            
        Returns:
            ID of player(s) who must draw, or None
        """
        pass
    
    def apply_rule_7_hand_swap(self, swapper_player_id: int,
                              target_player_id: int) -> bool:
        """
        Apply Rule 7: Swap hands between two players.
        
        Args:
            swapper_player_id: ID of player playing Seven
            target_player_id: ID of target player
            
        Returns:
            True if swap was successful
        """
        pass
    
    def apply_rule_0_hand_pass(self, passer_player_id: int,
                               target_player_id: int,
                               direction: str) -> bool:
        """
        Apply Rule 0: Pass entire hand to target in direction.
        Player keeps turn after passing.
        
        Args:
            passer_player_id: ID of player passing hand
            target_player_id: ID of target player
            direction: "forward" or "reverse"
            
        Returns:
            True if pass was successful
        """
        pass
    
    def apply_stacking_accumulation(self, card_played: Card) -> Tuple[bool, int]:
        """
        Apply Stacking Rule: Accumulate +2/+4 cards.
        
        Validation:
        - +2 can stack on +2 or +4 (accumulate)
        - +4 can stack on +2 or +4 (accumulate)
        - +4 cannot stack on +2 (invalid, resolve original +2)
        
        Args:
            card_played: The +2 or +4 card being stacked
            
        Returns:
            Tuple: (is_valid_stacking, new_total_penalty)
        """
        pass
    
    def resolve_stacking_penalty(self, responder_player_id: int,
                                 penalty_count: int):
        """
        Resolve stacking penalty: player draws accumulated cards and loses turn.
        
        Args:
            responder_player_id: ID of player who must draw
            penalty_count: Total accumulated penalty
        """
        pass
    
    def check_win_condition(self) -> Optional[int]:
        """
        Check if any player has won.
        Win condition: Player has 0 cards in hand (UNO played).
        Cannot win with action card if rule enabled.
        
        Returns:
            ID of winner if game is won, None otherwise
        """
        pass
    
    def check_game_over_conditions(self) -> Optional[Tuple[int, str]]:
        """
        Check for game-ending conditions.
        - Player won (hand empty)
        - Player disconnected before game start
        - All other players disconnected
        
        Returns:
            Tuple: (winner_id, reason) or None if game continues
            reason: "player_won", "player_disconnected", etc.
        """
        pass
    
    def get_current_player_id(self) -> Optional[int]:
        """Get the ID of the player whose turn it is."""
        pass
    
    def get_game_status(self) -> GameStatus:
        """Get the current game status for broadcasting."""
        pass
    
    def serialize_game_state(self) -> Dict:
        """
        Serialize complete game state to dictionary (for client updates).
        Host broadcasts this to keep all clients in sync.
        
        Returns:
            Dictionary representation of entire game state
        """
        pass
    
    def get_player_hands(self) -> Dict[int, List[Card]]:
        """
        Get all players' hands.
        Note: Each client only knows its own hand via local state.
        
        Returns:
            Dictionary mapping player_id to list of Cards
        """
        pass
    
    def handle_disconnect(self, player_id: int):
        """
        Handle player disconnection during game.
        
        If before game start:
        - Remove player from room
        
        If during game:
        - Mark player as disconnected
        - Skip their turns automatically
        - End game if only 1 player left
        
        Args:
            player_id: ID of disconnected player
        """
        pass
    
    def validate_action_is_current_player_turn(self, player_id: int) -> bool:
        """
        Validate that it's the specified player's turn.
        Host enforces strict turn order.
        
        Args:
            player_id: ID of player taking action
            
        Returns:
            True if it's this player's turn
        """
        pass
    
    def validate_card_in_hand(self, player_id: int, card_index: int) -> bool:
        """
        Validate that card exists at index in player's hand.
        
        Args:
            player_id: ID of player
            card_index: Index to check
            
        Returns:
            True if valid index and card exists
        """
        pass
    
    def broadcast_game_state_update(self):
        """Broadcast current game state to all connected clients."""
        pass
    
    def get_all_players(self) -> List[Player]:
        """Get list of all players in the game."""
        pass
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a specific player by ID."""
        pass
