"""Freeze effect — slows all OTHER players for a short window.

This is the only power-up whose effect is a *debuff*: when picked up, the
effect is attached to every other living player rather than to the picker.
"""
from .effect import PlayerEffect


class FreezeEffect(PlayerEffect):
    NAME = "Freeze"
    COLOR = (130, 200, 255)
    ICON = "Z"
    DURATION_MS = 3500

    @classmethod
    def dispatch(cls, picker, ctx) -> None:
        for other in ctx.players:
            if other is picker or not other.alive():
                continue
            other.add_effect(cls())

    def modify_speed(self, base: float) -> float:
        return base * 0.4

    def modify_cooldown(self, base: float) -> float:
        return base * 1.8
