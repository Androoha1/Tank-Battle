"""Shotgun effect — each shot fires 5 bullets in a wide spread."""
from .effect import PlayerEffect


class ShotgunEffect(PlayerEffect):
    NAME = "Shotgun"
    COLOR = (240, 120, 60)
    ICON = "W"
    DURATION_MS = 6500
    IS_WEAPON = True

    def shoot_pattern(self) -> list[float]:
        return [-26.0, -13.0, 0.0, 13.0, 26.0]

    def modify_cooldown(self, base: float) -> float:
        return base * 1.15
