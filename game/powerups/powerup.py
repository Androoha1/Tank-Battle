"""Abstract base class for power-ups.

A single PowerUp subclass plays two roles: as a *pickup* entity rendered in
the world, and as an *active effect* on a Player. When picked up, the
controller creates a fresh effect instance via :meth:`apply` and the world
sprite is discarded.

Subclasses override one or more of :meth:`modify_speed`,
:meth:`modify_cooldown`, and :meth:`shoot_pattern` to express their effect.
"""
from abc import ABC
import math
import pygame as pg

from ..entities.entity import Entity
from .. import config


class PowerUp(Entity, ABC):
    NAME: str = "PowerUp"
    COLOR: tuple[int, int, int] = (220, 220, 220)
    ICON: str = "?"
    DURATION_MS: int = config.POWERUP_DURATION_MS
    IS_WEAPON: bool = False

    _font_cache: pg.font.Font | None = None

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._radius = config.POWERUP_RADIUS
        self._spin = 0.0
        self._bob = 0.0
        self._active_elapsed = 0
        self._is_active = False

    # ---- pickup-entity interface ----
    @property
    def rect(self) -> pg.Rect:
        r = self._radius + 4
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    def update(self, dt: float, ctx) -> None:
        self._spin = (self._spin + dt * 0.18) % 360.0
        self._bob = (self._bob + dt * 0.005) % math.tau

    def draw(self, surface: pg.Surface) -> None:
        if PowerUp._font_cache is None:
            PowerUp._font_cache = pg.font.SysFont("arialblack", 18, bold=True)
        font = PowerUp._font_cache

        cx = int(self._x)
        cy = int(self._y + math.sin(self._bob) * 3)

        # halo
        halo_r = self._radius * 3
        halo = pg.Surface((halo_r * 2, halo_r * 2), pg.SRCALPHA)
        pg.draw.circle(halo, (*self.COLOR, 35), (halo_r, halo_r), halo_r)
        pg.draw.circle(halo, (*self.COLOR, 80), (halo_r, halo_r), int(halo_r * 0.65))
        surface.blit(halo, (cx - halo_r, cy - halo_r))

        # body
        pg.draw.circle(surface, (250, 250, 250), (cx, cy), self._radius)
        pg.draw.circle(surface, self.COLOR, (cx, cy), self._radius - 3)
        pg.draw.circle(surface, (255, 255, 255), (cx, cy), self._radius, 1)

        # icon
        icon = font.render(self.ICON, True, (250, 250, 250))
        surface.blit(icon, icon.get_rect(center=(cx, cy)))

    # ---- active-effect interface ----
    def activate(self) -> None:
        self._is_active = True
        self._active_elapsed = 0

    def tick_effect(self, dt: float) -> bool:
        """Advance the active timer; returns True once expired."""
        self._active_elapsed += dt
        return self._active_elapsed >= self.DURATION_MS

    @property
    def remaining_ratio(self) -> float:
        return max(0.0, 1.0 - self._active_elapsed / self.DURATION_MS)

    def apply(self, player, ctx) -> None:
        """Spawn a fresh effect instance and attach it to the player.

        Subclasses may override to apply effects to OTHER players (debuffs).
        """
        effect = self.__class__(0, 0)
        effect.activate()
        player.add_effect(effect)

    # ---- polymorphic stat/weapon modifiers (default: no-op) ----
    def modify_speed(self, base: float) -> float:
        return base

    def modify_cooldown(self, base: float) -> float:
        return base

    def shoot_pattern(self) -> list[float] | None:
        """Return a list of angle offsets (deg) to override the standard single shot."""
        return None

    def shoot_kind(self) -> str | None:
        """Return a non-default shot kind ('big', 'mine', ...) or None."""
        return None

    # ---- shield-style hit absorption ----
    absorbs_hit: bool = False

    def try_consume_hit(self) -> bool:
        """If this effect absorbs hits, consume one charge and return True."""
        return False

    # ---- fun modifiers (default: no-op) ----
    swaps_steering: bool = False  # Drunk
    phases_walls: bool = False    # Ghost

    def modify_size(self, base: int) -> int:
        """Effective tank size (used for hitbox + drawing)."""
        return base

    def modify_alpha(self, base: int) -> int:
        """Effective draw alpha for the tank sprite."""
        return base

    def rotation_per_tick(self) -> float:
        """Auto-rotation in degrees/frame applied each tick (Spinner)."""
        return 0.0

    def shoot_angle_offset(self) -> float:
        """Static angle added to the player's facing when firing (Backshot)."""
        return 0.0

    def modify_max_bounces(self, base: int) -> int:
        """Effective bullet bounce count (Pinball)."""
        return base
