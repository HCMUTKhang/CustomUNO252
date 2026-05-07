"""
Main menu screen.
Allows player to start a game or join an existing game room.
"""

from typing import Callable, Optional
import pygame
from client.ui import theme
from shared.constants import DEFAULT_HOST


class MenuScreen:
    """
    Main menu UI screen.
    Displays options to host or join a game.
    """

    def __init__(self, on_host_click: Callable, on_join_click: Callable):
        self.on_host_click = on_host_click
        self.on_join_click = on_join_click
        self.button_zones = {}

        self._host_rect = pygame.Rect(0, 0, 200, 50)
        self._join_rect = pygame.Rect(0, 0, 200, 50)

        # Text input fields
        self._name_text = "Player"
        self._ip_text = DEFAULT_HOST
        self._active_field: Optional[str] = None  # "name" | "ip" | None
        self._name_rect = pygame.Rect(0, 0, 280, 38)
        self._ip_rect = pygame.Rect(0, 0, 280, 38)

    # ------------------------------------------------------------------
    # Public getters used by InputHandler / GameClient
    # ------------------------------------------------------------------

    def get_player_name(self) -> str:
        return self._name_text.strip() or "Player"

    def get_server_ip(self) -> str:
        return self._ip_text.strip() or DEFAULT_HOST

    # ------------------------------------------------------------------
    # Event handling (called directly by GameClient for KEYDOWN events)
    # ------------------------------------------------------------------

    def handle_pygame_event(self, event: pygame.event.Event):
        """Forward raw pygame events so text fields can capture keyboard input."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._name_rect.collidepoint(pos):
                self._active_field = "name"
            elif self._ip_rect.collidepoint(pos):
                self._active_field = "ip"
            else:
                self._active_field = None

        elif event.type == pygame.KEYDOWN and self._active_field:
            if event.key == pygame.K_BACKSPACE:
                if self._active_field == "name":
                    self._name_text = self._name_text[:-1]
                else:
                    self._ip_text = self._ip_text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                self._active_field = None
            elif event.unicode and len(event.unicode) == 1:
                if self._active_field == "name" and len(self._name_text) < 20:
                    self._name_text += event.unicode
                elif self._active_field == "ip" and len(self._ip_text) < 40:
                    self._ip_text += event.unicode

    def handle_input(self, input_data: dict):
        return

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, renderer):
        renderer.draw_rect(theme.BG_DARK, (0, 0, renderer.width, renderer.height), filled=True)
        renderer.draw_text("Custom UNO", (renderer.width // 2, 80), font_size=40, color=theme.ACCENT, center=True)

        cx = renderer.width // 2
        # Name field
        self._name_rect.topleft = (cx - 140, 160)
        self._ip_rect.topleft = (cx - 140, 220)
        self._host_rect.topleft = (cx - 100, 290)
        self._join_rect.topleft = (cx - 100, 360)

        self._draw_field(renderer, self._name_rect, "Name: " + self._name_text,
                         active=self._active_field == "name")
        self._draw_field(renderer, self._ip_rect, "Server IP: " + self._ip_text,
                         active=self._active_field == "ip")

        renderer.draw_rect(theme.PRIMARY,
                           (self._host_rect.x, self._host_rect.y,
                            self._host_rect.width, self._host_rect.height, 10), filled=True)
        renderer.draw_rect(theme.PRIMARY,
                           (self._join_rect.x, self._join_rect.y,
                            self._join_rect.width, self._join_rect.height, 10), filled=True)
        renderer.draw_text("Host Game",
                           (self._host_rect.x + self._host_rect.width // 2,
                            self._host_rect.y + self._host_rect.height // 2),
                           font_size=22, color=(255, 255, 255), center=True)
        renderer.draw_text("Join Game",
                           (self._join_rect.x + self._join_rect.width // 2,
                            self._join_rect.y + self._join_rect.height // 2),
                           font_size=22, color=(255, 255, 255), center=True)

        self.button_zones = {
            "host_game": self._host_rect,
            "join_game": self._join_rect,
        }

    def _draw_field(self, renderer, rect: pygame.Rect, text: str, active: bool):
        border_color = theme.ACCENT if active else (100, 100, 120)
        renderer.draw_rect((30, 30, 50), (rect.x, rect.y, rect.width, rect.height, 6), filled=True)
        surf = renderer.screen
        pygame.draw.rect(surf, border_color, rect, 2, border_radius=6)
        font = pygame.font.SysFont(None, 22)
        label = font.render(text, True, (220, 220, 220))
        surf.blit(label, (rect.x + 8, rect.y + 10))

    # ------------------------------------------------------------------

    def update(self, delta_time: float):
        return
