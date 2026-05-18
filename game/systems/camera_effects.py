"""Camera shake and screen-flash effects."""
import random


class CameraEffects:
    """Tracks shake and flash state; produces a per-frame offset for the blit."""

    def __init__(self) -> None:
        self._shake_intensity = 0.0
        self._shake_timer = 0.0
        self._shake_duration = 0.0
        self._flash_color: tuple[int, int, int] | None = None
        self._flash_alpha: int = 0

    def request_shake(self, intensity: float, duration_ms: float) -> None:
        if intensity > self._shake_intensity or self._shake_timer <= 0:
            self._shake_intensity = intensity
            self._shake_timer = duration_ms
            self._shake_duration = duration_ms

    def request_flash(self, color: tuple[int, int, int], alpha: int) -> None:
        self._flash_color = color
        self._flash_alpha = alpha

    def update(self, dt: float) -> None:
        if self._shake_timer > 0:
            self._shake_timer = max(0.0, self._shake_timer - dt)
        if self._flash_alpha > 0:
            self._flash_alpha = max(0, int(self._flash_alpha - dt * 0.35))

    def reset(self) -> None:
        self._shake_intensity = 0.0
        self._shake_timer = 0.0
        self._flash_alpha = 0

    @property
    def shake_offset(self) -> tuple[int, int]:
        if self._shake_timer > 0 and self._shake_duration > 0:
            t = self._shake_timer / self._shake_duration
            amp = self._shake_intensity * t
            return (int(random.uniform(-amp, amp)), int(random.uniform(-amp, amp)))
        return (0, 0)

    @property
    def flash_alpha(self) -> int:
        return self._flash_alpha

    @property
    def flash_color(self) -> tuple[int, int, int] | None:
        return self._flash_color
