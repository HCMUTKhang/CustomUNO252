"""
Button UI component.
Reusable button component for menus and game screens.
"""

from typing import Callable, Tuple, Optional


class Button:
    """
    Reusable button UI component.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, on_click: Callable):
        """
        Initialize a button.
        
        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            text: Button text label
            on_click: Callback when button is clicked
        """
        pass
    
    def set_position(self, x: int, y: int):
        """
        Set button position.
        
        Args:
            x: X position
            y: Y position
        """
        pass
    
    def set_text(self, text: str):
        """
        Set button text.
        
        Args:
            text: New text label
        """
        pass
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable the button.
        
        Args:
            enabled: True to enable
        """
        pass
    
    def is_mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Check if mouse is over the button.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if mouse is over button
        """
        pass
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle click event at mouse position.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if click was on button
        """
        pass
    
    def render(self, renderer):
        """
        Render the button.
        
        Args:
            renderer: Renderer instance
        """
        pass
    
    def update(self, delta_time: float):
        """
        Update button state (e.g., hover effects).
        
        Args:
            delta_time: Time since last frame
        """
        pass
