"""Pinball — your bullets bounce many more times."""
from .powerup import PowerUp


class Pinball(PowerUp):
    NAME = "Pinball"
    COLOR = (255, 100, 220)
    ICON = "K"
    DURATION_MS = 7000

    def modify_max_bounces(self, base: int) -> int:
        return base + 6
