from .powerup import PowerUp


class Speed(PowerUp):
    NAME = "Speed"
    COLOR = (110, 220, 255)
    ICON = "S"

    def modify_speed(self, base: float) -> float:
        return base * 1.7
