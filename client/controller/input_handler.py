"""
Input handler for capturing player interactions (mouse and keyboard).
Translates raw Pygame events into semantic game actions via callback.

Design: M3 registers clickable zones each frame via update_*_zones().
InputHandler checks those zones on mouse click and fires action_callback.
This keeps layout knowledge in M3 and click logic in M4.
"""

import pygame
from typing import Optional, Tuple, Callable, List, Dict
from enum import Enum
from shared.enums import CardColor, TurnDirection
from shared.message_protocol import CardDTO


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
    Converts pygame events into semantic game actions and fires action_callback.

    Clickable zone registration (called by M3 each render frame):
        update_card_zones(zones)        - list of (pygame.Rect, CardDTO)
        update_button_zones(zones)      - dict of name -> pygame.Rect
        update_color_zones(zones)       - list of (pygame.Rect, CardColor)
        update_target_zones(zones)      - list of (pygame.Rect, player_id)
        update_direction_zones(zones)   - list of (pygame.Rect, TurnDirection)

    action_callback signature: (action_type: str, action_data: dict) -> None
    """

    def __init__(self, action_callback: Callable):
        self._callback: Callable = action_callback

        # Mouse state
        self._mouse_pos: Tuple[int, int] = (0, 0)
        self._hover_card_index: Optional[int] = None

        # Clickable zones registered by M3 each frame
        # Each zone list is replaced entirely on every register call
        self._card_zones: List[Tuple[pygame.Rect, CardDTO]] = []
        self._button_zones: Dict[str, pygame.Rect] = {}
        self._color_zones: List[Tuple[pygame.Rect, CardColor]] = []
        self._target_zones: List[Tuple[pygame.Rect, int]] = []          # (rect, player_id)
        self._direction_zones: List[Tuple[pygame.Rect, TurnDirection]] = []

        # Whether the local player may interact right now
        self._input_enabled: bool = True

    # ------------------------------------------------------------------
    # Zone registration (called by M3 after each render pass)
    # ------------------------------------------------------------------

    def update_card_zones(self, zones: List[Tuple[pygame.Rect, CardDTO]]):
        """Register card bounding boxes. zones[i] = (rect, card_dto)."""
        self._card_zones = zones

    def update_button_zones(self, zones: Dict[str, pygame.Rect]):
        """
        Register named button zones.
        Expected keys: "draw_pile", "reaction_btn", "start_game", "leave_room"
        """
        self._button_zones = zones

    def update_color_zones(self, zones: List[Tuple[pygame.Rect, CardColor]]):
        """Register color-picker buttons for Wild / Wild+4 flow."""
        self._color_zones = zones

    def update_target_zones(self, zones: List[Tuple[pygame.Rect, int]]):
        """Register target-player buttons for Rule-7 swap flow."""
        self._target_zones = zones

    def update_direction_zones(self, zones: List[Tuple[pygame.Rect, TurnDirection]]):
        """Register direction buttons for Rule-0 flow."""
        self._direction_zones = zones

    def set_input_enabled(self, enabled: bool):
        """Block or unblock player interaction (e.g. when not their turn)."""
        self._input_enabled = enabled

    # ------------------------------------------------------------------
    # Main event loop
    # ------------------------------------------------------------------

    def process_events(self, events: list):
        """
        Process a list of pygame events for this frame.

        Args:
            events: List of pygame events from pygame.event.get()
        """
        for event in events:
            if event.type == pygame.QUIT:
                self._callback("quit", {})

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_click(event.pos, event.button)

            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)

            elif event.type == pygame.KEYDOWN:
                self.handle_key_press(event.key)

    def handle_mouse_click(self, pos: Tuple[int, int], button: int):
        """
        Hit-test registered zones in priority order and fire the matching action.

        Args:
            pos: Mouse position (x, y)
            button: Mouse button (1 = left)
        """
        if button != 1:
            return

        # Always allow quit — other actions require input enabled
        if not self._input_enabled:
            return

        # 1. Color selection overlay (highest priority when pending)
        for rect, color in self._color_zones:
            if rect.collidepoint(pos):
                self._callback("color_chosen", {"color": color})
                return

        # 2. Target player selection overlay
        for rect, player_id in self._target_zones:
            if rect.collidepoint(pos):
                self._callback("target_chosen", {"player_id": player_id})
                return

        # 3. Direction selection overlay
        for rect, direction in self._direction_zones:
            if rect.collidepoint(pos):
                self._callback("direction_chosen", {"direction": direction})
                return

        # 4. Named buttons
        if "reaction_btn" in self._button_zones:
            if self._button_zones["reaction_btn"].collidepoint(pos):
                self._callback("react_rule8", {})
                return

        if "draw_pile" in self._button_zones:
            if self._button_zones["draw_pile"].collidepoint(pos):
                self._callback("draw_card", {})
                return

        if "start_game" in self._button_zones:
            if self._button_zones["start_game"].collidepoint(pos):
                self._callback("start_game", {})
                return

        if "leave_room" in self._button_zones:
            if self._button_zones["leave_room"].collidepoint(pos):
                self._callback("leave_room", {})
                return

        if "host_game" in self._button_zones:
            if self._button_zones["host_game"].collidepoint(pos):
                self._callback("host_game", {})
                return

        if "join_game" in self._button_zones:
            if self._button_zones["join_game"].collidepoint(pos):
                self._callback("join_game", {})
                return

        # 5. Card in hand
        for i, (rect, card_dto) in enumerate(self._card_zones):
            if rect.collidepoint(pos):
                self._callback("card_clicked", {"card_index": i, "card": card_dto})
                return

    def handle_key_press(self, key: int):
        """
        Handle keyboard input.

        Args:
            key: pygame key constant
        """
        if key == pygame.K_ESCAPE:
            self._callback("escape", {})
        elif key == pygame.K_SPACE:
            # Spacebar as shortcut for reaction button
            self._callback("react_rule8", {})

    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """
        Track mouse position and update hover card index.

        Args:
            pos: Mouse position (x, y)
        """
        self._mouse_pos = pos
        prev_hover = self._hover_card_index
        self._hover_card_index = None

        for i, (rect, _) in enumerate(self._card_zones):
            if rect.collidepoint(pos):
                self._hover_card_index = i
                break

        # Notify M3 only when hover changes
        if self._hover_card_index != prev_hover:
            self._callback("hover_changed", {"card_index": self._hover_card_index})

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return self._mouse_pos

    def get_hover_card_index(self) -> Optional[int]:
        """Return the index of the card currently under the mouse, or None."""
        return self._hover_card_index
