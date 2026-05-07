"""
Game screen.
Displays the game board, players' cards, discard/draw piles, and action buttons.
"""

from typing import Callable, Optional
from shared.data_structures import Card, Player
from shared.enums import GameState
import pygame
from shared.message_protocol import CardDTO
from client.ui.components.card_display import CardDisplay
from client.ui import theme


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
        self.on_play_card = on_play_card
        self.on_draw_card = on_draw_card
        self.on_uno_click = on_uno_click
        self.players = []
        self.hand: list[Card] = []
        self.current_player_id = None
        self.last_card_played: Optional[Card] = None
        self.input_enabled = True
        self.button_zones = {}
        self.card_zones = []  # list of (rect, CardDTO)
        self._card_displays: list[CardDisplay] = []
        # layout
        self._draw_rect = pygame.Rect(50, 50, 80, 120)
        self._reaction_rect = pygame.Rect(150, 50, 140, 40)
        self._discard_rect = pygame.Rect(150, 200, 80, 120)
        self._uno_rect = pygame.Rect(50, 420, 120, 40)
    
    def update_game_state(self, state_data: dict):
        """
        Update game state from server.
        
        Args:
            state_data: Game state dictionary from server
        """
        return
    
    def update_players(self, players: list):
        """
        Update player information display.
        
        Args:
            players: List of Player objects
        """
        self.players = players
    
    def update_hand(self, cards: list):
        """
        Update the local player's hand display.
        
        Args:
            cards: List of Card objects
        """
        self.hand = cards
        # rebuild CardDisplay instances for hand
        self._card_displays = []
        # layout constants kept in sync with render()
        card_w, card_h = 72, 108
        max_visible = min(len(self.hand), 12)
        total_w = card_w + (max_visible-1) * 28
        start_x = max(60, (800 - total_w)//2)  # fallback width; renderer will reposition in render pass
        hand_y = 640 - 140
        for i, card in enumerate(self.hand[:max_visible]):
            x = start_x + i * 28
            cd = CardDisplay(card, x, hand_y, card_w, card_h, on_click=None)
            self._card_displays.append(cd)
    
    def set_current_player(self, player_id: int):
        """
        Highlight whose turn it is.
        
        Args:
            player_id: ID of current player
        """
        self.current_player_id = player_id
    
    def set_last_card_played(self, card: Optional[Card]):
        """
        Update the display of the last played card.
        
        Args:
            card: Card object or None
        """
        self.last_card_played = card
    
    def enable_player_input(self, enabled: bool):
        """
        Enable/disable input based on turn state.
        
        Args:
            enabled: True to enable input
        """
        self.input_enabled = enabled
    
    def handle_input(self, input_data: dict):
        """
        Handle input for the game screen.
        
        Args:
            input_data: Input action dictionary
        """
        # handle hover feedback and click visuals
        card_index = input_data.get("card_index")
        if "card_index" in input_data:
            # update target offsets on displays
            for i, cd in enumerate(self._card_displays):
                cd._target_offset_y = cd._lift_amount if (card_index is not None and i == card_index) else 0.0
        # card clicked visual (main forwards card click action_data here)
        if "card_clicked_index" in input_data:
            idx = input_data.get("card_clicked_index")
            if idx is not None and 0 <= idx < len(self._card_displays):
                self._card_displays[idx]._flash_timer = self._card_displays[idx]._flash_duration
        return
    
    def render(self, renderer):
        """
        Render the game screen.
        
        Args:
            renderer: Renderer instance
        """
        # Title
        renderer.draw_text("UNO Table", (renderer.width//2, 24), font_size=28, color=theme.ACCENT, center=True)

        # Top: opponent hand strip
        top_h = 96
        renderer.draw_text("Player 2", (renderer.width - 120, 20), font_size=18, color=(220,220,220), center=False)
        opp_x = 40
        opp_y = 40
        opp_card_w, opp_card_h = 56, 84
        opp_gap = 8
        # draw sample opponent cards
        for i in range(min(8, max(0, len(self.players) and 8))):
            cx = opp_x + i * (opp_card_w + opp_gap)
            renderer.draw_rect((255,255,255), (cx, opp_y, opp_card_w, opp_card_h, 6), filled=False, width=3)
            renderer.draw_rect((60,120,200), (cx+4, opp_y+4, opp_card_w-8, opp_card_h-8, 6), filled=True)

        # Center: play area with big discard preview
        center_h = 220
        center_y = 140
        renderer.draw_rect((40,70,120), (40, center_y, renderer.width - 320, center_h, 8), filled=True)
        # draw big discard card in middle
        mid_x = 40 + (renderer.width - 320)//2 - 48
        mid_y = center_y + center_h//2 - 72//2
        # use last_card_played if available
        if self.last_card_played:
            cd = CardDisplay(self.last_card_played, mid_x, mid_y, 96, 144)
            cd.render(renderer)
        else:
            renderer.draw_rect((200,200,200), (mid_x, mid_y, 96, 144, 8), filled=True)

        # Right panel: current player and buttons
        panel_x = renderer.width - 240
        renderer.draw_text(f"Player 1", (panel_x + 100, 40), font_size=18, color=(255,255,255), center=True)
        renderer.draw_text("Player 1's turn", (panel_x + 100, 90), font_size=20, color=theme.ACCENT, center=True)
        # Draw buttons
        b_w, b_h = 100, 40
        renderer.draw_rect(theme.PRIMARY, (panel_x + 60, 140, b_w, b_h, 8), filled=True)
        renderer.draw_text("Draw", (panel_x + 60 + b_w//2, 140 + b_h//2), font_size=16, color=(255,255,255), center=True)
        renderer.draw_rect(theme.NEGATIVE, (panel_x + 60, 200, b_w, b_h, 8), filled=True)
        renderer.draw_text("Say UNO", (panel_x + 60 + b_w//2, 200 + b_h//2), font_size=16, color=(255,255,255), center=True)

        # render hand via CardDisplay instances (animated)
        self.card_zones = []
        max_visible = min(len(self.hand), 12)
        card_w, card_h = 72, 108
        total_w = card_w + (max_visible-1) * 28
        start_x = max(60, (renderer.width - total_w)//2)
        hand_y = renderer.height - 140
        # ensure displays are positioned based on current renderer width
        for i, cd in enumerate(self._card_displays[:max_visible]):
            x = start_x + i * 28
            cd.x = x
            cd.y = hand_y
            cd._rect.width = card_w
            cd._rect.height = card_h
            cd.width = card_w
            cd.height = card_h
            cd.render(renderer)
            dto = CardDTO(color=cd.card.color, value=cd.card.value)
            self.card_zones.append((cd._rect.copy(), dto))

        # expose button zones for InputHandler
        zones = {
            "draw_pile": self._draw_rect,
            "reaction_btn": self._reaction_rect,
        }
        self.button_zones = zones
    
    def update(self, delta_time: float):
        """
        Update game screen state.
        
        Args:
            delta_time: Time since last frame
        """
        # advance animations on card displays
        for cd in getattr(self, '_card_displays', []):
            try:
                cd.update(delta_time)
            except Exception:
                pass
