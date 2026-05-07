"""
Test suite for M4 (Client Controller & Event Handling) — no UI required.

Run from project root:
    python test_m4.py              # unit tests only
    python test_m4.py --server     # unit tests + integration (needs server running)
    python test_m4.py --full       # unit tests + auto-start server + integration
"""

import os
import sys
import time
import threading

# Headless pygame — must be set BEFORE importing pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1, 1))  # dummy surface required for some pygame.Rect ops


# =============================================================================
# Helpers
# =============================================================================

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
_results = {"pass": 0, "fail": 0}

def check(name: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  {PASS} {name}")
        _results["pass"] += 1
    else:
        print(f"  {FAIL} {name}" + (f" — {detail}" if detail else ""))
        _results["fail"] += 1


# =============================================================================
# 1. GameStateManager unit tests
# =============================================================================

def test_game_state_manager():
    print("\n── GameStateManager ──────────────────────────────────────")
    from client.state.game_state import GameStateManager
    from shared.enums import GameState, TurnDirection, CardColor, CardValue

    gsm = GameStateManager()

    # --- Initial state ---
    check("initial game_state is LOBBY", gsm.get_game_state() == GameState.LOBBY)
    check("initial local_player_id is None", gsm.get_local_player_id() is None)
    check("initial hand is empty", gsm.get_local_hand() == [])
    check("initial is_local_player_turn False", gsm.is_local_player_turn() is False)

    # --- set_local_player_id / set_local_username ---
    gsm.set_local_player_id(1)
    gsm.set_local_username("Alice")
    check("local_player_id set", gsm.get_local_player_id() == 1)

    # --- LOBBY_UPDATE event ---
    gsm.handle_event("LOBBY_UPDATE", {
        "players": [
            {"client_id": 1, "name": "Alice", "is_host": True, "is_connected": True},
            {"client_id": 2, "name": "Bob",   "is_host": False, "is_connected": True},
        ],
        "host_client_id": 1,
        "game_state": "lobby",
        "player_count": 2,
    })
    check("lobby players loaded",  len(gsm.get_lobby_players()) == 2)
    check("is_host True for client_id=1", gsm.is_host())
    check("game_state stays LOBBY",  gsm.get_game_state() == GameState.LOBBY)

    # --- LOBBY_UPDATE auto-sets local_player_id via username ---
    gsm2 = GameStateManager()
    gsm2.set_local_username("Bob")
    gsm2.handle_event("LOBBY_UPDATE", {
        "players": [
            {"client_id": 1, "name": "Alice", "is_host": True,  "is_connected": True},
            {"client_id": 2, "name": "Bob",   "is_host": False, "is_connected": True},
        ],
        "host_client_id": 1,
        "game_state": "lobby",
        "player_count": 2,
    })
    check("local_player_id auto-detected from username",
          gsm2.get_local_player_id() == 2)
    check("is_host False for Bob", gsm2.is_host() is False)

    # --- GameStateUpdate ---
    state_dict = {
        "message_type": "game_state_update",
        "current_turn_player_id": 1,
        "current_play_direction": "forward",
        "top_discard_card": {"color": "red", "value": "5"},
        "client_hand": [
            {"color": "red",  "value": "3"},
            {"color": "blue", "value": "7"},
            {"color": "wild", "value": "wild"},
        ],
        "opponents_card_counts": {"2": 5},
        "active_stacking_penalty": 0,
        "active_color": None,
    }
    gsm.update_game_state(state_dict)

    check("game_state → PLAYING",    gsm.get_game_state() == GameState.PLAYING)
    check("hand has 3 cards",         len(gsm.get_local_hand()) == 3)
    check("turn_direction FORWARD",   gsm.get_turn_direction() == TurnDirection.FORWARD)
    check("is_local_player_turn True (pid=1 == current=1)",
          gsm.is_local_player_turn())

    top = gsm.get_last_card_played()
    check("top discard red 5",
          top is not None and top.color == CardColor.RED and top.value == CardValue.FIVE)

    hand = gsm.get_local_hand()
    check("hand card 0 is red 3",
          hand[0].color == CardColor.RED and hand[0].value == CardValue.THREE)

    opponents = gsm.get_opponents_card_counts()
    check("opponent card count = 5", opponents.get("2") == 5)

    # --- Not your turn ---
    state_dict2 = dict(state_dict, current_turn_player_id=2)
    gsm.update_game_state(state_dict2)
    check("is_local_player_turn False when other's turn",
          gsm.is_local_player_turn() is False)

    # --- Pending selections ---
    from shared.message_protocol import CardDTO
    wild_card = CardDTO(color=CardColor.WILD, value=CardValue.WILD)
    gsm.set_pending_color_selection(wild_card)
    check("pending_color_selection set", gsm.is_pending_color_selection())
    check("pending_card is wild card",   gsm.get_pending_card() == wild_card)
    gsm.clear_pending_selection()
    check("pending cleared",             gsm.is_pending_color_selection() is False)

    seven_card = CardDTO(color=CardColor.RED, value=CardValue.SEVEN)
    gsm.set_pending_target_selection(seven_card)
    check("pending_target_selection set", gsm.is_pending_target_selection())
    gsm.clear_pending_selection()

    zero_card = CardDTO(color=CardColor.GREEN, value=CardValue.ZERO)
    gsm.set_pending_direction_selection(zero_card)
    check("pending_direction_selection set", gsm.is_pending_direction_selection())
    gsm.clear_pending_selection()

    # --- Rule 8 timer ---
    gsm.handle_event("RULE_8_STARTED", {"timeout": 0.3})
    check("rule8 active after event",    gsm.is_rule8_active())
    check("rule8 not yet reacted",       gsm.has_rule8_reacted() is False)
    remaining_before = gsm.get_rule8_time_remaining()
    check("rule8 time > 0 initially",    remaining_before > 0)
    gsm.mark_rule8_reacted()
    check("mark_rule8_reacted works",    gsm.has_rule8_reacted())

    time.sleep(0.35)   # wait for timeout to expire
    remaining_after = gsm.update_rule8_timer()
    check("rule8 expired after timeout", remaining_after == 0.0)
    check("rule8 inactive after expire", gsm.is_rule8_active() is False)

    gsm.handle_event("RULE_8_RESOLVED", {})
    check("game_state back to PLAYING after rule8 resolved",
          gsm.get_game_state() == GameState.PLAYING)

    # --- GAME_OVER ---
    gsm.handle_event("GAME_OVER", {"winner_id": 1, "winner_name": "Alice"})
    check("game_state GAME_OVER",  gsm.get_game_state() == GameState.GAME_OVER)
    check("winner_name correct",   gsm.get_winner_name() == "Alice")
    check("winner_id correct",     gsm.get_winner_id() == 1)

    # --- get_game_status() ---
    status = gsm.get_game_status()
    check("get_game_status returns GameStatus",
          hasattr(status, "game_state") and hasattr(status, "current_player_id"))

    # --- reset_state preserves player_id ---
    gsm.reset_state()
    check("reset preserves local_player_id", gsm.get_local_player_id() == 1)
    check("reset clears hand",               gsm.get_local_hand() == [])
    check("reset returns to LOBBY",          gsm.get_game_state() == GameState.LOBBY)

    # --- serialize_state ---
    info = gsm.serialize_state()
    check("serialize_state returns dict", isinstance(info, dict))
    check("serialize_state has game_state key", "game_state" in info)


# =============================================================================
# 2. InputHandler unit tests
# =============================================================================

def test_input_handler():
    print("\n── InputHandler ─────────────────────────────────────────")
    from client.controller.input_handler import InputHandler
    from shared.message_protocol import CardDTO
    from shared.enums import CardColor, CardValue, TurnDirection

    received_actions = []
    def callback(action_type, action_data):
        received_actions.append((action_type, action_data))

    ih = InputHandler(action_callback=callback)

    # --- Zone registration ---
    card_dto = CardDTO(color=CardColor.RED, value=CardValue.FIVE)
    card_zone = pygame.Rect(100, 400, 60, 90)
    ih.update_card_zones([(card_zone, card_dto)])
    check("card zone registered", len(ih._card_zones) == 1)

    draw_rect = pygame.Rect(600, 300, 60, 90)
    ih.update_button_zones({"draw_pile": draw_rect})
    check("button zone registered", "draw_pile" in ih._button_zones)

    # --- Card click ---
    received_actions.clear()
    ih.handle_mouse_click((120, 440), 1)    # inside card_zone
    check("card click fires card_clicked",
          len(received_actions) == 1 and received_actions[0][0] == "card_clicked")
    check("card_clicked carries correct card",
          received_actions[0][1].get("card") == card_dto)

    # --- Draw pile click ---
    received_actions.clear()
    ih.handle_mouse_click((620, 340), 1)    # inside draw_rect
    check("draw pile click fires draw_card",
          len(received_actions) == 1 and received_actions[0][0] == "draw_card")

    # --- Miss (no zone) ---
    received_actions.clear()
    ih.handle_mouse_click((0, 0), 1)
    check("click outside all zones fires nothing", len(received_actions) == 0)

    # --- Right-click ignored ---
    received_actions.clear()
    ih.handle_mouse_click((120, 440), 3)    # right click
    check("right click ignored", len(received_actions) == 0)

    # --- Input disabled blocks card click ---
    ih.set_input_enabled(False)
    received_actions.clear()
    ih.handle_mouse_click((120, 440), 1)
    check("card click blocked when input disabled", len(received_actions) == 0)
    ih.set_input_enabled(True)

    # --- Hover detection ---
    received_actions.clear()
    ih.handle_mouse_motion((130, 450))      # inside card_zone
    check("hover enter fires hover_changed",
          any(a[0] == "hover_changed" for a in received_actions))
    check("hover card index is 0",
          ih.get_hover_card_index() == 0)

    received_actions.clear()
    ih.handle_mouse_motion((130, 450))      # same position — no change
    check("no duplicate hover_changed on same position",
          not any(a[0] == "hover_changed" for a in received_actions))

    received_actions.clear()
    ih.handle_mouse_motion((0, 0))          # left card
    check("hover exit fires hover_changed with None",
          any(a[0] == "hover_changed" and a[1].get("card_index") is None
              for a in received_actions))
    check("hover card index is None after leaving", ih.get_hover_card_index() is None)

    # --- Color selection zone (priority over card) ---
    color_rect = pygame.Rect(50, 50, 80, 80)
    ih.update_color_zones([(color_rect, CardColor.RED)])
    received_actions.clear()
    ih.handle_mouse_click((70, 70), 1)      # inside color_rect
    check("color zone fires color_chosen",
          len(received_actions) == 1 and received_actions[0][0] == "color_chosen")
    check("color_chosen carries CardColor.RED",
          received_actions[0][1].get("color") == CardColor.RED)
    ih.update_color_zones([])

    # --- Target zone ---
    target_rect = pygame.Rect(200, 200, 80, 80)
    ih.update_target_zones([(target_rect, 2)])
    received_actions.clear()
    ih.handle_mouse_click((240, 240), 1)
    check("target zone fires target_chosen",
          received_actions[0][0] == "target_chosen")
    check("target_chosen carries player_id=2",
          received_actions[0][1].get("player_id") == 2)
    ih.update_target_zones([])

    # --- Direction zone ---
    dir_rect = pygame.Rect(300, 300, 80, 80)
    ih.update_direction_zones([(dir_rect, TurnDirection.FORWARD)])
    received_actions.clear()
    ih.handle_mouse_click((340, 340), 1)
    check("direction zone fires direction_chosen",
          received_actions[0][0] == "direction_chosen")
    check("direction_chosen carries TurnDirection.FORWARD",
          received_actions[0][1].get("direction") == TurnDirection.FORWARD)
    ih.update_direction_zones([])

    # --- Reaction button ---
    react_rect = pygame.Rect(500, 500, 120, 60)
    ih.update_button_zones({"reaction_btn": react_rect})
    received_actions.clear()
    ih.handle_mouse_click((560, 530), 1)
    check("reaction button fires react_rule8",
          received_actions[0][0] == "react_rule8")

    # --- Spacebar shortcut ---
    received_actions.clear()
    ih.handle_key_press(pygame.K_SPACE)
    check("spacebar fires react_rule8", received_actions[0][0] == "react_rule8")

    # --- get_mouse_position ---
    ih.handle_mouse_motion((777, 888))
    check("get_mouse_position updated", ih.get_mouse_position() == (777, 888))


# =============================================================================
# 3. Integration test — GameClient + real server
# =============================================================================

def test_integration():
    print("\n── Integration (server + GameStateManager) ──────────────")
    from client.controller.network_client import NetworkClient
    from client.state.game_state import GameStateManager
    from shared.message_protocol import JoinRoom
    from shared.enums import GameState

    gsm = GameStateManager()
    gsm.set_local_username("TestPlayer")

    client = NetworkClient(host="127.0.0.1", port=5000)
    connected = client.connect()
    check("client connects to server", connected)

    if not connected:
        print("  (skipping remaining integration tests — server not reachable)")
        return

    # Send JoinRoom
    ok = client.send_message(JoinRoom(username="TestPlayer"))
    check("JoinRoom sent", ok)

    # Wait for LOBBY_UPDATE
    deadline = time.time() + 3.0
    lobby_received = False
    while time.time() < deadline:
        for msg in client.get_messages():
            from shared.enums import MessageType
            if msg.message_type == MessageType.EVENT_BROADCAST:
                if msg.event_name == "LOBBY_UPDATE":
                    gsm.handle_event("LOBBY_UPDATE", msg.event_data)
                    lobby_received = True
        if lobby_received:
            break
        time.sleep(0.05)

    check("LOBBY_UPDATE received", lobby_received)
    check("local_player_id detected from lobby",
          gsm.get_local_player_id() is not None)
    check("game_state is LOBBY", gsm.get_game_state() == GameState.LOBBY)
    check("at least 1 player in lobby", len(gsm.get_lobby_players()) >= 1)

    local_pid = gsm.get_local_player_id()
    host_pid  = gsm.get_host_client_id()
    check("first joiner is host", local_pid == host_pid and gsm.is_host())

    client.disconnect()
    print("  (disconnected)")


# =============================================================================
# Entry point
# =============================================================================

def start_server():
    """Start a local server in a daemon thread for the integration test."""
    from server.main import GameServer
    def _run():
        srv = GameServer(host="127.0.0.1", port=5000)
        srv.start()
        try:
            while True:
                time.sleep(1)
        except Exception:
            pass
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(0.6)   # let the socket bind


if __name__ == "__main__":
    run_server   = "--server" in sys.argv
    auto_server  = "--full"   in sys.argv

    print("=" * 56)
    print("  M4 Test Suite — Custom UNO Online")
    print("=" * 56)

    test_game_state_manager()
    test_input_handler()

    if auto_server:
        print("\n── Starting local server for integration test ───────────")
        start_server()
        test_integration()
    elif run_server:
        test_integration()
    else:
        print("\n  (skip integration — pass --server if server is running,")
        print("   or --full to auto-start one)")

    print("\n" + "=" * 56)
    total = _results["pass"] + _results["fail"]
    print(f"  Results: {_results['pass']}/{total} passed", end="")
    if _results["fail"]:
        print(f"  ← {_results['fail']} FAILED")
    else:
        print("  ✓ All passed")
    print("=" * 56)
    sys.exit(0 if _results["fail"] == 0 else 1)
