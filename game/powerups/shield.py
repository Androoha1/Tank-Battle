"""Shield power-up — absorbs a single hit before expiring."""
from .powerup import PowerUp


class Shield(PowerUp):
    NAME = "Shield"
    COLOR = (140, 220, 255)
    ICON = "D"
    DURATION_MS = 10000
    absorbs_hit = True

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._charges = 1

    def try_consume_hit(self) -> bool:
        if self._charges > 0:
            self._charges -= 1
            # Expire immediately once consumed.
            self._active_elapsed = self.DURATION_MS
            return True
        return False
