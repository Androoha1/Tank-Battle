"""Pinball effect — your bullets bounce many more times."""
from .effect import PlayerEffect


class PinballEffect(PlayerEffect):
    NAME = "Pinball"
    COLOR = (255, 100, 220)
    ICON = "K"
    DURATION_MS = 7000

    def modify_max_bounces(self, base: int) -> int:
        return base + 6
