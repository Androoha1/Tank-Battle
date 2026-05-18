"""Mine weapon effect — pressing 'shoot' drops a proximity mine."""
from .effect import PlayerEffect


class MinePowerEffect(PlayerEffect):
    NAME = "Mine"
    COLOR = (200, 80, 80)
    ICON = "M"
    DURATION_MS = 9000
    IS_WEAPON = True

    def shoot_pattern(self) -> list[float]:
        return [0.0]

    def shoot_kind(self) -> str:
        return "mine"

    def modify_cooldown(self, base: float) -> float:
        return base * 1.4
