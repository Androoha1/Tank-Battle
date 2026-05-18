"""Spinner — debuff applied to OTHER players: forces them to auto-rotate."""
from .powerup import PowerUp


class Spinner(PowerUp):
    NAME = "Spinner"
    COLOR = (255, 80, 230)
    ICON = "O"
    DURATION_MS = 4000

    def apply(self, player, ctx) -> None:
        # Spin the OTHER player(s); picker stays still.
        for other in ctx.players:
            if other is player or not other.alive():
                continue
            effect = self.__class__(0, 0)
            effect.activate()
            other.add_effect(effect)

    def rotation_per_tick(self) -> float:
        return 6.0  # degrees per frame; about double the manual rotate speed
