"""
Chat UI component.
Allows players to communicate during the game.
"""

from typing import Callable, List, Tuple


class ChatBox:
    """
    Chat UI component for player communication.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 on_message_send: Callable):
        """
        Initialize the chat box.
        
        Args:
            x: X position
            y: Y position
            width: Chat box width
            height: Chat box height
            on_message_send: Callback when message is sent
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_message_send = on_message_send
        self.messages: List[Tuple[str, str]] = []
        self.input_text: str = ""
        self.visible = True
        import pygame
        self._input_rect = pygame.Rect(x + 4, y + height - 30, width - 8, 26)
    
    def add_message(self, sender: str, text: str):
        """
        Add a message to the chat display.
        
        Args:
            sender: Name of message sender
            text: Message text
        """
        self.messages.append((sender, text))
        # keep last 20 messages
        self.messages = self.messages[-20:]
    
    def clear_messages(self):
        """Clear all messages from the chat."""
        self.messages.clear()
    
    def set_input_text(self, text: str):
        """
        Set the input field text.
        
        Args:
            text: New input text
        """
        self.input_text = text
    
    def get_input_text(self) -> str:
        """Get the current input field text."""
        return self.input_text
    
    def submit_message(self):
        """Process and submit the current input message."""
        if not self.input_text.strip():
            return
        try:
            self.on_message_send(self.input_text.strip())
        except Exception:
            pass
        self.input_text = ""
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the chat box (text entry, send).
        
        Args:
            input_data: Input action dictionary
        """
        # Expecting simple dicts: {"type": "text", "text": "..."} or {"type": "submit"}
        t = input_data.get("type")
        if t == "text":
            self.input_text = input_data.get("text", "")
        elif t == "submit":
            self.submit_message()
    
    def is_focused(self) -> bool:
        """Check if the input field is focused."""
        return False
    
    def set_visible(self, visible: bool):
        """
        Show or hide the chat box.
        
        Args:
            visible: True to show
        """
        self.visible = visible
    
    def render(self, renderer):
        """
        Render the chat box.
        
        Args:
            renderer: Renderer instance
        """
        if not self.visible:
            return
        # background
        renderer.draw_rect((40, 40, 40), (self.x, self.y, self.width, self.height), filled=True)
        # messages
        y = self.y + 6
        for sender, text in self.messages[-10:]:
            renderer.draw_text(f"{sender}: {text}", (self.x + 6, y), font_size=16, color=(220, 220, 220))
            y += 18
        # input box
        renderer.draw_rect((255, 255, 255), (self._input_rect.x, self._input_rect.y, self._input_rect.w, self._input_rect.h), filled=True)
        renderer.draw_text(self.input_text, (self._input_rect.x + 4, self._input_rect.y + 2), font_size=16, color=(0, 0, 0))
    
    def update(self, delta_time: float):
        """
        Update chat state.
        
        Args:
            delta_time: Time since last frame
        """
        return
