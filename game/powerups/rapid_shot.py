from .powerup import PowerUp


class RapidShot(PowerUp):
    """Weapon power-up: dramatically reduced cooldown for a short burst."""
    NAME = "Rapid Shot"
    COLOR = (255, 90, 160)
    ICON = "R"
    DURATION_MS = 6000
    IS_WEAPON = True

    def modify_cooldown(self, base: float) -> float:
        return base * 0.18

    def shoot_pattern(self) -> list[float]:
        return [0.0]
