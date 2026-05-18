"""Drunk — debuff applied to OTHER players: left/right steering is swapped."""
from .powerup import PowerUp


class Drunk(PowerUp):
    NAME = "Drunk"
    COLOR = (255, 160, 80)
    ICON = "X"
    DURATION_MS = 4500
    swaps_steering = True

    def apply(self, player, ctx) -> None:
        # Applies to OTHER living players — the picker stays sober.
        for other in ctx.players:
            if other is player or not other.alive():
                continue
            effect = self.__class__(0, 0)
            effect.activate()
            other.add_effect(effect)
