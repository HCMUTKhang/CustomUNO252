"""
Card display UI component.
Renders individual UNO cards with visual styling.
"""

from typing import Callable, Optional, Tuple
from shared.data_structures import Card


class CardDisplay:
    """
    UI component for displaying and interacting with cards.
    """
    
    def __init__(self, card: Card, x: int, y: int, width: int, height: int,
                 on_click: Optional[Callable] = None):
        """
        Initialize a card display.
        
        Args:
            card: Card object to display
            x: X position
            y: Y position
            width: Card width
            height: Card height
            on_click: Optional callback when card is clicked
        """
        pass
    
    def set_card(self, card: Card):
        """
        Update the card being displayed.
        
        Args:
            card: New card to display
        """
        pass
    
    def set_position(self, x: int, y: int):
        """
        Set card position.
        
        Args:
            x: X position
            y: Y position
        """
        pass
    
    def set_selected(self, selected: bool):
        """
        Highlight card as selected.
        
        Args:
            selected: True to select
        """
        pass
    
    def is_mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Check if mouse is over the card.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if mouse is over card
        """
        pass
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle click event at mouse position.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if click was on card
        """
        pass
    
    def render(self, renderer):
        """
        Render the card display.
        
        Args:
            renderer: Renderer instance
        """
        pass
    
    def update(self, delta_time: float):
        """
        Update card display state (e.g., animations).
        
        Args:
            delta_time: Time since last frame
        """
        pass
