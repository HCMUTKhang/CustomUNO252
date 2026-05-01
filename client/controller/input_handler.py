"""
Input handler for capturing player interactions (mouse and keyboard).
"""

import pygame
from typing import Optional, Tuple, Callable
from enum import Enum


class InputAction(Enum):
    """Enumeration of possible input actions."""
    CLICK = "click"
    KEY_PRESS = "key_press"
    MOUSE_MOVE = "mouse_move"
    DRAG_START = "drag_start"
    DRAG_END = "drag_end"


class InputHandler:
    """
    Captures and processes player input events (mouse, keyboard).
    Converts pygame events into game-relevant actions.
    """
    
    def __init__(self, action_callback: Callable):
        """
        Initialize the input handler.
        
        Args:
            action_callback: Callback function for input actions
        """
        pass
    
    def process_events(self, events: list):
        """
        Process pygame events and generate input actions.
        
        Args:
            events: List of pygame events
        """
        pass
    
    def handle_mouse_click(self, pos: Tuple[int, int], button: int):
        """
        Handle mouse click events.
        
        Args:
            pos: Mouse position (x, y)
            button: Mouse button number (1=left, 2=middle, 3=right)
        """
        pass
    
    def handle_key_press(self, key: int):
        """
        Handle keyboard input.
        
        Args:
            key: pygame key constant
        """
        pass
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """
        Handle mouse movement.
        
        Args:
            pos: Mouse position (x, y)
        """
        pass
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        pass
