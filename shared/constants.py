"""
Game constants shared between Client and Server.
Aligned with functional requirements: Host-Authoritative, Custom Rules, Stacking.
"""

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Game configuration - Room settings
MAX_PLAYERS = 4
MIN_PLAYERS = 2
HAND_SIZE = 7
DECK_SIZE = 108

# Deck composition (standard UNO deck)
CARDS_PER_COLOR = 25  # 0 + 1-9 (2 each) + Skip/Reverse/Draw2 (2 each)
NUM_COLORS = 4  # Red, Yellow, Green, Blue
WILD_CARDS = 4  # Wild
WILD_DRAW_FOUR_CARDS = 4  # Wild Draw Four

# Card dimensions
CARD_WIDTH = 60
CARD_HEIGHT = 90

# Colors (RGB tuples)
COLOR_RED = (220, 20, 60)
COLOR_YELLOW = (255, 215, 0)
COLOR_GREEN = (34, 139, 34)
COLOR_BLUE = (65, 105, 225)
COLOR_WILD = (50, 50, 50)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

# Server networking
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5000
MAX_MESSAGE_SIZE = 4096
MESSAGE_TIMEOUT = 30  # seconds

# Custom Rules - Configuration
# Rule 0: Play in Order (pass entire hand in chosen direction, keep turn)
ENABLE_RULE_0 = True

# Rule 7: Sevens (swap hands with target player)
ENABLE_RULE_7 = True

# Rule 8: Eights (reaction event - all players click to react)
ENABLE_RULE_8 = True
REACTION_EVENT_TIMEOUT = 3.0  # seconds for players to respond to Eight
REACTION_EVENT_PENALTY = 2  # cards to draw if last to respond

# Stacking Rule: +2/+4 accumulation
ENABLE_STACKING = True
DRAW_TWO_PENALTY = 2  # cards
DRAW_FOUR_PENALTY = 4  # cards

# Draw and Play: If no legal move, draw one card
ALLOW_DRAW_PLAY_SAME_TURN = True

# Reverse behavior in 2-player game
# True = Reverse acts as Skip, False = standard rule
REVERSE_AS_SKIP_TWO_PLAYER = False

# Win condition: Cannot use action cards as final card
CANNOT_WIN_WITH_ACTION_CARD = True

# Host authoritative state validation
VALIDATE_CARD_PLAY = True  # Host must validate all plays
VALIDATE_TURN_ORDER = True  # Host must enforce turn order
VALIDATE_STACKING_RULES = True  # Host must validate stacking
BROADCAST_GAME_STATE_INTERVAL = 0.1  # seconds between state broadcasts

