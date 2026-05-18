from .effect import PlayerEffect


class SpeedEffect(PlayerEffect):
    NAME = "Speed"
    COLOR = (110, 220, 255)
    ICON = "S"

    def modify_speed(self, base: float) -> float:
        return base * 1.7
