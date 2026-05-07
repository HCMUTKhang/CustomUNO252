"""
Main menu screen.
Allows player to start a game or join an existing game room.
"""

from typing import Callable, Optional
import pygame
from client.ui import theme


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
        self.on_host_click = on_host_click
        self.on_join_click = on_join_click
        self.button_zones = {}
        # simple layout
        self._host_rect = pygame.Rect(100, 200, 200, 50)
        self._join_rect = pygame.Rect(100, 270, 200, 50)
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the menu screen.
        
        Args:
            input_data: Input action dictionary
        """
        # input_data handled by InputHandler via GameClient action mapping
        return
    
    def render(self, renderer):
        """
        Render the menu screen.
        
        Args:
            renderer: Renderer instance
        """
        # Background
        renderer.draw_rect(theme.BG_DARK, (0, 0, renderer.width, renderer.height), filled=True)
        # Title centered
        renderer.draw_text("Custom UNO", (renderer.width//2, 80), font_size=40, color=theme.ACCENT, center=True)
        # Buttons centered horizontally
        host_x = renderer.width//2 - 120
        join_x = renderer.width//2 - 120
        self._host_rect.topleft = (host_x, 220)
        self._join_rect.topleft = (join_x, 300)
        renderer.draw_rect(theme.PRIMARY, (self._host_rect.x, self._host_rect.y, self._host_rect.width, self._host_rect.height, 10), filled=True)
        renderer.draw_rect(theme.PRIMARY, (self._join_rect.x, self._join_rect.y, self._join_rect.width, self._join_rect.height, 10), filled=True)
        renderer.draw_text("Host Game", (self._host_rect.x + self._host_rect.width//2, self._host_rect.y + self._host_rect.height//2), font_size=22, color=(255,255,255), center=True)
        renderer.draw_text("Join Game", (self._join_rect.x + self._join_rect.width//2, self._join_rect.y + self._join_rect.height//2), font_size=22, color=(255,255,255), center=True)
        # expose button zones for InputHandler
        self.button_zones = {
            "host_game": self._host_rect,
            "join_game": self._join_rect,
        }
    
    def update(self, delta_time: float):
        """
        Update menu screen state (e.g., animations).
        
        Args:
            delta_time: Time since last frame
        """
        return
