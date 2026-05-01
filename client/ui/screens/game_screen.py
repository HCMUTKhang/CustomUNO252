"""
Game screen.
Displays the game board, players' cards, discard/draw piles, and action buttons.
"""

from typing import Callable, Optional
from shared.data_structures import Card, Player
from shared.enums import GameState


class GameScreen:
    """
    Game play UI screen.
    Displays game board, hand, and handles game interactions.
    """
    
    def __init__(self, on_play_card: Callable, on_draw_card: Callable, 
                 on_uno_click: Callable):
        """
        Initialize the game screen.
        
        Args:
            on_play_card: Callback when card is played
            on_draw_card: Callback when draw pile is clicked
            on_uno_click: Callback when UNO button is clicked
        """
        pass
    
    def update_game_state(self, state_data: dict):
        """
        Update game state from server.
        
        Args:
            state_data: Game state dictionary from server
        """
        pass
    
    def update_players(self, players: list):
        """
        Update player information display.
        
        Args:
            players: List of Player objects
        """
        pass
    
    def update_hand(self, cards: list):
        """
        Update the local player's hand display.
        
        Args:
            cards: List of Card objects
        """
        pass
    
    def set_current_player(self, player_id: int):
        """
        Highlight whose turn it is.
        
        Args:
            player_id: ID of current player
        """
        pass
    
    def set_last_card_played(self, card: Optional[Card]):
        """
        Update the display of the last played card.
        
        Args:
            card: Card object or None
        """
        pass
    
    def enable_player_input(self, enabled: bool):
        """
        Enable/disable input based on turn state.
        
        Args:
            enabled: True to enable input
        """
        pass
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the game screen.
        
        Args:
            input_data: Input action dictionary
        """
        pass
    
    def render(self, renderer):
        """
        Render the game screen.
        
        Args:
            renderer: Renderer instance
        """
        pass
    
    def update(self, delta_time: float):
        """
        Update game screen state.
        
        Args:
            delta_time: Time since last frame
        """
        pass
