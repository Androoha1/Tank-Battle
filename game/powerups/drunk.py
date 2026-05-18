"""Drunk effect — debuff applied to OTHER players: left/right steering is swapped."""
from .effect import PlayerEffect


class DrunkEffect(PlayerEffect):
    NAME = "Drunk"
    COLOR = (255, 160, 80)
    ICON = "X"
    DURATION_MS = 4500
    swaps_steering = True

    @classmethod
    def dispatch(cls, picker, ctx) -> None:
        for other in ctx.players:
            if other is picker or not other.alive():
                continue
            other.add_effect(cls())
