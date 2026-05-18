"""Ghost effect — phase through walls; tank renders semi-transparent."""
from .effect import PlayerEffect


class GhostEffect(PlayerEffect):
    NAME = "Ghost"
    COLOR = (210, 220, 255)
    ICON = "G"
    DURATION_MS = 5000
    phases_walls = True

    def modify_alpha(self, base: int) -> int:
        return 110
