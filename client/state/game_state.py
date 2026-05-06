"""
Client-side game state management.
Stores the local representation of game state received from the server.
"""

import time
from typing import List, Optional, Dict
from shared.data_structures import Card, Player, GameStatus
from shared.enums import GameState, PlayerState, TurnDirection, CardColor
from shared.message_protocol import CardDTO


def _dto_to_card(dto: CardDTO) -> Card:
    return Card(color=dto.color, value=dto.value)


class GameStateManager:
    """
    Manages client-side game state.
    Receives updates from server and maintains local state for UI rendering.
    """

    def __init__(self):
        self._local_player_id: Optional[int] = None
        self._local_username: str = ""

        # Persisted player registry (built from LOBBY_UPDATE events)
        self._players: Dict[int, Player] = {}

        # Game state from GameStateUpdate
        self._game_state: GameState = GameState.LOBBY
        self._current_turn_player_id: Optional[int] = None
        self._turn_direction: TurnDirection = TurnDirection.FORWARD
        self._top_discard_card: Optional[CardDTO] = None
        self._active_color: Optional[CardColor] = None
        self._active_stacking_penalty: int = 0

        # Local player's full hand (only we know our own cards)
        self._local_hand: List[Card] = []

        # Opponents: player_id (str) -> card count
        self._opponents_card_counts: Dict[str, int] = {}

        # Lobby metadata
        self._host_client_id: Optional[int] = None

        # Rule 8 timer
        self._rule8_active: bool = False
        self._rule8_start_time: float = 0.0
        self._rule8_timeout: float = 3.0
        self._rule8_reacted: bool = False

        # Pending selection flags (special card flows)
        self._pending_color_selection: bool = False
        self._pending_target_selection: bool = False
        self._pending_direction_selection: bool = False
        self._pending_card: Optional[CardDTO] = None

        # End-of-game
        self._winner_id: Optional[int] = None
        self._winner_name: Optional[str] = None

    # ------------------------------------------------------------------
    # State updates from server messages
    # ------------------------------------------------------------------

    def update_game_state(self, state_data: dict):
        """
        Update game state from server's GameStateUpdate message dict.

        Args:
            state_data: Dictionary containing game state from server
        """
        try:
            self._current_turn_player_id = state_data.get("current_turn_player_id")

            direction_val = state_data.get("current_play_direction")
            if direction_val:
                self._turn_direction = TurnDirection(direction_val)

            top_card_data = state_data.get("top_discard_card")
            if top_card_data:
                self._top_discard_card = CardDTO.from_dict(top_card_data)

            hand_data = state_data.get("client_hand", [])
            self._local_hand = [_dto_to_card(CardDTO.from_dict(c)) for c in hand_data]

            self._opponents_card_counts = state_data.get("opponents_card_counts", {})
            self._active_stacking_penalty = state_data.get("active_stacking_penalty", 0)

            color_val = state_data.get("active_color")
            self._active_color = CardColor(color_val) if color_val else None

            # Transition to PLAYING unless already in a special state
            if self._game_state not in (GameState.GAME_OVER, GameState.REACTION_EVENT):
                self._game_state = GameState.PLAYING

            # Update local player's hand in the player registry
            if self._local_player_id is not None and self._local_player_id in self._players:
                self._players[self._local_player_id].hand = self._local_hand[:]

        except Exception as e:
            print(f"[STATE] Error in update_game_state: {e}")

    def handle_event(self, event_name: str, event_data: dict):
        """
        Handle EventBroadcast messages from server.

        Args:
            event_name: Event identifier string
            event_data: Event payload dict
        """
        if event_name == "LOBBY_UPDATE":
            self._apply_lobby_update(event_data)

        elif event_name == "GAME_STARTING":
            self._game_state = GameState.PLAYING

        elif event_name == "RULE_8_STARTED":
            self._rule8_active = True
            self._rule8_start_time = time.time()
            self._rule8_reacted = False
            self._rule8_timeout = float(event_data.get("timeout", 3.0))
            self._game_state = GameState.REACTION_EVENT

        elif event_name == "RULE_8_RESOLVED":
            self._rule8_active = False
            self._rule8_reacted = False
            if self._game_state == GameState.REACTION_EVENT:
                self._game_state = GameState.PLAYING

        elif event_name == "GAME_OVER":
            self._game_state = GameState.GAME_OVER
            self._winner_id = event_data.get("winner_id")
            self._winner_name = event_data.get("winner_name")

    def _apply_lobby_update(self, event_data: dict):
        self._host_client_id = event_data.get("host_client_id")

        game_state_val = event_data.get("game_state", "lobby")
        try:
            self._game_state = GameState(game_state_val)
        except ValueError:
            pass

        # Rebuild player registry from lobby data
        for player_info in event_data.get("players", []):
            pid = player_info["client_id"]
            if pid not in self._players:
                self._players[pid] = Player(
                    player_id=pid,
                    name=player_info.get("name", f"Player{pid}"),
                    is_host=player_info.get("is_host", False),
                    is_connected=player_info.get("is_connected", True),
                )
            else:
                self._players[pid].name = player_info.get("name", self._players[pid].name)
                self._players[pid].is_host = player_info.get("is_host", False)
                self._players[pid].is_connected = player_info.get("is_connected", True)

        # Identify local player by username if not yet known
        if self._local_player_id is None and self._local_username:
            for player_info in event_data.get("players", []):
                if player_info.get("name") == self._local_username:
                    self._local_player_id = player_info["client_id"]
                    break

    # ------------------------------------------------------------------
    # Rule 8 timer helpers
    # ------------------------------------------------------------------

    def update_rule8_timer(self) -> float:
        """
        Tick the Rule 8 countdown. Returns remaining seconds (0 when expired).
        """
        if not self._rule8_active:
            return 0.0
        remaining = max(0.0, self._rule8_timeout - (time.time() - self._rule8_start_time))
        if remaining <= 0:
            self._rule8_active = False
        return remaining

    def mark_rule8_reacted(self):
        self._rule8_reacted = True

    # ------------------------------------------------------------------
    # Pending selection state (Wild color / Rule-7 target / Rule-0 direction)
    # ------------------------------------------------------------------

    def set_pending_color_selection(self, card: CardDTO):
        self._pending_color_selection = True
        self._pending_card = card

    def set_pending_target_selection(self, card: CardDTO):
        self._pending_target_selection = True
        self._pending_card = card

    def set_pending_direction_selection(self, card: CardDTO):
        self._pending_direction_selection = True
        self._pending_card = card

    def clear_pending_selection(self):
        self._pending_color_selection = False
        self._pending_target_selection = False
        self._pending_direction_selection = False
        self._pending_card = None

    # ------------------------------------------------------------------
    # Setters
    # ------------------------------------------------------------------

    def set_local_player_id(self, player_id: int):
        self._local_player_id = player_id

    def set_local_username(self, username: str):
        self._local_username = username

    # ------------------------------------------------------------------
    # Getters — used by M3 (renderer) and M4 (main loop)
    # ------------------------------------------------------------------

    def get_local_player_id(self) -> Optional[int]:
        return self._local_player_id

    def get_local_player(self) -> Optional[Player]:
        if self._local_player_id is None:
            return None
        player = self._players.get(self._local_player_id)
        if player is None:
            return None
        # Return a copy with the actual hand injected
        return Player(
            player_id=player.player_id,
            name=player.name,
            hand=self._local_hand[:],
            state=player.state,
            score=player.score,
            is_host=player.is_host,
            is_connected=player.is_connected,
        )

    def get_all_players(self) -> List[Player]:
        result = []
        for pid, player in self._players.items():
            if pid == self._local_player_id:
                result.append(Player(
                    player_id=player.player_id,
                    name=player.name,
                    hand=self._local_hand[:],
                    state=player.state,
                    score=player.score,
                    is_host=player.is_host,
                    is_connected=player.is_connected,
                ))
            else:
                result.append(player)
        return result

    def get_player(self, player_id: int) -> Optional[Player]:
        return self._players.get(player_id)

    def get_game_status(self) -> GameStatus:
        last_card: Optional[Card] = None
        if self._top_discard_card:
            last_card = _dto_to_card(self._top_discard_card)
        return GameStatus(
            game_state=self._game_state,
            current_player_id=self._current_turn_player_id,
            last_card_played=last_card,
            turn_direction=self._turn_direction,
            active_wild_color=self._active_color,
        )

    def get_current_player_id(self) -> Optional[int]:
        return self._current_turn_player_id

    def get_last_card_played(self) -> Optional[Card]:
        if self._top_discard_card is None:
            return None
        return _dto_to_card(self._top_discard_card)

    def get_local_hand(self) -> List[Card]:
        return self._local_hand

    def get_turn_direction(self) -> TurnDirection:
        return self._turn_direction

    def get_active_color(self) -> Optional[CardColor]:
        return self._active_color

    def get_active_stacking_penalty(self) -> int:
        return self._active_stacking_penalty

    def get_opponents_card_counts(self) -> Dict[str, int]:
        return self._opponents_card_counts

    def get_game_state(self) -> GameState:
        return self._game_state

    def get_lobby_players(self) -> List[dict]:
        return [
            {
                "client_id": p.player_id,
                "name": p.name,
                "is_host": p.is_host,
                "is_connected": p.is_connected,
            }
            for p in self._players.values()
        ]

    def get_host_client_id(self) -> Optional[int]:
        return self._host_client_id

    def is_host(self) -> bool:
        return (
            self._local_player_id is not None
            and self._local_player_id == self._host_client_id
        )

    def is_local_player_turn(self) -> bool:
        return (
            self._local_player_id is not None
            and self._current_turn_player_id == self._local_player_id
        )

    def is_rule8_active(self) -> bool:
        return self._rule8_active

    def has_rule8_reacted(self) -> bool:
        return self._rule8_reacted

    def get_rule8_time_remaining(self) -> float:
        if not self._rule8_active:
            return 0.0
        return max(0.0, self._rule8_timeout - (time.time() - self._rule8_start_time))

    def is_pending_color_selection(self) -> bool:
        return self._pending_color_selection

    def is_pending_target_selection(self) -> bool:
        return self._pending_target_selection

    def is_pending_direction_selection(self) -> bool:
        return self._pending_direction_selection

    def get_pending_card(self) -> Optional[CardDTO]:
        return self._pending_card

    def get_winner_id(self) -> Optional[int]:
        return self._winner_id

    def get_winner_name(self) -> Optional[str]:
        return self._winner_name

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset_state(self):
        saved_id = self._local_player_id
        saved_username = self._local_username
        self.__init__()
        self._local_player_id = saved_id
        self._local_username = saved_username

    def serialize_state(self) -> dict:
        return {
            "local_player_id": self._local_player_id,
            "game_state": self._game_state.value,
            "current_turn_player_id": self._current_turn_player_id,
            "is_local_player_turn": self.is_local_player_turn(),
            "local_hand_count": len(self._local_hand),
            "active_stacking_penalty": self._active_stacking_penalty,
            "rule8_active": self._rule8_active,
            "rule8_time_remaining": self.get_rule8_time_remaining(),
            "pending_color": self._pending_color_selection,
            "pending_target": self._pending_target_selection,
            "pending_direction": self._pending_direction_selection,
            "is_host": self.is_host(),
        }
