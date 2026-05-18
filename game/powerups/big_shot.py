"""Big Shot weapon — a single large, slow projectile."""
from .powerup import PowerUp


class BigShot(PowerUp):
    NAME = "Big Shot"
    COLOR = (255, 110, 110)
    ICON = "B"
    DURATION_MS = 7000
    IS_WEAPON = True

    def shoot_pattern(self) -> list[float]:
        return [0.0]

    def shoot_kind(self) -> str:
        return "big"

    def modify_cooldown(self, base: float) -> float:
        return base * 1.6
