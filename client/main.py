"""
Client main entry point.
Initializes the client, manages the game loop, and orchestrates all subsystems.

Screen flow:  menu → lobby → game (→ game_over overlay)
"""

import pygame
import threading
import time
from typing import Optional

from client.ui.renderer import Renderer
from client.controller.input_handler import InputHandler
from client.controller.network_client import NetworkClient
from client.state.game_state import GameStateManager
from client.ui.screens.menu_screen import MenuScreen
from client.ui.screens.lobby_screen import LobbyScreen
from client.ui.screens.game_screen import GameScreen
from shared.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_HOST, DEFAULT_PORT,
    MAX_PLAYERS, REACTION_EVENT_TIMEOUT,
)
from shared.enums import GameState, CardValue, MessageType
from shared.message_protocol import (
    JoinRoom, StartGame, PlayCard, DrawCard, Rule8Reaction, CardDTO,
)


class GameClient:
    """
    Main client orchestrator.
    Manages rendering, input, networking, and UI state.
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self._default_host = host
        self._default_port = port

        # Subsystems (created in initialize())
        self.renderer: Optional[Renderer] = None
        self.state: Optional[GameStateManager] = None
        self.input_handler: Optional[InputHandler] = None
        self.network: Optional[NetworkClient] = None

        # Screens
        self.menu_screen: Optional[MenuScreen] = None
        self.lobby_screen: Optional[LobbyScreen] = None
        self.game_screen: Optional[GameScreen] = None

        # Active screen key: "menu" | "lobby" | "game" | "game_over"
        self._screen: str = "menu"

        self._player_name: str = "Player"
        self._running: bool = False
        self._clock: Optional[pygame.time.Clock] = None
        self._fps: int = 60

        # Background server thread (only set when this client is the host)
        self._server_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """
        Initialize all client subsystems.

        Returns:
            True if initialization successful
        """
        pygame.init()
        self._clock = pygame.time.Clock()

        self.renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT, self._fps)
        if not self.renderer.initialize():
            print("[CLIENT] Failed to initialize renderer")
            return False

        self.state = GameStateManager()
        self.input_handler = InputHandler(action_callback=self._on_input_action)

        # Screens receive callbacks into GameClient so M3 never touches network/state
        self.menu_screen = MenuScreen(
            on_host_click=self._on_host_click,
            on_join_click=self._on_join_click,
        )
        self.input_handler.set_menu_getters(
            name_getter=self.menu_screen.get_player_name,
            ip_getter=self.menu_screen.get_server_ip,
        )
        self.lobby_screen = LobbyScreen(
            on_start_game=self._on_start_game,
            on_leave_room=self._on_leave_room,
        )
        self.game_screen = GameScreen(
            on_play_card=self._on_play_card,
            on_draw_card=self._on_draw_card,
            on_uno_click=self._on_uno_click,
        )
        return True

    def run(self):
        """Main game loop. Runs until window is closed."""
        if not self.initialize():
            return

        self._running = True
        while self._running and self.renderer.is_running():
            delta_ms = self._clock.tick(self._fps)
            delta_time = delta_ms / 1000.0

            # 1. Collect and dispatch pygame events
            events = self.renderer.get_events()
            if self._screen == "menu" and self.menu_screen:
                for event in events:
                    self.menu_screen.handle_pygame_event(event)
            self.input_handler.process_events(events)

            # 2. Drain server message queue
            if self.network and self.network.is_connected():
                for msg in self.network.get_messages():
                    self.handle_server_message(msg)

            # 3. Game logic update
            self.update(delta_time)

            # 4. Render
            self.render()

        self.shutdown()

    def update(self, delta_time: float):
        """
        Update game state and logic.

        Args:
            delta_time: Time since last frame in seconds
        """
        # Tick the Rule-8 countdown every frame
        if self.state.is_rule8_active():
            remaining = self.state.update_rule8_timer()
            # If time expired and we never reacted, server will penalise us.
            # Nothing extra needed client-side; server is authoritative.
            _ = remaining

        screen = self._active_screen()
        if screen:
            screen.update(delta_time)

    def render(self):
        """Render the current frame."""
        self.renderer.clear_screen((30, 30, 50))
        screen = self._active_screen()
        if screen:
            screen.render(self.renderer)
            # Register clickable zones with InputHandler if provided by screen
            if self.input_handler:
                if hasattr(screen, 'button_zones'):
                    self.input_handler.update_button_zones(getattr(screen, 'button_zones') or {})
                if hasattr(screen, 'card_zones'):
                    self.input_handler.update_card_zones(getattr(screen, 'card_zones') or [])
                if hasattr(screen, 'color_zones'):
                    self.input_handler.update_color_zones(getattr(screen, 'color_zones') or [])
                if hasattr(screen, 'target_zones'):
                    self.input_handler.update_target_zones(getattr(screen, 'target_zones') or [])
                if hasattr(screen, 'direction_zones'):
                    self.input_handler.update_direction_zones(getattr(screen, 'direction_zones') or [])
        self.renderer.update_display()

    def shutdown(self):
        """Shutdown all client subsystems."""
        print("[CLIENT] Shutting down...")
        self.disconnect_from_server()
        if self.renderer:
            self.renderer.shutdown()
        pygame.quit()

    # ------------------------------------------------------------------
    # Server message handling
    # ------------------------------------------------------------------

    def handle_server_message(self, message):
        """
        Handle incoming message from server.

        Args:
            message: NetworkMessage from server
        """
        msg_type = message.message_type

        if msg_type == MessageType.GAME_STATE_UPDATE:
            state_dict = message.to_dict()
            self.state.update_game_state(state_dict)
            self._sync_game_screen()

        elif msg_type == MessageType.EVENT_BROADCAST:
            self._handle_event_broadcast(message.event_name, message.event_data)

        elif msg_type == MessageType.ERROR_MESSAGE:
            print(f"[CLIENT] Server error [{message.error_type}]: {message.message}")

    def _handle_event_broadcast(self, event_name: str, event_data: dict):
        self.state.handle_event(event_name, event_data)

        if event_name == "LOBBY_UPDATE":
            self._screen = "lobby"
            if self.lobby_screen:
                self.lobby_screen.update_players(self.state.get_lobby_players())
                self.lobby_screen.set_room_info(
                    room_id=str(self.state.get_host_client_id() or ""),
                    max_players=MAX_PLAYERS,
                )
                self.lobby_screen.set_is_host(self.state.is_host())

        elif event_name == "GAME_STARTING":
            self._screen = "game"

        elif event_name == "RULE_8_STARTED":
            print(f"[CLIENT] Rule 8 event! React within {event_data.get('timeout', REACTION_EVENT_TIMEOUT)}s")

        elif event_name == "RULE_8_RESOLVED":
            print("[CLIENT] Rule 8 resolved")

        elif event_name == "GAME_OVER":
            winner = event_data.get("winner_name", "Unknown")
            print(f"[CLIENT] Game over — winner: {winner}")
            self._screen = "game_over"

    def _sync_game_screen(self):
        """Push latest state to the game screen so M3 can render it."""
        if self.game_screen is None:
            return
        self.game_screen.update_hand(self.state.get_local_hand())
        self.game_screen.set_current_player(self.state.get_current_player_id())
        self.game_screen.set_last_card_played(self.state.get_last_card_played())
        self.game_screen.enable_player_input(self.state.is_local_player_turn())

    # ------------------------------------------------------------------
    # Input action dispatcher (receives semantic actions from InputHandler)
    # ------------------------------------------------------------------

    def _on_input_action(self, action_type: str, action_data: dict):
        self.handle_input_action(action_type, action_data)

    def handle_input_action(self, action_type: str, action_data: dict):
        """
        Handle local player input action.

        Args:
            action_type: Semantic action type string
            action_data: Action payload dict
        """
        if action_type == "quit":
            self._running = False

        elif action_type == "escape":
            # In lobby or game, pressing ESC does nothing dangerous by default
            pass

        # --- Card interaction ---
        elif action_type == "card_clicked":
            if self.state.is_local_player_turn():
                card: Optional[CardDTO] = action_data.get("card")
                if card:
                    # forward to game screen for visual feedback (flash)
                    if self.game_screen:
                        # InputHandler provides card_index; forward as visual event
                        idx = action_data.get("card_index")
                        self.game_screen.handle_input({"card_clicked_index": idx})
                    self._handle_card_clicked(card)

        elif action_type == "draw_card":
            if self.state.is_local_player_turn():
                self.network.send_message(DrawCard())

        # --- Special card selections ---
        elif action_type == "color_chosen":
            if self.state.is_pending_color_selection():
                pending = self.state.get_pending_card()
                color = action_data.get("color")
                if pending and color:
                    self._send_play_card(pending, chosen_color=color)
                    self.state.clear_pending_selection()

        elif action_type == "target_chosen":
            if self.state.is_pending_target_selection():
                pending = self.state.get_pending_card()
                target_id = action_data.get("player_id")
                if pending and target_id is not None:
                    self._send_play_card(pending, target_player_id=target_id)
                    self.state.clear_pending_selection()

        elif action_type == "direction_chosen":
            if self.state.is_pending_direction_selection():
                pending = self.state.get_pending_card()
                direction = action_data.get("direction")
                if pending and direction:
                    self._send_play_card(pending, chosen_direction=direction)
                    self.state.clear_pending_selection()

        # --- Rule 8 reaction ---
        elif action_type == "react_rule8":
            if self.state.is_rule8_active() and not self.state.has_rule8_reacted():
                self.network.send_message(Rule8Reaction())
                self.state.mark_rule8_reacted()

        # --- Hover (pass through to game screen for visual feedback) ---
        elif action_type == "hover_changed":
            if self.game_screen:
                self.game_screen.handle_input(action_data)

        # --- Lobby/menu navigation ---
        elif action_type == "host_game":
            player_name = action_data.get("player_name", self._player_name)
            self._player_name = player_name
            self.host_game()

        elif action_type == "join_game":
            player_name = action_data.get("player_name", self._player_name)
            server_ip = action_data.get("server_ip", self._default_host)
            self._player_name = player_name
            self.network = NetworkClient(server_ip, self._default_port)
            self.join_game(server_ip)

        elif action_type == "start_game":
            self.start_game()

        elif action_type == "leave_room":
            self._on_leave_room()

    def _handle_card_clicked(self, card: CardDTO):
        """Determine whether we need extra input or can play immediately."""
        if card.value == CardValue.WILD or card.value == CardValue.WILD_DRAW_FOUR:
            self.state.set_pending_color_selection(card)
        elif card.value == CardValue.SEVEN:
            self.state.set_pending_target_selection(card)
        elif card.value == CardValue.ZERO:
            self.state.set_pending_direction_selection(card)
        else:
            self._send_play_card(card)

    def _send_play_card(self, card: CardDTO, chosen_color=None,
                        target_player_id=None, chosen_direction=None):
        msg = PlayCard(
            card=card,
            chosen_color=chosen_color,
            target_player_id=target_player_id,
            chosen_direction=chosen_direction,
        )
        self.network.send_message(msg)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect_to_server(self, player_name: str, host: str = DEFAULT_HOST) -> bool:
        """
        Establish connection to server and send join message.

        Args:
            player_name: Display name for this player
            host: Server host address

        Returns:
            True if connection successful
        """
        if self.network is None:
            self.network = NetworkClient(host, self._default_port)
        if not self.network.connect():
            print(f"[CLIENT] Could not connect to {host}:{self._default_port}")
            return False
        self.state.set_local_username(player_name)
        join_msg = JoinRoom(username=player_name)
        return self.network.send_message(join_msg)

    def disconnect_from_server(self):
        """Disconnect from the server."""
        if self.network:
            self.network.disconnect()

    def host_game(self):
        """Start a local server in a background thread, then join it as first player."""
        def _run_server():
            from server.main import GameServer
            srv = GameServer(host="0.0.0.0", port=self._default_port)
            srv.start()
            try:
                while True:
                    time.sleep(1)
            except Exception:
                pass

        self._server_thread = threading.Thread(target=_run_server, daemon=True)
        self._server_thread.start()

        # Give the server socket time to bind before connecting
        time.sleep(0.5)

        self.network = NetworkClient("localhost", self._default_port)
        self.connect_to_server(self._player_name, host="localhost")

    def join_game(self, room_id: str):
        """
        Join an existing game room.

        Args:
            room_id: Server IP address to connect to
        """
        self.connect_to_server(self._player_name, host=room_id)

    def start_game(self):
        """Notify server to start the game (host only)."""
        if self.network and self.network.is_connected():
            self.network.send_message(StartGame())

    def send_player_action(self, action_type: str, action_data: dict):
        """
        Send player action to server (public API for external callers).

        Args:
            action_type: Type of action
            action_data: Action details
        """
        self.handle_input_action(action_type, action_data)

    # ------------------------------------------------------------------
    # Screen callbacks (wired into M3 screen constructors)
    # ------------------------------------------------------------------

    def _on_host_click(self, player_name: str = "Player"):
        self._player_name = player_name
        self.host_game()

    def _on_join_click(self, player_name: str = "Player", server_ip: str = DEFAULT_HOST):
        self._player_name = player_name
        self.network = NetworkClient(server_ip, self._default_port)
        self.join_game(server_ip)

    def _on_start_game(self):
        self.start_game()

    def _on_leave_room(self):
        self.disconnect_from_server()
        self.state.reset_state()
        self._screen = "menu"

    def _on_play_card(self, card, **kwargs):
        """Called by GameScreen when the player selects a card to play."""
        if isinstance(card, CardDTO):
            self._handle_card_clicked(card)
        else:
            # Support plain Card objects if M3 passes them
            from shared.message_protocol import CardDTO as DTO
            self._handle_card_clicked(DTO(color=card.color, value=card.value))

    def _on_draw_card(self):
        """Called by GameScreen when the player clicks the draw pile."""
        if self.state.is_local_player_turn():
            self.network.send_message(DrawCard())

    def _on_uno_click(self):
        """Called by GameScreen when the player clicks the UNO button."""
        pass  # Optional: implement UNO declaration if required

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _active_screen(self):
        if self._screen == "menu":
            return self.menu_screen
        elif self._screen == "lobby":
            return self.lobby_screen
        elif self._screen in ("game", "game_over"):
            return self.game_screen
        return self.menu_screen


def main():
    """Entry point for the client application."""
    client = GameClient(host=DEFAULT_HOST, port=DEFAULT_PORT)
    client.run()


if __name__ == "__main__":
    main()
