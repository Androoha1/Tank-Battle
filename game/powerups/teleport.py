"""Teleport — instantly relocate the picker to a random spawn point."""
from .powerup import PowerUp
from ..entities.particle import Particle


class Teleport(PowerUp):
    NAME = "Teleport"
    COLOR = (200, 130, 255)
    ICON = "P"
    DURATION_MS = 400  # short residual effect, mostly cosmetic

    def apply(self, player, ctx) -> None:
        spawn = ctx.random_spawn_point()
        if spawn is None:
            return
        sx, sy, sa = spawn
        # Particle burst at the old position.
        for _ in range(22):
            ctx.add_particle(Particle(player.x, player.y, self.COLOR, lifetime=400, size=4))
        player.teleport_to(sx, sy, sa)
        # Particle burst at the new position.
        for _ in range(22):
            ctx.add_particle(Particle(sx, sy, self.COLOR, lifetime=400, size=4))
        # Short cosmetic effect on the player so the badge briefly appears.
        effect = self.__class__(0, 0)
        effect.activate()
        player.add_effect(effect)
