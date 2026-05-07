"""
Card display UI component.
Renders individual UNO cards with visual styling.
"""

from typing import Callable, Optional, Tuple
from shared.data_structures import Card
import pygame
from client.ui import theme


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
        self.card = card
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_click = on_click
        self.selected = False
        self._rect = pygame.Rect(x, y, width, height)
        # animation state
        self._current_offset_y = 0.0
        self._target_offset_y = 0.0
        self._lift_amount = -18  # pixels to lift on hover
        self._lerp_speed = 10.0  # higher is snappier
        # click flash
        self._flash_timer = 0.0
        self._flash_duration = 0.12
    
    def set_card(self, card: Card):
        """
        Update the card being displayed.
        
        Args:
            card: New card to display
        """
        self.card = card
    
    def set_position(self, x: int, y: int):
        """
        Set card position.
        
        Args:
            x: X position
            y: Y position
        """
        self.x = x
        self.y = y
        self._rect.topleft = (x, y)
    
    def set_selected(self, selected: bool):
        """
        Highlight card as selected.
        
        Args:
            selected: True to select
        """
        self.selected = selected
        # treat selected as a stronger lift
        self._target_offset_y = self._lift_amount if selected else 0.0
    
    def is_mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Check if mouse is over the card.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if mouse is over card
        """
        return self._rect.collidepoint(mouse_pos)
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle click event at mouse position.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if click was on card
        """
        if self.is_mouse_over(mouse_pos):
            if self.on_click:
                try:
                    self.on_click(self.card)
                except Exception:
                    pass
            # trigger flash effect
            self._flash_timer = self._flash_duration
            return True
        return False
    
    def render(self, renderer):
        """
        Render the card display.
        
        Args:
            renderer: Renderer instance
        """
        # compose drawing position with animation offset
        draw_x = int(self.x)
        draw_y = int(self.y + self._current_offset_y)

        # Improved card rendering: color strip + big centered value
        # determine card color
        try:
            color_map = {
                'red': (200, 70, 70),
                'green': (80, 170, 90),
                'blue': (34, 108, 179),
                'yellow': (230, 200, 70),
                'wild': (30, 30, 30),
            }
            card_color = getattr(self.card.color, 'value', str(self.card.color)).lower()
            rgb = color_map.get(card_color, (160, 160, 160))
        except Exception:
            rgb = (160, 160, 160)

        # outer white border/background
        renderer.draw_rect((255,255,255), (draw_x, draw_y, self.width, self.height, 8), filled=False, width=6)

        # inner colored panel inset
        inset = 6
        inner_rect = (draw_x + inset, draw_y + inset, self.width - inset*2, self.height - inset*2, 6)
        renderer.draw_rect(rgb, inner_rect, filled=True)

        # stylized white swash: draw an ellipse overlapping center to mimic curved white area
        ell_w = int(self.width * 0.9)
        ell_h = int(self.height * 0.5)
        ell_x = draw_x + (self.width - ell_w)//2
        ell_y = draw_y + int(self.height * 0.22)
        try:
            renderer.draw_ellipse((255,255,255), (ell_x, ell_y, ell_w, ell_h))
        except Exception:
            # fallback: draw rounded rect for swash
            renderer.draw_rect((255,255,255), (ell_x, ell_y, ell_w, ell_h, 20), filled=True)

        # value text centered on card; use card's color for number for contrast
        text = f"{getattr(self.card.value, 'value', str(self.card.value))}"
        # text color: use darker if card is light (yellow)
        text_color = (10,10,10) if card_color == 'yellow' else (255,255,255)
        renderer.draw_text(text, (draw_x + self.width//2, draw_y + int(self.height * 0.55)), font_size=24, color=text_color, center=True)

        # small corner value in top-left
        try:
            corner_text = str(getattr(self.card.value, 'value', str(self.card.value)))[:2]
            renderer.draw_text(corner_text, (draw_x + 10, draw_y + 6), font_size=14, color=text_color, center=False)
        except Exception:
            pass

        # click flash overlay (white fade)
        if self._flash_timer > 0:
            alpha = int(180 * (self._flash_timer / self._flash_duration))
            renderer.draw_rect((255, 255, 255, alpha), (draw_x, draw_y, self.width, self.height, 8), filled=True)
    
    def update(self, delta_time: float):
        """
        Update card display state (e.g., animations).
        
        Args:
            delta_time: Time since last frame
        """
        # simple eased interpolation towards target offset
        diff = self._target_offset_y - self._current_offset_y
        step = diff * min(1.0, self._lerp_speed * delta_time)
        self._current_offset_y += step

        # update rect position to reflect visual offset for hit-testing
        self._rect.topleft = (int(self.x), int(self.y + self._current_offset_y))

        # flash timer
        if self._flash_timer > 0:
            self._flash_timer = max(0.0, self._flash_timer - delta_time)
