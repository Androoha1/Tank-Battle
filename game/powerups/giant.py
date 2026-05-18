"""Giant — bigger, slower tank that can soak one hit."""
from .powerup import PowerUp


class Giant(PowerUp):
    NAME = "Giant"
    COLOR = (255, 150, 80)
    ICON = "H"
    DURATION_MS = 9000
    absorbs_hit = True

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._charges = 1

    def modify_size(self, base: int) -> int:
        return int(base * 1.6)

    def modify_speed(self, base: float) -> float:
        return base * 0.72

    def try_consume_hit(self) -> bool:
        if self._charges > 0:
            self._charges -= 1
            self._active_elapsed = self.DURATION_MS  # expire after the hit
            return True
        return False
