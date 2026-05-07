"""
Deck management for the UNO game.
Handles card creation, shuffling, drawing, and discarding.
"""
import random
from typing import List, Optional
from shared.data_structures import Card
from shared.enums import CardColor, CardValue


class Deck:
    """
    Manages the game deck including draw pile and discard pile.
    """
    
    def __init__(self):
        """Initialize and populate the deck."""
        self.draw_pile: List[Card] = []
        self.discard_pile: List[Card] = []
    
    def initialize_deck(self):
        """Create all 108 UNO cards and add to draw pile."""
        for card_color in [CardColor.RED, CardColor.YELLOW, CardColor.GREEN, CardColor.BLUE]:
            # Add number cards (0-9)
            for value in [CardValue.ZERO, CardValue.ONE, CardValue.TWO, CardValue.THREE,
                          CardValue.FOUR, CardValue.FIVE, CardValue.SIX, CardValue.SEVEN,
                          CardValue.EIGHT, CardValue.NINE, CardValue.SKIP, CardValue.REVERSE, CardValue.DRAW_TWO]:
                new_card = Card(color=card_color, value=value)
                self.draw_pile.append(new_card)
                self.draw_pile.append(new_card)
            # Add action cards (Skip, Reverse, Draw Two)
            for action in [CardValue.WILD, CardValue.WILD_DRAW_FOUR]:
                self.draw_pile.append(Card(color=card_color, value=action))
                self.draw_pile.append(Card(color=card_color, value=action))
        
    
    def shuffle_draw_pile(self):
        """Shuffle the draw pile."""
        random.shuffle(self.draw_pile)
    
    def draw_card(self) -> Optional[Card]:
        """
        Draw a card from the draw pile.
        If draw pile is empty, reshuffle discard pile.
        
        Returns:
            Card object or None if unable to draw
        """
        if not self.draw_pile:
            if not self.discard_pile:
                return None  # No cards available anywhere
            self.reshuffle_discard_to_draw()
        if not self.draw_pile:
            return None
        return self.draw_pile.pop()
    
    def draw_multiple(self, count: int) -> List[Card]:
        """
        Draw multiple cards from the draw pile.
        
        Args:
            count: Number of cards to draw
            
        Returns:
            List of Card objects
        """
        drawn_cards: List[Card] = []
        for _ in range(count):
            card = self.draw_card()
            if card is not None:
                drawn_cards.append(card)
            else:
                break  # No more cards to draw
        return drawn_cards
    
    def discard_card(self, card: Card):
        """
        Add a card to the discard pile.
        
        Args:
            card: Card to discard
        """
        self.discard_pile.append(card)
    
    def peek_top_discard(self) -> Optional[Card]:
        """
        Peek at the top card of the discard pile without removing it.
        
        Returns:
            Top card or None if discard pile is empty
        """
        if self.discard_pile:
            return self.discard_pile[-1]
        return None
    
    def get_draw_pile_count(self) -> int:
        """Get the number of cards remaining in the draw pile."""
        return len(self.draw_pile)
    
    def get_discard_pile_count(self) -> int:
        """Get the number of cards in the discard pile."""
        return len(self.discard_pile)
    
    def reshuffle_discard_to_draw(self):
        """Move discard pile cards back to draw pile and reshuffle."""
        self.draw_pile = self.discard_pile
        self.discard_pile = []
        self.shuffle_draw_pile()
