"""
Game engine for managing core game logic.
Handles turn progression, card validation, game state, and win conditions.
This is the authoritative source of truth for game state (Host-Authoritative model).
All clients trust the host's decisions on game state and rule enforcement.
"""

import time
from typing import List, Optional, Tuple, Callable, Dict
from shared.data_structures import Card, Player, GameStatus, ReactionEvent, StackingState
from shared.enums import (
    GameState, PlayerState, CardColor, CardValue, TurnDirection,
    ReactionEventState as ReactionStateEnum, CardAction
)
from server.deck import Deck
from server.player import PlayerManager
from server.rules import RuleEngine


class GameEngine:
    """
    Central game logic engine (Host-Authoritative).
    Handles all game mechanics, turn progression, and rule application.
    Communicates game state changes via broadcast callback.
    All authority over game state flows through this engine.
    """

    def __init__(self, state_update_callback: Callable, enable_rule_0: bool = True,
                 enable_rule_7: bool = True, enable_rule_8: bool = True,
                 enable_stacking: bool = True, cannot_win_with_action: bool = True):
        """
        Initialize the game engine.

        Args:
            state_update_callback: Callback to broadcast game state updates
            enable_rule_0: Enable Play in Order (pass entire hand)
            enable_rule_7: Enable Sevens (hand swap)
            enable_rule_8: Enable Eights (reaction event)
            enable_stacking: Enable draw card stacking
            cannot_win_with_action: Disallow action cards as final card
        """
        self._broadcast_callback: Callable = state_update_callback
        self.enable_rule_0 = enable_rule_0
        self.enable_rule_7 = enable_rule_7
        self.enable_rule_8 = enable_rule_8
        self.enable_stacking = enable_stacking
        self.cannot_win_with_action = cannot_win_with_action

        # Core components (initialised in start_game)
        self.deck: Optional[Deck] = None
        self.player_manager: Optional[PlayerManager] = None
        self.rule_engine: Optional[RuleEngine] = None
        self.game_status: Optional[GameStatus] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_game(self, players: List[Player]) -> bool:
        """
        Initialize and start a new game.
        Shuffles deck, deals initial hands, selects starting player.

        Args:
            players: List of Player objects to play

        Returns:
            True if game started successfully
        """
        if not players:
            return False

        # Build components
        self.deck = Deck()
        self.deck.initialize_deck()
        self.deck.shuffle_draw_pile()

        self.player_manager = PlayerManager()
        for p in players:
            self.player_manager.add_player(p.player_id, p.name, p.is_host)

        self.rule_engine = RuleEngine(
            enable_rule_0=self.enable_rule_0,
            enable_rule_7=self.enable_rule_7,
            enable_rule_8=self.enable_rule_8,
            enable_stacking=self.enable_stacking,
            cannot_win_with_action_card=self.cannot_win_with_action,
        )

        # Deal 7 cards to each player
        for p in players:
            cards = self.deck.draw_multiple(7)
            self.player_manager.add_cards_to_hand(p.player_id, cards)

        # Flip first card onto discard pile (must be a number card)
        starting_card: Optional[Card] = None
        while True:
            card = self.deck.draw_card()
            if card is None:
                return False
            if card.value not in (CardValue.WILD, CardValue.WILD_DRAW_FOUR,
                                  CardValue.SKIP, CardValue.REVERSE, CardValue.DRAW_TWO):
                starting_card = card
                break
            # Put action/wild back and try again
            self.deck.draw_pile.insert(0, card)

        self.deck.discard_card(starting_card)

        starting_player_id = players[0].player_id

        self.game_status = GameStatus(
            game_state=GameState.PLAYING,
            current_player_id=starting_player_id,
            current_turn_count=0,
            last_card_played=starting_card,
            draw_pile_count=self.deck.get_draw_pile_count(),
            discard_pile_count=self.deck.get_discard_pile_count(),
            turn_direction=TurnDirection.FORWARD,
            stacking_state=StackingState(),
            reaction_event=ReactionEvent(state=ReactionStateEnum.PENDING),
        )

        # Mark starting player as TURN
        self.player_manager.set_player_state(starting_player_id, PlayerState.TURN)

        self.broadcast_game_state_update()
        return True

    def end_game(self) -> Optional[int]:
        """
        End the current game and determine winner.

        Returns:
            ID of winning player or None if error
        """
        winner_id = self.check_win_condition()
        if self.game_status:
            self.game_status.game_state = GameState.GAME_OVER
        self.broadcast_game_state_update()
        return winner_id

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def next_turn(self):
        """Progress to the next player's turn."""
        if not self.game_status or self.game_status.game_state != GameState.PLAYING:
            return

        current_player_id = self.game_status.current_player_id
        turn_direction = self.game_status.turn_direction
        players = self.get_all_players()
        if not players:
            return

        active_ids = [p.player_id for p in players if p.state != PlayerState.DISCONNECTED]
        if not active_ids:
            return

        # Clear current player's TURN state
        if current_player_id is not None:
            self.player_manager.set_player_state(current_player_id, PlayerState.IDLE)

        next_id = self._get_next_player_id(current_player_id, turn_direction, active_ids)
        self.game_status.current_player_id = next_id
        self.game_status.current_turn_count += 1
        self._sync_pile_counts()

        self.player_manager.set_player_state(next_id, PlayerState.TURN)
        self.broadcast_game_state_update()

    def _get_next_player_id(self, current_id: Optional[int],
                            direction: TurnDirection, active_ids: List[int]) -> int:
        """Return the ID of the player who goes after current_id."""
        if current_id not in active_ids:
            return active_ids[0]
        idx = active_ids.index(current_id)
        if direction == TurnDirection.FORWARD:
            return active_ids[(idx + 1) % len(active_ids)]
        else:
            return active_ids[(idx - 1) % len(active_ids)]

    # Keep old name for backward compat
    def get_next_player_id(self, current_id: Optional[int],
                           direction: TurnDirection, active_ids: List[int]) -> int:
        return self._get_next_player_id(current_id, direction, active_ids)

    # ------------------------------------------------------------------
    # Card play
    # ------------------------------------------------------------------

    def attempt_play_card(self, player_id: int, card_index: int,
                          target_color: Optional[CardColor] = None,
                          target_player_id: Optional[int] = None,
                          chosen_direction: Optional[TurnDirection] = None) -> Tuple[bool, str]:
        """
        Attempt to play a card from a player's hand.

        Returns:
            Tuple: (success, error_message)
        """
        # 1. Verify turn
        if not self.validate_action_is_current_player_turn(player_id):
            return False, "WRONG_TURN"

        # 2. Verify card exists
        if not self.validate_card_in_hand(player_id, card_index):
            return False, "INVALID_CARD_INDEX"

        player_hand = self.player_manager.get_player_hand(player_id)
        card = player_hand[card_index]
        top_card = self.deck.peek_top_discard()
        active_color = self.game_status.active_wild_color

        # 3. Validate legality
        valid, err = self.rule_engine.validate_play_legality(
            card, top_card, True, self.game_status.current_player_id,
            player_id, active_color
        )
        if not valid:
            return False, err

        # 4. Cannot win with action card check
        if self.player_manager.get_player_hand_size(player_id) == 1:
            if not self.rule_engine.can_win_with_card(card):
                return False, "CANNOT_WIN_WITH_ACTION"

        # 5. Handle stacking
        if self.enable_stacking and card.value in (CardValue.DRAW_TWO, CardValue.WILD_DRAW_FOUR):
            stacking = self.game_status.stacking_state
            if stacking.is_active:
                is_valid_stack, new_total = self.rule_engine.apply_stacking(stacking, card)
                if not is_valid_stack:
                    # Invalid stack – resolve existing penalty on current player first
                    penalty = stacking.accumulated_penalty
                    stacking.is_active = False
                    stacking.accumulated_penalty = 0
                    self.draw_cards_penalty(player_id, penalty, "stacking_resolve")
                    return False, "INVALID_STACKING"
            else:
                # Start a new stack
                stacking = self.game_status.stacking_state
                stacking.is_active = True
                stacking.accumulated_penalty = 2 if card.value == CardValue.DRAW_TWO else 4
                stacking.last_card_played = card
                stacking.responder_player_id = None

        # 6. Execute the play – remove card from hand, add to discard
        self.player_manager.remove_card_from_hand(player_id, card_index)
        self.deck.discard_card(card)
        self.game_status.last_card_played = card

        # 7. Apply card effects
        self._apply_card_effects(player_id, card, target_color, target_player_id)

        # 8. Check win
        if self.player_manager.get_player_hand_size(player_id) == 0:
            self.end_game()
            return True, ""

        self._sync_pile_counts()
        self.broadcast_game_state_update()
        return True, ""

    def _apply_card_effects(self, player_id: int, card: Card,
                            target_color: Optional[CardColor],
                            target_player_id: Optional[int]):
        """Apply the effect of a played card."""
        val = card.value

        if val == CardValue.SKIP:
            self.skip_player()

        elif val == CardValue.REVERSE:
            self.reverse_turn_order()
            # In 2-player, Reverse acts as Skip
            active = [p.player_id for p in self.get_all_players()
                      if p.state != PlayerState.DISCONNECTED]
            if len(active) == 2:
                self.skip_player()

        elif val == CardValue.DRAW_TWO:
            if not (self.enable_stacking and self.game_status.stacking_state.is_active):
                self.next_turn()
                next_pid = self.game_status.current_player_id
                self.draw_cards_penalty(next_pid, 2, "draw_two")
                return  # Already advanced turn

        elif val == CardValue.WILD:
            self.apply_wild_card(player_id, target_color or CardColor.RED)

        elif val == CardValue.WILD_DRAW_FOUR:
            self.apply_wild_card(player_id, target_color or CardColor.RED)
            if not (self.enable_stacking and self.game_status.stacking_state.is_active):
                self.next_turn()
                next_pid = self.game_status.current_player_id
                self.draw_cards_penalty(next_pid, 4, "draw_four")
                return

        elif val == CardValue.SEVEN and self.enable_rule_7 and target_player_id:
            self.apply_rule_7_hand_swap(player_id, target_player_id)

        elif val == CardValue.ZERO and self.enable_rule_0 and target_player_id:
            if chosen_direction is None:
                direction_str = "forward" if self.game_status.turn_direction == TurnDirection.FORWARD else "backward"
            else:
                direction_str = "forward" if chosen_direction == TurnDirection.FORWARD else "backward"
            self.apply_rule_0_hand_pass(player_id, target_player_id, direction_str)

        elif val == CardValue.EIGHT and self.enable_rule_8:
            all_ids = [p.player_id for p in self.get_all_players()
                       if p.state != PlayerState.DISCONNECTED]
            self.trigger_reaction_event_rule_8(player_id, card)
            return  # Reaction event takes over; don't advance turn yet

        self.next_turn()

    # ------------------------------------------------------------------
    # Draw actions
    # ------------------------------------------------------------------

    def attempt_draw_card(self, player_id: int) -> Tuple[bool, Optional[Card]]:
        """
        Handle player's draw action.

        Returns:
            Tuple: (drawn_card_playable, drawn_card)
        """
        if not self.validate_action_is_current_player_turn(player_id):
            return False, None

        card = self.deck.draw_card()
        if card is None:
            return False, None

        self.player_manager.add_card_to_hand(player_id, card)
        self._sync_pile_counts()

        top_card = self.deck.peek_top_discard()
        playable = self.rule_engine.is_valid_play(card, top_card,
                                                  self.game_status.active_wild_color)
        if not playable:
            self.next_turn()

        self.broadcast_game_state_update()
        return playable, card

    def draw_cards_penalty(self, player_id: int, count: int, reason: str):
        """
        Apply penalty draw (from +2, +4, Rule 8, stacking, etc.).
        Player draws specified cards and loses turn.
        """
        cards = self.deck.draw_multiple(count)
        self.player_manager.add_cards_to_hand(player_id, cards)
        self.player_manager.set_player_state(player_id, PlayerState.PENALTY_DRAW)
        self._sync_pile_counts()
        self.broadcast_game_state_update()
        # Restore state and continue
        self.player_manager.set_player_state(player_id, PlayerState.IDLE)

    # ------------------------------------------------------------------
    # Simple card effects
    # ------------------------------------------------------------------

    def skip_player(self):
        """Skip the current player's turn and move to next player."""
        # Advance once to skip, then the caller's next_turn() advances again
        if not self.game_status:
            return
        turn_direction = self.game_status.turn_direction
        active_ids = [p.player_id for p in self.get_all_players()
                      if p.state != PlayerState.DISCONNECTED]
        skipped_id = self._get_next_player_id(
            self.game_status.current_player_id, turn_direction, active_ids)
        self.player_manager.set_player_state(skipped_id, PlayerState.IDLE)
        self.game_status.current_player_id = skipped_id

    def reverse_turn_order(self):
        """Reverse the direction of play."""
        if not self.game_status:
            return
        if self.game_status.turn_direction == TurnDirection.FORWARD:
            self.game_status.turn_direction = TurnDirection.REVERSE
        else:
            self.game_status.turn_direction = TurnDirection.FORWARD

    def apply_wild_card(self, player_id: int, target_color: CardColor):
        """Apply wild card effect – change active color."""
        if self.game_status:
            self.game_status.active_wild_color = target_color

    # ------------------------------------------------------------------
    # Rule 8 – Reaction Event
    # ------------------------------------------------------------------

    def trigger_reaction_event_rule_8(self, triggered_by_player_id: int,
                                      triggered_card: Card) -> ReactionEvent:
        """Trigger Rule 8 reaction event."""
        all_ids = [p.player_id for p in self.get_all_players()
                   if p.state != PlayerState.DISCONNECTED]
        event = self.rule_engine.apply_rule_8(triggered_by_player_id, triggered_card, all_ids)
        self.game_status.reaction_event = event
        self.game_status.game_state = GameState.REACTION_EVENT
        for pid in all_ids:
            self.player_manager.set_player_state(pid, PlayerState.RESPONDING_REACTION)
        self.broadcast_game_state_update()
        return event

    def submit_reaction_response(self, player_id: int, reaction_event: ReactionEvent,
                                 current_time: float) -> bool:
        """Record a player's response to a reaction event."""
        return self.rule_engine.validate_rule_8_response(reaction_event, player_id, current_time)

    def resolve_reaction_event(self, reaction_event: ReactionEvent,
                               current_time: float) -> Optional[int]:
        """Resolve reaction event after timeout."""
        loser_id = self.rule_engine.resolve_rule_8_event(reaction_event, current_time)

        all_ids = [p.player_id for p in self.get_all_players()
                   if p.state != PlayerState.DISCONNECTED]

        if loser_id is None:
            # All non-responders draw; everyone except triggerer who responded is a loser
            responders = set(reaction_event.responders.keys())
            for pid in all_ids:
                if pid != reaction_event.triggered_by_player_id and pid not in responders:
                    self.draw_cards_penalty(pid, 2, "rule_8_reaction")
        else:
            self.draw_cards_penalty(loser_id, 2, "rule_8_reaction")

        # Restore all player states and resume game
        for pid in all_ids:
            self.player_manager.set_player_state(pid, PlayerState.IDLE)
        self.game_status.game_state = GameState.PLAYING
        reaction_event.state = ReactionStateEnum.PENDING  # reset alias
        self.next_turn()
        return loser_id

    # ------------------------------------------------------------------
    # Rule 7 – Hand Swap
    # ------------------------------------------------------------------

    def apply_rule_7_hand_swap(self, swapper_player_id: int,
                               target_player_id: int) -> bool:
        """Swap hands between two players (Rule 7)."""
        if not self.rule_engine.enable_rule_7:
            return False
        swapper = self.player_manager.get_player(swapper_player_id)
        target = self.player_manager.get_player(target_player_id)
        if swapper is None or target is None:
            return False
        swapper.hand, target.hand = target.hand, swapper.hand
        return True

    # ------------------------------------------------------------------
    # Rule 0 – Hand Pass
    # ------------------------------------------------------------------

    def apply_rule_0_hand_pass(self, passer_player_id: int,
                               target_player_id: int,
                               direction: str) -> bool:
        """Pass entire hand to target player (Rule 0). Player keeps their turn."""
        if not self.rule_engine.enable_rule_0:
            return False
        passer = self.player_manager.get_player(passer_player_id)
        target = self.player_manager.get_player(target_player_id)
        if passer is None or target is None:
            return False
        target.hand.extend(passer.hand)
        passer.hand = []
        return True

    # ------------------------------------------------------------------
    # Stacking
    # ------------------------------------------------------------------

    def apply_stacking_accumulation(self, card_played: Card) -> Tuple[bool, int]:
        """Apply stacking accumulation for +2/+4 cards."""
        stacking = self.game_status.stacking_state
        is_valid, new_total = self.rule_engine.apply_stacking(stacking, card_played)
        return is_valid, new_total if new_total is not None else stacking.accumulated_penalty

    def resolve_stacking_penalty(self, responder_player_id: int, penalty_count: int):
        """Resolve stacking penalty: player draws accumulated cards and loses turn."""
        stacking = self.game_status.stacking_state
        stacking.is_active = False
        stacking.accumulated_penalty = 0
        stacking.last_card_played = None
        stacking.responder_player_id = None
        self.draw_cards_penalty(responder_player_id, penalty_count, "stacking_resolve")
        self.next_turn()

    # ------------------------------------------------------------------
    # Win / game-over conditions
    # ------------------------------------------------------------------

    def check_win_condition(self) -> Optional[int]:
        """Check if any player has won (0 cards in hand)."""
        if not self.player_manager:
            return None
        for player in self.player_manager.get_all_players():
            if len(player.hand) == 0 and player.state != PlayerState.DISCONNECTED:
                return player.player_id
        return None

    def check_game_over_conditions(self) -> Optional[Tuple[int, str]]:
        """Check for all game-ending conditions."""
        if not self.player_manager:
            return None

        # Player won
        winner = self.check_win_condition()
        if winner is not None:
            return winner, "player_won"

        active = [p for p in self.player_manager.get_all_players()
                  if p.state != PlayerState.DISCONNECTED]

        if len(active) <= 1:
            if active:
                return active[0].player_id, "all_others_disconnected"
            return None, "no_players"

        return None

    # ------------------------------------------------------------------
    # Queries / helpers
    # ------------------------------------------------------------------

    def get_current_player_id(self) -> Optional[int]:
        """Get the ID of the player whose turn it is."""
        return self.game_status.current_player_id if self.game_status else None

    def get_game_status(self) -> Optional[GameStatus]:
        """Get the current game status."""
        return self.game_status

    def serialize_game_state(self) -> Dict:
        """Serialize complete game state to dictionary."""
        if not self.game_status or not self.player_manager:
            return {}

        players_data = []
        for p in self.player_manager.get_all_players():
            players_data.append({
                "player_id": p.player_id,
                "name": p.name,
                "hand_size": len(p.hand),
                "state": p.state.value,
                "score": p.score,
                "is_host": p.is_host,
                "is_connected": p.is_connected,
            })

        top_card = self.deck.peek_top_discard() if self.deck else None
        stacking = self.game_status.stacking_state
        reaction = self.game_status.reaction_event

        return {
            "game_state": self.game_status.game_state.value,
            "current_player_id": self.game_status.current_player_id,
            "current_turn_count": self.game_status.current_turn_count,
            "turn_direction": self.game_status.turn_direction.value,
            "draw_pile_count": self.game_status.draw_pile_count,
            "discard_pile_count": self.game_status.discard_pile_count,
            "last_card_played": {
                "color": self.game_status.last_card_played.color.value,
                "value": self.game_status.last_card_played.value.value,
            } if self.game_status.last_card_played else None,
            "top_discard_card": {
                "color": top_card.color.value,
                "value": top_card.value.value,
            } if top_card else None,
            "active_wild_color": self.game_status.active_wild_color.value
                                  if self.game_status.active_wild_color else None,
            "players": players_data,
            "stacking_state": {
                "is_active": stacking.is_active,
                "accumulated_penalty": stacking.accumulated_penalty,
                "responder_player_id": stacking.responder_player_id,
            },
            "reaction_event": {
                "is_active": reaction.is_active,
                "triggered_by_player_id": reaction.triggered_by_player_id,
                "state": reaction.state.value if reaction.state else None,
                "penalty_drawer_id": reaction.penalty_drawer_id,
            },
        }

    def get_player_hands(self) -> Dict[int, List[Card]]:
        """Get all players' hands."""
        if not self.player_manager:
            return {}
        return {p.player_id: list(p.hand)
                for p in self.player_manager.get_all_players()}

    # ------------------------------------------------------------------
    # Disconnection
    # ------------------------------------------------------------------

    def handle_disconnect(self, player_id: int):
        """Handle player disconnection during game."""
        if not self.player_manager:
            return
        player = self.player_manager.get_player(player_id)
        if player is None:
            return

        if not self.game_status or self.game_status.game_state == GameState.LOBBY:
            self.player_manager.remove_player(player_id)
            return

        # Mark as disconnected; skip their turns automatically
        self.player_manager.set_player_state(player_id, PlayerState.DISCONNECTED)
        player.is_connected = False

        # If it was their turn, advance
        if self.game_status.current_player_id == player_id:
            self.next_turn()

        # Check if only 1 player remains
        result = self.check_game_over_conditions()
        if result:
            self.end_game()

        self.broadcast_game_state_update()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def validate_action_is_current_player_turn(self, player_id: int) -> bool:
        """Validate that it's the specified player's turn."""
        if not self.game_status:
            return False
        return self.game_status.current_player_id == player_id

    def validate_card_in_hand(self, player_id: int, card_index: int) -> bool:
        """Validate that card exists at index in player's hand."""
        if not self.player_manager:
            return False
        hand = self.player_manager.get_player_hand(player_id)
        return 0 <= card_index < len(hand)

    # ------------------------------------------------------------------
    # Broadcast
    # ------------------------------------------------------------------

    def broadcast_game_state_update(self):
        """Broadcast current game state to all connected clients."""
        if callable(self._broadcast_callback) and self.game_status:
            self._broadcast_callback(self.get_game_status())

    def get_all_players(self) -> List[Player]:
        """Get list of all players in the game."""
        if not self.player_manager:
            return []
        return self.player_manager.get_all_players()

    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a specific player by ID."""
        if not self.player_manager:
            return None
        return self.player_manager.get_player(player_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sync_pile_counts(self):
        """Keep pile counts in game_status in sync with deck."""
        if self.game_status and self.deck:
            self.game_status.draw_pile_count = self.deck.get_draw_pile_count()
            self.game_status.discard_pile_count = self.deck.get_discard_pile_count()
