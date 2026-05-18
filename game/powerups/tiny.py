"""Tiny — shrinks the tank, making it harder to hit and a little nippier."""
from .powerup import PowerUp


class Tiny(PowerUp):
    NAME = "Tiny"
    COLOR = (170, 240, 180)
    ICON = "T"
    DURATION_MS = 8000

    def modify_size(self, base: int) -> int:
        return max(14, int(base * 0.6))

    def modify_speed(self, base: float) -> float:
        return base * 1.15
