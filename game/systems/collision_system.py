"""Shot-to-player collision detection and resolution."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .world import World


class CollisionSystem:
    """Processes shot↔player collisions for one tick.

    Called after all shots have been updated (and already-dead shots removed),
    so every shot in *world.shots* is alive when this runs.
    """

    def process(self, world: "World", players: list, ctx) -> None:
        for s in world.shots[:]:
            if not s.alive():
                continue
            for player in players:
                if not player.alive():
                    continue
                # No friendly fire — owner's bullets never hit them.
                if player is s.owner:
                    continue
                if s.rect.colliderect(player.rect):
                    player.kill_player(ctx)
                    s.kill()
                    break
            if not s.alive() and s in world.shots:
                world.shots.remove(s)
