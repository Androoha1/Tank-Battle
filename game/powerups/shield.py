"""Shield effect — absorbs a single hit before expiring."""
from .effect import PlayerEffect


class ShieldEffect(PlayerEffect):
    NAME = "Shield"
    COLOR = (140, 220, 255)
    ICON = "D"
    DURATION_MS = 10000
    absorbs_hit = True

    def __init__(self) -> None:
        super().__init__()
        self._charges = 1

    def try_consume_hit(self) -> bool:
        if self._charges > 0:
            self._charges -= 1
            self._active_elapsed = self.DURATION_MS
            return True
        return False
