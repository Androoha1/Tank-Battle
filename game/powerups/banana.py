"""Banana — for a few seconds, your tank drops slippery peels behind itself."""
from .powerup import PowerUp
from ..entities.banana_peel import BananaPeel


class Banana(PowerUp):
    NAME = "Banana"
    COLOR = (255, 230, 80)
    ICON = "Y"
    DURATION_MS = 5000
    DROP_INTERVAL_MS = 380

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._drop_timer = 0.0

    def on_tick(self, player, ctx, dt: float) -> None:
        self._drop_timer -= dt
        if self._drop_timer <= 0:
            ctx.add_banana(BananaPeel(player.x, player.y, player))
            self._drop_timer = self.DROP_INTERVAL_MS
