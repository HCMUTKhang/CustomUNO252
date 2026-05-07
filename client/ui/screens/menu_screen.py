"""
Main menu screen.
Allows player to start a game or join an existing game room.
"""

from typing import Callable, Optional


class MenuScreen:
    """
    Main menu UI screen.
    Displays options to host or join a game.
    """
    
    def __init__(self, on_host_click: Callable, on_join_click: Callable):
        """
        Initialize the menu screen.
        
        Args:
            on_host_click: Callback when "Host Game" is clicked
            on_join_click: Callback when "Join Game" is clicked
        """
        pass
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the menu screen.
        
        Args:
            input_data: Input action dictionary
        """
        pass
    
    def render(self, renderer):
        """
        Render the menu screen.
        
        Args:
            renderer: Renderer instance
        """
        pass
    
    def update(self, delta_time: float):
        """
        Update menu screen state (e.g., animations).
        
        Args:
            delta_time: Time since last frame
        """
        pass
