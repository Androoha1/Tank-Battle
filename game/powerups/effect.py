"""Strategy base class for active player effects (buffs and debuffs)."""
from abc import ABC

from .. import config


class PlayerEffect(ABC):
    NAME: str = "Effect"
    COLOR: tuple[int, int, int] = (220, 220, 220)
    ICON: str = "?"
    DURATION_MS: int = config.POWERUP_DURATION_MS
    IS_WEAPON: bool = False

    absorbs_hit: bool = False
    swaps_steering: bool = False
    phases_walls: bool = False

    def __init__(self) -> None:
        self._active_elapsed: float = 0.0

    def tick_effect(self, dt: float) -> bool:
        """Advance the active timer; returns True once expired."""
        self._active_elapsed += dt
        return self._active_elapsed >= self.DURATION_MS

    @property
    def remaining_ratio(self) -> float:
        return max(0.0, 1.0 - self._active_elapsed / self.DURATION_MS)

    @classmethod
    def dispatch(cls, picker, ctx) -> None:
        """Called when the pickup is collected. Default: attach a fresh
        instance of this effect to the picker. Subclasses override for
        debuffs, teleports, etc."""
        picker.add_effect(cls())

    def modify_speed(self, base: float) -> float:
        return base

    def modify_cooldown(self, base: float) -> float:
        return base

    def modify_size(self, base: int) -> int:
        return base

    def modify_alpha(self, base: int) -> int:
        return base

    def modify_max_bounces(self, base: int) -> int:
        return base

    def shoot_pattern(self) -> list[float] | None:
        """Return a list of angle offsets (deg) to override the standard single shot."""
        return None

    def shoot_kind(self) -> str | None:
        """Return a non-default shot kind ('big', 'mine', ...) or None."""
        return None

    def shoot_angle_offset(self) -> float:
        """Static angle added to the player's facing when firing (Backshot)."""
        return 0.0

    def rotation_per_tick(self) -> float:
        """Auto-rotation in degrees/frame applied each tick (Spinner)."""
        return 0.0

    def try_consume_hit(self) -> bool:
        """If this effect absorbs hits, consume one charge and return True."""
        return False
