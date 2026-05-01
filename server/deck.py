"""
Deck management for the UNO game.
Handles card creation, shuffling, drawing, and discarding.
"""

from typing import List, Optional
from shared.data_structures import Card
from shared.enums import CardColor, CardValue


class Deck:
    """
    Manages the game deck including draw pile and discard pile.
    """
    
    def __init__(self):
        """Initialize and populate the deck."""
        pass
    
    def initialize_deck(self):
        """Create all 108 UNO cards and add to draw pile."""
        pass
    
    def shuffle_draw_pile(self):
        """Shuffle the draw pile."""
        pass
    
    def draw_card(self) -> Optional[Card]:
        """
        Draw a card from the draw pile.
        If draw pile is empty, reshuffle discard pile.
        
        Returns:
            Card object or None if unable to draw
        """
        pass
    
    def draw_multiple(self, count: int) -> List[Card]:
        """
        Draw multiple cards from the draw pile.
        
        Args:
            count: Number of cards to draw
            
        Returns:
            List of Card objects
        """
        pass
    
    def discard_card(self, card: Card):
        """
        Add a card to the discard pile.
        
        Args:
            card: Card to discard
        """
        pass
    
    def peek_top_discard(self) -> Optional[Card]:
        """
        Peek at the top card of the discard pile without removing it.
        
        Returns:
            Top card or None if discard pile is empty
        """
        pass
    
    def get_draw_pile_count(self) -> int:
        """Get the number of cards remaining in the draw pile."""
        pass
    
    def get_discard_pile_count(self) -> int:
        """Get the number of cards in the discard pile."""
        pass
    
    def reshuffle_discard_to_draw(self):
        """Move discard pile cards back to draw pile and reshuffle."""
        pass
