"""
Main Pygame renderer for the client UI.
Manages screen setup, drawing, and frame rendering.
"""

import pygame
from typing import List, Optional
from client.ui import theme


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
        self.width = width
        self.height = height
        self.fps = fps
        self.screen = None
        self._font = None
        self._clock = None
    
    def initialize(self) -> bool:
        """
        Initialize Pygame and create the game window.
        
        Returns:
            True if initialization successful
        """
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Custom UNO")
            # default font loaded from theme
            self._font = pygame.font.SysFont(theme.FONT_NAME, 24)
            self._clock = pygame.time.Clock()
            return True
        except Exception:
            return False
    
    def shutdown(self):
        """Shutdown Pygame and close the window."""
        try:
            pygame.display.quit()
        except Exception:
            pass
    
    def clear_screen(self, color: tuple = (255, 255, 255)):
        """
        Clear the screen with a background color.
        
        Args:
            color: RGB color tuple
        """
        if self.screen:
            self.screen.fill(color)
    
    def update_display(self):
        """Update the display to show the current frame."""
        pygame.display.flip()
    
    def get_events(self) -> List:
        """
        Get all pygame events for this frame.
        
        Returns:
            List of pygame events
        """
        return list(pygame.event.get())
    
    def draw_text(self, text: str, pos: tuple, font_size: int = 24, 
                  color: tuple = (0, 0, 0), center: bool = False):
        """
        Draw text on the screen.
        
        Args:
            text: Text string
            pos: Position (x, y)
            font_size: Font size in pixels
            color: RGB color tuple
        """
        if not self.screen:
            return
        try:
            font = pygame.font.SysFont(theme.FONT_NAME, font_size)
        except Exception:
            font = pygame.font.SysFont(None, font_size)
        surf = font.render(text, True, color)
        if center:
            rect = surf.get_rect(center=pos)
            self.screen.blit(surf, rect.topleft)
        else:
            self.screen.blit(surf, pos)
    
    def draw_image(self, image, pos: tuple, scale: Optional[tuple] = None):
        """
        Draw an image on the screen.
        
        Args:
            image: Pygame surface
            pos: Position (x, y)
            scale: Optional scale tuple (width, height)
        """
        if not self.screen or image is None:
            return
        surf = image
        if scale:
            surf = pygame.transform.smoothscale(image, scale)
        self.screen.blit(surf, pos)

    def draw_ellipse(self, color: tuple, rect: tuple, width: int = 0):
        """Draw an ellipse on the screen."""
        if not self.screen:
            return
        if isinstance(rect, pygame.Rect):
            r = rect
        else:
            r = pygame.Rect(rect)
        pygame.draw.ellipse(self.screen, color, r, width)
    
    def draw_rect(self, color: tuple, rect: tuple, filled: bool = True, width: int = 1):
        """
        Draw a rectangle.
        
        Args:
            color: RGB color tuple
            rect: Rect tuple (x, y, width, height)
            filled: Whether to fill the rectangle
            width: Border width if not filled
        """
        if not self.screen:
            return
        border_radius = 0
        # Accept either a pygame.Rect or a tuple/list (x,y,w,h) optionally with 5th elem border_radius
        if isinstance(rect, pygame.Rect):
            r = rect
        elif isinstance(rect, (tuple, list)):
            if len(rect) >= 4:
                x, y, w, h = rect[0], rect[1], rect[2], rect[3]
                r = pygame.Rect(x, y, w, h)
                if len(rect) >= 5:
                    border_radius = int(rect[4])
            else:
                # fallback: try to create Rect directly (will raise for invalid inputs)
                r = pygame.Rect(rect)
        else:
            r = pygame.Rect(rect)

        if filled:
            pygame.draw.rect(self.screen, color, r, border_radius=border_radius)
        else:
            pygame.draw.rect(self.screen, color, r, width, border_radius=border_radius)
    
    def get_tick(self) -> float:
        """Get the number of milliseconds since initialization."""
        return pygame.time.get_ticks()
    
    def is_running(self) -> bool:
        """Check if the game window is still open."""
        return pygame.display.get_init()
