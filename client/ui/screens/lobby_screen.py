"""
Lobby screen.
Shows connected players, allows starting the game, displays room info.
"""

from typing import Callable, Optional
from shared.data_structures import Player


class LobbyScreen:
    """
    Lobby UI screen.
    Displays players in the room and allows game start.
    """
    
    def __init__(self, on_start_game: Callable, on_leave_room: Callable):
        """
        Initialize the lobby screen.
        
        Args:
            on_start_game: Callback when host clicks "Start Game"
            on_leave_room: Callback when player clicks "Leave Room"
        """
        pass
    
    def update_players(self, players: list):
        """
        Update the list of players in the lobby.
        
        Args:
            players: List of Player objects
        """
        pass
    
    def set_room_info(self, room_id: str, max_players: int):
        """
        Set room information to display.
        
        Args:
            room_id: ID of the room
            max_players: Maximum players allowed
        """
        pass
    
    def set_is_host(self, is_host: bool):
        """
        Set whether local player is the host.
        
        Args:
            is_host: True if local player hosts
        """
        pass
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the lobby screen.
        
        Args:
            input_data: Input action dictionary
        """
        pass
    
    def render(self, renderer):
        """
        Render the lobby screen.
        
        Args:
            renderer: Renderer instance
        """
        pass
    
    def update(self, delta_time: float):
        """
        Update lobby screen state.
        
        Args:
            delta_time: Time since last frame
        """
        pass
