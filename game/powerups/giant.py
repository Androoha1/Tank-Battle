"""Giant effect — bigger, slower tank that can soak one hit."""
from .effect import PlayerEffect


class GiantEffect(PlayerEffect):
    NAME = "Giant"
    COLOR = (255, 150, 80)
    ICON = "H"
    DURATION_MS = 9000
    absorbs_hit = True

    def __init__(self) -> None:
        super().__init__()
        self._charges = 1

    def modify_size(self, base: int) -> int:
        return int(base * 1.6)

    def modify_speed(self, base: float) -> float:
        return base * 0.72

    def try_consume_hit(self) -> bool:
        if self._charges > 0:
            self._charges -= 1
            self._active_elapsed = self.DURATION_MS
            return True
        return False
