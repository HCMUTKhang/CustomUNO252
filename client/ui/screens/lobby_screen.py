"""
Lobby screen.
Shows connected players, allows starting the game, displays room info.
"""

from typing import Callable, Optional
from shared.data_structures import Player
import pygame
from client.ui import theme


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
        self.on_start_game = on_start_game
        self.on_leave_room = on_leave_room
        self.players = []
        self.room_id = ""
        self.max_players = 4
        self._is_host = False
        self.button_zones = {}
        self._start_rect = pygame.Rect(500, 50, 160, 40)
        self._leave_rect = pygame.Rect(500, 100, 160, 40)
    
    def update_players(self, players: list):
        """
        Update the list of players in the lobby.
        
        Args:
            players: List of Player objects
        """
        self.players = players
    
    def set_room_info(self, room_id: str, max_players: int):
        """
        Set room information to display.
        
        Args:
            room_id: ID of the room
            max_players: Maximum players allowed
        """
        self.room_id = room_id
        self.max_players = max_players
    
    def set_is_host(self, is_host: bool):
        """
        Set whether local player is the host.
        
        Args:
            is_host: True if local player hosts
        """
        self._is_host = is_host
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the lobby screen.
        
        Args:
            input_data: Input action dictionary
        """
        return
    
    def render(self, renderer):
        """
        Render the lobby screen.
        
        Args:
            renderer: Renderer instance
        """
        renderer.draw_text("Lobby", (renderer.width//2, 40), font_size=30, color=theme.ACCENT, center=True)
        renderer.draw_text(f"Room: {self.room_id}", (renderer.width//2, 80), font_size=16, color=(200,200,200), center=True)
        # player list box
        box_x = 60
        box_y = 120
        box_w = renderer.width - 140
        box_h = 200
        renderer.draw_rect(theme.BG_MED, (box_x, box_y, box_w, box_h, 8), filled=True)
        y = box_y + 12
        for p in self.players:
            renderer.draw_text(f"{p.get('name')}", (box_x + 18, y), font_size=18, color=(240,240,240))
            y += 32
        # Buttons on right column
        self._leave_rect.topleft = (renderer.width - 200, 60)
        renderer.draw_rect(theme.NEGATIVE, (self._leave_rect.x, self._leave_rect.y, self._leave_rect.width, self._leave_rect.height, 8), filled=True)
        renderer.draw_text("Leave", (self._leave_rect.x + self._leave_rect.width//2, self._leave_rect.y + self._leave_rect.height//2), font_size=16, color=(255,255,255), center=True)
        if self._is_host:
            self._start_rect.topleft = (renderer.width - 200, 120)
            renderer.draw_rect(theme.POSITIVE, (self._start_rect.x, self._start_rect.y, self._start_rect.width, self._start_rect.height, 8), filled=True)
            renderer.draw_text("Start Game", (self._start_rect.x + self._start_rect.width//2, self._start_rect.y + self._start_rect.height//2), font_size=16, color=(255,255,255), center=True)
        # expose button zones
        zones = {"leave_room": self._leave_rect}
        if self._is_host:
            zones["start_game"] = self._start_rect
        self.button_zones = zones
    
    def update(self, delta_time: float):
        """
        Update lobby screen state.
        
        Args:
            delta_time: Time since last frame
        """
        return
