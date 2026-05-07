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
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.on_click = on_click
        self.enabled = True
        self._hover = False
        import pygame
        self._rect = pygame.Rect(x, y, width, height)
    
    def set_position(self, x: int, y: int):
        """
        Set button position.
        
        Args:
            x: X position
            y: Y position
        """
        self.x = x
        self.y = y
        import pygame
        self._rect.topleft = (x, y)
    
    def set_text(self, text: str):
        """
        Set button text.
        
        Args:
            text: New text label
        """
        self.text = text
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable the button.
        
        Args:
            enabled: True to enable
        """
        self.enabled = enabled
    
    def is_mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Check if mouse is over the button.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if mouse is over button
        """
        return self._rect.collidepoint(mouse_pos)
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Handle click event at mouse position.
        
        Args:
            mouse_pos: Mouse position (x, y)
            
        Returns:
            True if click was on button
        """
        if not self.enabled:
            return False
        if self.is_mouse_over(mouse_pos):
            try:
                self.on_click()
            except Exception:
                pass
            return True
        return False
    
    def render(self, renderer):
        """
        Render the button.
        
        Args:
            renderer: Renderer instance
        """
        bg = (70, 130, 180) if self.enabled else (100, 100, 100)
        mouse_pos = None
        try:
            import pygame
            mouse_pos = pygame.mouse.get_pos()
        except Exception:
            mouse_pos = (0, 0)
        self._hover = self.is_mouse_over(mouse_pos)
        color = tuple(min(255, c + 30) for c in bg) if self._hover and self.enabled else bg
        # shadow
        renderer.draw_rect((0,0,0), (self.x+2, self.y+4, self.width, self.height, 8), filled=True)
        renderer.draw_rect(color, (self.x, self.y, self.width, self.height, 8), filled=True)
        # centered text
        renderer.draw_text(self.text, (self.x + self.width//2, self.y + self.height//2), font_size=20, color=(255, 255, 255), center=True)
    
    def update(self, delta_time: float):
        """
        Update button state (e.g., hover effects).
        
        Args:
            delta_time: Time since last frame
        """
        return
