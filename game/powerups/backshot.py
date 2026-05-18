"""Backshot effect — bullets come out of the BACK of the tank."""
from .effect import PlayerEffect


class BackshotEffect(PlayerEffect):
    NAME = "Backshot"
    COLOR = (255, 220, 120)
    ICON = "U"
    DURATION_MS = 7000

    def shoot_angle_offset(self) -> float:
        return 180.0
