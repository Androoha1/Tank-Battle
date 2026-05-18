"""Teleport effect — instantly relocate the picker to a random spawn point."""
from .effect import PlayerEffect
from ..entities.particle import Particle


class TeleportEffect(PlayerEffect):
    NAME = "Teleport"
    COLOR = (200, 130, 255)
    ICON = "P"
    DURATION_MS = 400  # short residual effect, mostly cosmetic

    @classmethod
    def dispatch(cls, picker, ctx) -> None:
        spawn = ctx.random_spawn_point()
        if spawn is None:
            return
        sx, sy, sa = spawn
        # Particle burst at the old position.
        for _ in range(22):
            ctx.add_particle(Particle(picker.x, picker.y, cls.COLOR, lifetime=400, size=4))
        picker.teleport_to(sx, sy, sa)
        # Particle burst at the new position.
        for _ in range(22):
            ctx.add_particle(Particle(sx, sy, cls.COLOR, lifetime=400, size=4))
        # Short cosmetic effect so the badge briefly appears.
        picker.add_effect(cls())
