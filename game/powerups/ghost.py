"""Ghost — phase through walls; tank renders semi-transparent."""
from .powerup import PowerUp


class Ghost(PowerUp):
    NAME = "Ghost"
    COLOR = (210, 220, 255)
    ICON = "G"
    DURATION_MS = 5000
    phases_walls = True

    def modify_alpha(self, base: int) -> int:
        return 110
