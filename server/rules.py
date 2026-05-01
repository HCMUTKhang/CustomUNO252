"""
Custom UNO rules implementation.
Handles Rule 0 (Pass entire hand), Rule 7 (Sevens/hand swap), Rule 8 (Eights/reaction event),
Stacking (+2/+4 accumulation), and base UNO rules.
Host-authoritative validation (all logic enforced by host).
"""

from typing import List, Optional, Tuple
from shared.data_structures import Card, Player, ReactionEvent, StackingState
from shared.enums import CardColor, CardValue, CardAction, StackingState as StackingStateEnum


class RuleEngine:
    """
    Validates and applies custom UNO rules.
    All validation is host-authoritative and clients trust these decisions.
    """
    
    def __init__(self, enable_rule_0: bool = True, enable_rule_7: bool = True,
                 enable_rule_8: bool = True, enable_stacking: bool = True,
                 cannot_win_with_action_card: bool = True):
        """
        Initialize the rule engine with custom rule settings.
        
        Args:
            enable_rule_0: Enable Play in Order (pass entire hand)
            enable_rule_7: Enable Sevens hand swap rule
            enable_rule_8: Enable Eights reaction event rule
            enable_stacking: Enable draw card stacking (+2/+4 accumulation)
            cannot_win_with_action_card: Cannot use action card as final card
        """
        pass
    
    def is_valid_play(self, played_card: Card, top_card: Card,
                      active_wild_color: Optional[CardColor] = None) -> bool:
        """
        Check if a card can be played on top of another card.
        Host-authoritative validation: rejects illegal plays.
        
        Criteria for valid play:
        - Same color (unless wild or active wild color)
        - Same number/value
        - Same action type
        - Valid Wild or Wild Draw Four
        
        Args:
            played_card: Card being played
            top_card: Current top card on discard pile
            active_wild_color: Active color if top card is wild
            
        Returns:
            True if play is valid, False if illegal
        """
        pass
    
    def is_playable_hand_exists(self, hand: List[Card], top_card: Card,
                                active_wild_color: Optional[CardColor] = None) -> bool:
        """
        Check if player has any legal card to play.
        Used to determine if player must draw.
        
        Args:
            hand: Player's hand (list of Cards)
            top_card: Current top card on discard pile
            active_wild_color: Active color if top card is wild
            
        Returns:
            True if hand contains at least one playable card
        """
        pass
    
    def check_uno(self, hand_size: int) -> bool:
        """
        Check if a player has UNO (1 card left in hand).
        
        Args:
            hand_size: Current size of player's hand after card play
            
        Returns:
            True if player has exactly 1 card left
        """
        pass
    
    def can_win_with_card(self, card: Card) -> bool:
        """
        Check if a card is allowed as the final card (win condition).
        If CANNOT_WIN_WITH_ACTION_CARD is enabled, rejects Skip/Reverse/Draw Two.
        
        Args:
            card: Card being considered as final card
            
        Returns:
            True if this card can be used to win, False if not allowed
        """
        pass
    
    def apply_rule_0(self, current_player_id: int, playing_player_id: int,
                     target_player_id: int, hand_direction: str) -> bool:
        """
        Apply Rule 0: Play in Order.
        Current player can pass entire hand to a direction and keep turn.
        Requires playing a card of same color/value as top card.
        
        Args:
            current_player_id: ID of player whose turn it is
            playing_player_id: ID of player attempting to play (should be current)
            target_player_id: Target player to receive the hand
            hand_direction: "forward" or "backward" (left/right)
            
        Returns:
            True if Rule 0 play is valid
        """
        pass
    
    def apply_rule_7(self, player_id: int, played_card: Card,
                     target_player_id: int) -> bool:
        """
        Apply Rule 7: Sevens (Hand Swap).
        Playing a Seven allows player to swap hands with target player.
        Card must be a valid Seven (CardValue.SEVEN).
        
        Args:
            player_id: ID of player playing the Seven
            played_card: The Seven card being played
            target_player_id: Target player to swap hands with
            
        Returns:
            True if swap is valid
        """
        pass
    
    def apply_rule_8(self, triggered_by_player_id: int, played_card: Card,
                     all_player_ids: List[int]) -> ReactionEvent:
        """
        Apply Rule 8: Eights (Reaction Event).
        Playing an Eight triggers a reaction event.
        All players have 3 seconds to click reaction button.
        Last responder (slowest or didn't respond) draws 2 cards.
        
        Host must:
        - Broadcast ReactionEventMessage to all clients
        - Collect responses within timeout
        - Determine last responder
        - Apply 2-card penalty
        
        Args:
            triggered_by_player_id: ID of player who played the Eight
            played_card: The Eight card that triggered the event
            all_player_ids: List of all player IDs to respond
            
        Returns:
            ReactionEvent object with event tracking information
        """
        pass
    
    def validate_rule_8_response(self, reaction_event: ReactionEvent,
                                responding_player_id: int,
                                response_time: float) -> bool:
        """
        Validate and record a player's response to Rule 8 reaction event.
        
        Args:
            reaction_event: The active reaction event
            responding_player_id: ID of player responding
            response_time: Server-recorded timestamp of response
            
        Returns:
            True if response was valid and recorded
        """
        pass
    
    def resolve_rule_8_event(self, reaction_event: ReactionEvent,
                             current_time: float) -> Optional[int]:
        """
        Resolve Rule 8 reaction event after timeout expires.
        Determines last responder (who draws 2 cards).
        
        Rules:
        - Player who didn't respond in time = latest responder
        - If multiple didn't respond = all draw 2 cards
        - If all responded = last one by response time draws
        
        Args:
            reaction_event: The reaction event to resolve
            current_time: Current server time
            
        Returns:
            ID of player who must draw 2 cards, or None if all must draw
        """
        pass
    
    def apply_stacking(self, current_stacking_state: StackingState,
                      new_card: Card) -> Tuple[bool, Optional[int]]:
        """
        Apply Stacking Rule: +2/+4 accumulation.
        Rules:
        - +2 on +2 = +4 total (valid stacking)
        - +2 on +4 = +6 total (valid stacking)
        - +4 on +4 = +8 total (valid stacking)
        - +4 on +2 = NOT VALID (invalid stacking, original +2 resolves)
        
        Host validates new card before adding to stack.
        
        Args:
            current_stacking_state: Current accumulated penalty state
            new_card: New card being played on top
            
        Returns:
            Tuple: (is_valid_stacking, total_penalty)
            is_valid_stacking: True if stacking is allowed
            total_penalty: New accumulated penalty, or None if stacking not valid
        """
        pass
    
    def get_card_action_type(self, card: Card) -> CardAction:
        """
        Get the action type of a card (Number, Skip, Reverse, etc.).
        Used to determine valid play matching.
        
        Args:
            card: Card to get action type for
            
        Returns:
            CardAction enumeration value
        """
        pass
    
    def calculate_card_points(self, card: Card) -> int:
        """
        Calculate points for a card (used for round scoring).
        - Number cards: face value (0-9)
        - Skip, Reverse, +2: 20 points
        - Wild: 50 points
        - Wild +4: 50 points
        
        Args:
            card: Card to score
            
        Returns:
            Point value of the card
        """
        pass
    
    def calculate_hand_points(self, hand: List[Card]) -> int:
        """
        Calculate total points for a hand (used for round scoring).
        
        Args:
            hand: List of cards in hand
            
        Returns:
            Total points for the hand
        """
        pass
    
    def validate_play_legality(self, played_card: Card, top_card: Card,
                               player_has_playable: bool,
                               current_player_id: int, playing_player_id: int) -> Tuple[bool, str]:
        """
        Comprehensive host-side validation of card play.
        Rejects invalid plays and returns error reason.
        
        Validates:
        - Card is in player's hand
        - It's the correct player's turn
        - Card is legal to play
        - Not winning with action card (if rule enabled)
        
        Args:
            played_card: Card being played
            top_card: Top card on discard pile
            player_has_playable: Whether player has playable card
            current_player_id: Whose turn it should be
            playing_player_id: Who is trying to play
            
        Returns:
            Tuple: (is_valid, error_message)
            is_valid: True if play is legal
            error_message: Reason for rejection, or "" if valid
        """
        pass
        Apply Stacking rule: Accumulate draw counts when +2 or +4 cards are stacked.
        
        Args:
            draw_count: Current accumulated draw count
            new_card: New card being stacked
            
        Returns:
            Updated draw count
        """
        pass
    
    def calculate_card_points(self, card: Card) -> int:
        """
        Calculate points for a card (used for scoring).
        
        Args:
            card: Card to score
            
        Returns:
            Point value of the card
        """
        pass
    
    def calculate_hand_points(self, hand: List[Card]) -> int:
        """
        Calculate total points for a hand (used for round scoring).
        
        Args:
            hand: List of cards in hand
            
        Returns:
            Total points
        """
        pass
