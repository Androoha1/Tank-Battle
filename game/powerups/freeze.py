"""Freeze power-up — slows all OTHER players for a short window.

This is the only power-up whose effect is a *debuff*: when picked up, the
instance is attached to every other living player rather than to the picker.
"""
from .powerup import PowerUp


class Freeze(PowerUp):
    NAME = "Freeze"
    COLOR = (130, 200, 255)
    ICON = "Z"
    DURATION_MS = 3500

    def apply(self, player, ctx) -> None:
        # Apply to OTHER players instead of the picker.
        for other in ctx.players:
            if other is player or not other.alive():
                continue
            effect = self.__class__(0, 0)
            effect.activate()
            other.add_effect(effect)

    def modify_speed(self, base: float) -> float:
        return base * 0.4

    def modify_cooldown(self, base: float) -> float:
        return base * 1.8
