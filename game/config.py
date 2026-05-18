"""Centralised configuration constants."""

# Window
WIDTH = 1280
HEIGHT = 720
FPS = 60
HUD_HEIGHT = 56

# Palette
BLACK = (10, 12, 18)
DARK_BG = (18, 22, 32)
GRID = (28, 34, 48)
WHITE = (235, 235, 240)
HUD_BG = (16, 18, 26)
HUD_LINE = (60, 70, 90)

WALL_COLOR = (84, 96, 120)
WALL_HIGHLIGHT = (140, 156, 180)
WALL_SHADOW = (40, 48, 64)

# Player colour sets (primary / secondary / accent)
PLAYER_COLORS = [
    {"primary": (235, 86, 86),  "secondary": (170, 38, 38),  "accent": (255, 210, 150), "name": "RED"},
    {"primary": (86, 168, 235), "secondary": (38, 110, 180), "accent": (190, 230, 255), "name": "BLUE"},
    {"primary": (130, 220, 120), "secondary": (60, 150, 70), "accent": (210, 255, 190), "name": "GREEN"},
    {"primary": (230, 200, 90), "secondary": (190, 150, 30), "accent": (255, 240, 180), "name": "YELLOW"},
]

# Tank physics
TANK_SIZE = 36
TANK_SPEED = 2.6
TANK_REVERSE_RATIO = 0.65
TANK_ROT_SPEED = 2.8           # degrees per frame
SHOT_COOLDOWN_MS = 550

# Shot physics
SHOT_RADIUS = 5
SHOT_SPEED = 6.4
SHOT_MAX_BOUNCES = 2
SHOT_LIFETIME_MS = 6000
SHOT_OWNER_GRACE_MS = 160

# Power-ups
POWERUP_RADIUS = 14
POWERUP_SPAWN_INTERVAL_MS = 6500
POWERUP_DURATION_MS = 8000
MAX_POWERUPS_ON_MAP = 3

# Rounds
ROUND_END_DELAY_MS = 1800
