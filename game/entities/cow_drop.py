"""Cow Drop — a global hazard. A cow plummets from off-screen onto a random
map position, telegraphed by a growing shadow. Anything in the blast radius
when it lands is squished.
"""
import math
import random
import pygame as pg

from .entity import Entity
from .particle import Particle
from .shockwave import Shockwave


class CowDrop(Entity):
    WARNING_MS = 1500
    HIT_FLASH_MS = 250
    FADE_MS = 1200
    KILL_RADIUS = 56

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._phase = "warning"
        self._timer = self.WARNING_MS
        self._rot_speed = random.uniform(180, 540)  # deg/sec during fall
        self._rot = random.uniform(0, 360)

    @property
    def rect(self) -> pg.Rect:
        r = self.KILL_RADIUS
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    def update(self, dt: float, ctx) -> None:
        self._timer -= dt
        if self._phase == "warning":
            self._rot = (self._rot + self._rot_speed * dt * 0.001) % 360
            if self._timer <= 0:
                self._impact(ctx)
                self._phase = "hit"
                self._timer = self.HIT_FLASH_MS
        elif self._phase == "hit":
            if self._timer <= 0:
                self._phase = "fade"
                self._timer = self.FADE_MS
        else:
            if self._timer <= 0:
                self.kill()

    def _impact(self, ctx) -> None:
        ctx.request_shake(intensity=18, duration_ms=520)
        ctx.request_flash((255, 250, 220), 90)
        for p in ctx.players:
            if not p.alive():
                continue
            dx = p.x - self._x
            dy = p.y - self._y
            if dx * dx + dy * dy <= self.KILL_RADIUS * self.KILL_RADIUS:
                p.kill_player(ctx)
        # impact debris
        for _ in range(36):
            ctx.add_particle(Particle(
                self._x, self._y, (210, 180, 140),
                lifetime=random.randint(450, 800),
                size=random.randint(3, 5),
            ))
        ctx.add_shockwave(Shockwave(
            self._x, self._y, color=(255, 250, 220),
            max_radius=150, speed=0.32, thickness=4,
        ))
        ctx.audio.play_explosion()

    # ------------------------------------------------------------------ draw
    def draw(self, surface: pg.Surface) -> None:
        if self._phase == "warning":
            self._draw_falling(surface)
        elif self._phase == "hit":
            self._draw_cow(surface, self._x, self._y, 60, rot=0, alpha=255)
        else:
            t = max(0.0, self._timer / self.FADE_MS)
            self._draw_cow(surface, self._x, self._y, 60, rot=0, alpha=int(255 * t))

    def _draw_falling(self, surface: pg.Surface) -> None:
        progress = 1.0 - (self._timer / self.WARNING_MS)
        # growing ground shadow
        shadow_r = int(18 + 38 * progress)
        shadow_alpha = int(70 + 130 * progress)
        sh = pg.Surface((shadow_r * 2 + 8, shadow_r * 2 + 8), pg.SRCALPHA)
        pg.draw.ellipse(sh, (0, 0, 0, shadow_alpha),
                        (4, 4, shadow_r * 2, shadow_r * 2))
        surface.blit(sh, (int(self._x - shadow_r - 4),
                          int(self._y - shadow_r - 4)))

        # falling cow descending from above the screen
        fall_height = 260
        cow_y = self._y - fall_height * (1.0 - progress)
        cow_size = int(28 + 32 * progress)
        self._draw_cow(surface, self._x, cow_y, cow_size, rot=self._rot, alpha=255)

    @staticmethod
    def _draw_cow(surface: pg.Surface, cx: float, cy: float,
                  size: int, rot: float = 0.0, alpha: int = 255) -> None:
        # Top-down cartoon cow: white blob with black spots, four nubby legs,
        # a small head, and pink ears + nose. Drawn onto a temporary surface
        # so we can rotate the whole thing as it tumbles.
        canvas = pg.Surface((size * 2 + 12, size * 2 + 12), pg.SRCALPHA)
        ccx, ccy = canvas.get_width() // 2, canvas.get_height() // 2

        body_w = int(size * 1.35)
        body_h = int(size * 0.95)

        # legs (under body)
        for off in ((-0.32, -0.42), (0.32, -0.42), (-0.32, 0.42), (0.32, 0.42)):
            lx = ccx + int(body_w * off[0])
            ly = ccy + int(body_h * off[1])
            pg.draw.rect(canvas, (190, 190, 195, alpha),
                         (lx - 4, ly - 3, 8, 10), border_radius=2)

        # body
        body_rect = pg.Rect(0, 0, body_w, body_h)
        body_rect.center = (ccx, ccy)
        pg.draw.ellipse(canvas, (245, 245, 245, alpha), body_rect)
        pg.draw.ellipse(canvas, (40, 40, 40, alpha), body_rect, 2)

        # spots
        spot_a = (40, 40, 40, alpha)
        pg.draw.ellipse(canvas, spot_a,
                        (ccx - body_w // 3, ccy - body_h // 3,
                         body_w // 3, body_h // 3))
        pg.draw.ellipse(canvas, spot_a,
                        (ccx + 2, ccy + 2,
                         body_w // 4, body_h // 4))
        pg.draw.ellipse(canvas, spot_a,
                        (ccx - body_w // 5, ccy + body_h // 5,
                         body_w // 5, body_h // 6))

        # head
        head_r = int(size * 0.34)
        head_cx = ccx + body_w // 2 - 6
        head_cy = ccy
        pg.draw.circle(canvas, (245, 245, 245, alpha), (head_cx, head_cy), head_r)
        pg.draw.circle(canvas, (40, 40, 40, alpha), (head_cx, head_cy), head_r, 2)
        # ears
        pg.draw.ellipse(canvas, (255, 180, 200, alpha),
                        (head_cx - head_r, head_cy - head_r - 2, 8, 6))
        pg.draw.ellipse(canvas, (255, 180, 200, alpha),
                        (head_cx + head_r - 8, head_cy - head_r - 2, 8, 6))
        # snout
        pg.draw.ellipse(canvas, (255, 200, 210, alpha),
                        (head_cx + 2, head_cy - 3, 10, 8))
        # nostrils
        pg.draw.circle(canvas, (40, 40, 40, alpha),
                       (head_cx + 5, head_cy), 1)
        pg.draw.circle(canvas, (40, 40, 40, alpha),
                       (head_cx + 9, head_cy), 1)

        if rot:
            canvas = pg.transform.rotate(canvas, rot)
        surface.blit(canvas, canvas.get_rect(center=(int(cx), int(cy))).topleft)
