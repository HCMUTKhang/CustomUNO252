"""
Main Pygame renderer for the client UI.
Manages screen setup, drawing, and frame rendering.
"""

import pygame
from typing import List, Optional


class Renderer:
    """
    Main Pygame renderer.
    Handles screen initialization, frame updates, and game loop.
    """
    
    def __init__(self, width: int, height: int, fps: int = 60):
        """
        Initialize the renderer.
        
        Args:
            width: Screen width
            height: Screen height
            fps: Target frames per second
        """
        pass
    
    def initialize(self) -> bool:
        """
        Initialize Pygame and create the game window.
        
        Returns:
            True if initialization successful
        """
        pass
    
    def shutdown(self):
        """Shutdown Pygame and close the window."""
        pass
    
    def clear_screen(self, color: tuple = (255, 255, 255)):
        """
        Clear the screen with a background color.
        
        Args:
            color: RGB color tuple
        """
        pass
    
    def update_display(self):
        """Update the display to show the current frame."""
        pass
    
    def get_events(self) -> List:
        """
        Get all pygame events for this frame.
        
        Returns:
            List of pygame events
        """
        pass
    
    def draw_text(self, text: str, pos: tuple, font_size: int = 24, 
                  color: tuple = (0, 0, 0)):
        """
        Draw text on the screen.
        
        Args:
            text: Text string
            pos: Position (x, y)
            font_size: Font size in pixels
            color: RGB color tuple
        """
        pass
    
    def draw_image(self, image, pos: tuple, scale: Optional[tuple] = None):
        """
        Draw an image on the screen.
        
        Args:
            image: Pygame surface
            pos: Position (x, y)
            scale: Optional scale tuple (width, height)
        """
        pass
    
    def draw_rect(self, color: tuple, rect: tuple, filled: bool = True, width: int = 1):
        """
        Draw a rectangle.
        
        Args:
            color: RGB color tuple
            rect: Rect tuple (x, y, width, height)
            filled: Whether to fill the rectangle
            width: Border width if not filled
        """
        pass
    
    def get_tick(self) -> float:
        """Get the number of milliseconds since initialization."""
        pass
    
    def is_running(self) -> bool:
        """Check if the game window is still open."""
        pass
