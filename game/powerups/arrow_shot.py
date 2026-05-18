from .effect import PlayerEffect


class ArrowShotEffect(PlayerEffect):
    """Weapon effect: fires three bullets in an arrow spread."""
    NAME = "Arrow Shot"
    COLOR = (180, 120, 255)
    ICON = "A"
    DURATION_MS = 7000
    IS_WEAPON = True

    def shoot_pattern(self) -> list[float]:
        return [-13.0, 0.0, 13.0]

    def modify_cooldown(self, base: float) -> float:
        return base * 0.95
