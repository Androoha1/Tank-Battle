from .effect import PlayerEffect


class FireRateEffect(PlayerEffect):
    NAME = "Fire Rate"
    COLOR = (255, 180, 90)
    ICON = "F"

    def modify_cooldown(self, base: float) -> float:
        return base * 0.5
