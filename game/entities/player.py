"""Player-controlled tank entity."""
import math
import random
import pygame as pg

from .entity import Entity
from .shot import Shot
from .particle import Particle
from .debris import Debris
from .shockwave import Shockwave
from ..events import GameEvent
from .. import config


class Player(Entity):
    """A tank. Reads keyboard input directly each frame (per sequence diagram)."""

    def __init__(
        self,
        x: float,
        y: float,
        angle_deg: float,
        colors: dict,
        controls: dict,
        name: str,
        events,
    ) -> None:
        super().__init__(x, y)
        self._angle = angle_deg
        self._colors = colors
        self._controls = controls
        self._name = name
        self._events = events
        self._size = config.TANK_SIZE
        self._base_speed = config.TANK_SPEED
        self._base_cooldown = config.SHOT_COOLDOWN_MS
        # Brief no-fire window on spawn so a still-held confirm key (e.g.
        # ENTER from the menu, which is also P2's shoot key) doesn't trigger
        # an immediate shot.
        self._cooldown = 700.0
        self._effects: list = []
        self._tread_offset = 0.0
        self._tread_phase = 0
        self._fire_flash = 0  # ms remaining

    # --- public read-only state -------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    @property
    def colors(self) -> dict:
        return self._colors

    @property
    def angle(self) -> float:
        return self._angle

    @property
    def rect(self) -> pg.Rect:
        s = self._eff_size() - 2
        return pg.Rect(int(self._x - s / 2), int(self._y - s / 2), s, s)

    @property
    def effects(self) -> list:
        return self._effects

    # --- effect plumbing --------------------------------------------------
    def add_effect(self, effect) -> None:
        """Add an effect, replacing any other instance of the same class."""
        self._effects = [e for e in self._effects if type(e) is not type(effect)]
        self._effects.append(effect)

    def _eff_speed(self) -> float:
        s = self._base_speed
        for e in self._effects:
            s = e.modify_speed(s)
        return s

    def _eff_cooldown(self) -> float:
        c = self._base_cooldown
        for e in self._effects:
            c = e.modify_cooldown(c)
        return c

    def _active_pattern(self) -> list[float]:
        for e in reversed(self._effects):
            pattern = e.shoot_pattern()
            if pattern is not None:
                return pattern
        return [0.0]

    def _active_kind(self) -> str:
        for e in reversed(self._effects):
            kind = e.shoot_kind()
            if kind is not None:
                return kind
        return "normal"

    def _eff_size(self) -> int:
        s = self._size
        for e in self._effects:
            s = e.modify_size(s)
        return s

    def _eff_alpha(self) -> int:
        a = 255
        for e in self._effects:
            a = e.modify_alpha(a)
        return max(0, min(255, a))

    def _phases_walls(self) -> bool:
        return any(getattr(e, "phases_walls", False) for e in self._effects)

    def _swaps_steering(self) -> bool:
        return any(getattr(e, "swaps_steering", False) for e in self._effects)

    def teleport_to(self, x: float, y: float, angle_deg: float) -> None:
        """Used by the Teleport powerup."""
        self._x = float(x)
        self._y = float(y)
        self._angle = float(angle_deg)

    # --- update -----------------------------------------------------------
    def update(self, dt: float, ctx) -> None:
        if not self._alive:
            return

        # Run per-frame effect behaviours (e.g. Banana dropping peels).
        for e in self._effects:
            e.on_tick(self, ctx, dt)
        # Then expire effects whose duration has run out.
        self._effects = [e for e in self._effects if not e.tick_effect(dt)]
        self._fire_flash = max(0, self._fire_flash - dt)

        keys = pg.key.get_pressed()
        c = self._controls
        left = keys[c["left"]]
        right = keys[c["right"]]
        up = keys[c["up"]]
        down = keys[c["down"]]
        shoot = keys[c["shoot"]]

        if self._swaps_steering():
            left, right = right, left

        if left:
            self._angle = (self._angle + config.TANK_ROT_SPEED) % 360
        if right:
            self._angle = (self._angle - config.TANK_ROT_SPEED) % 360

        # Spinner: forced auto-rotation on top of input.
        auto_rot = sum(e.rotation_per_tick() for e in self._effects)
        if auto_rot != 0:
            self._angle = (self._angle + auto_rot) % 360

        speed = self._eff_speed()
        move = 0.0
        if up:
            move += speed
        if down:
            move -= speed * config.TANK_REVERSE_RATIO

        if move != 0:
            rad = math.radians(self._angle)
            self._try_move(math.cos(rad) * move, -math.sin(rad) * move, ctx.walls)
            self._tread_offset = (self._tread_offset + abs(move) * 0.9) % 8.0
            self._tread_phase = (self._tread_phase + 1) % 1_000_000

        self._cooldown = max(0.0, self._cooldown - dt)
        if shoot and self._cooldown <= 0:
            self._fire(ctx)
            self._cooldown = self._eff_cooldown()
            self._fire_flash = 90

    def _try_move(self, dx: float, dy: float, walls) -> None:
        s = self._eff_size() - 2
        phasing = self._phases_walls()
        self._x += dx
        if not phasing:
            rect = pg.Rect(int(self._x - s / 2), int(self._y - s / 2), s, s)
            for w in walls:
                if rect.colliderect(w.rect):
                    if dx > 0:
                        self._x = w.rect.left - s / 2
                    elif dx < 0:
                        self._x = w.rect.right + s / 2
                    rect = pg.Rect(int(self._x - s / 2), int(self._y - s / 2), s, s)
        # Screen bounds always apply, even in ghost mode.
        if self._x - s / 2 < 0:
            self._x = s / 2
        elif self._x + s / 2 > config.WIDTH:
            self._x = config.WIDTH - s / 2

        self._y += dy
        if not phasing:
            rect = pg.Rect(int(self._x - s / 2), int(self._y - s / 2), s, s)
            for w in walls:
                if rect.colliderect(w.rect):
                    if dy > 0:
                        self._y = w.rect.top - s / 2
                    elif dy < 0:
                        self._y = w.rect.bottom + s / 2
                    rect = pg.Rect(int(self._x - s / 2), int(self._y - s / 2), s, s)
        if self._y - s / 2 < config.HUD_HEIGHT:
            self._y = config.HUD_HEIGHT + s / 2
        elif self._y + s / 2 > config.HEIGHT:
            self._y = config.HEIGHT - s / 2

    def _fire(self, ctx) -> None:
        # Mine drop is a special "weapon" — drop at current position.
        kind = self._active_kind()
        if kind == "mine":
            # Local import to avoid circular issues at module load.
            from .mine import Mine as MineEntity
            ctx.add_mine(MineEntity(self._x, self._y, self))
            for _ in range(8):
                ctx.add_particle(
                    Particle(self._x, self._y, (255, 120, 80),
                             lifetime=200, size=3)
                )
            self._events.publish(GameEvent.SHOT_FIRED, {"player": self, "kind": "mine"})
            return

        pattern = self._active_pattern()
        # Effective firing angle includes any global offset (e.g. Backshot = 180).
        angle_offset = sum(e.shoot_angle_offset() for e in self._effects)
        effective_angle = self._angle + angle_offset
        rad = math.radians(effective_angle)
        bx = self._x + math.cos(rad) * (self._size * 0.6)
        by = self._y - math.sin(rad) * (self._size * 0.6)
        color = self._colors["accent"]

        # Effective bounce count (Pinball adds to it).
        bounces = config.SHOT_MAX_BOUNCES
        for e in self._effects:
            bounces = e.modify_max_bounces(bounces)

        for offset in pattern:
            shot_angle = effective_angle + offset
            if kind == "big":
                ctx.add_shot(Shot(
                    bx, by, shot_angle, self, color,
                    radius=12, speed=4.0, max_bounces=1,
                ))
            else:
                ctx.add_shot(Shot(
                    bx, by, shot_angle, self, color, max_bounces=bounces,
                ))

        for _ in range(4):
            jitter = random.uniform(-8, 8)
            r2 = math.radians(self._angle + jitter)
            ctx.add_particle(
                Particle(
                    bx,
                    by,
                    self._colors["accent"],
                    vx=math.cos(r2) * 2.5,
                    vy=-math.sin(r2) * 2.5,
                    lifetime=180,
                    size=3,
                )
            )
        self._events.publish(GameEvent.SHOT_FIRED, {"player": self, "kind": kind})

    # --- destruction ------------------------------------------------------
    def kill_player(self, ctx) -> None:
        if not self._alive:
            return
        # Shield check — let the player consume a death-blocking effect instead.
        for e in self._effects:
            if getattr(e, "absorbs_hit", False) and e.try_consume_hit():
                # spawn a brief shield burst, then return without dying
                for _ in range(18):
                    ctx.add_particle(
                        Particle(self._x, self._y, getattr(e, "COLOR", (200, 230, 255)),
                                 lifetime=380, size=random.randint(2, 4))
                    )
                ctx.add_shockwave(Shockwave(self._x, self._y,
                                            color=getattr(e, "COLOR", (200, 230, 255)),
                                            max_radius=70, speed=0.22, thickness=2))
                ctx.request_shake(intensity=4, duration_ms=140)
                ctx.audio.play_shield()
                return

        self._alive = False
        # core flash particles
        for _ in range(60):
            ctx.add_particle(
                Particle(self._x, self._y, self._colors["primary"],
                         lifetime=random.randint(600, 1100),
                         size=random.randint(3, 7))
            )
        for _ in range(28):
            ctx.add_particle(
                Particle(self._x, self._y, (255, 230, 150),
                         lifetime=random.randint(350, 650),
                         size=random.randint(2, 5))
            )
        # debris chunks
        for _ in range(10):
            ctx.add_debris(Debris(self._x, self._y, self._colors["secondary"]))
        for _ in range(6):
            ctx.add_debris(Debris(self._x, self._y, (60, 60, 70)))
        # shockwave rings
        ctx.add_shockwave(Shockwave(self._x, self._y, color=(255, 240, 200),
                                    max_radius=170, speed=0.32, thickness=4))
        ctx.add_shockwave(Shockwave(self._x, self._y, color=self._colors["accent"],
                                    max_radius=130, speed=0.24, thickness=3))
        # camera shake + global flash
        ctx.request_shake(intensity=14, duration_ms=420)
        ctx.request_flash(self._colors["primary"], 90)
        self._events.publish(GameEvent.TANK_DESTROYED, {"player": self})

    def respawn(self, x: float, y: float, angle_deg: float) -> None:
        self._x = x
        self._y = y
        self._angle = angle_deg
        self._alive = True
        self._effects = []
        # Match the spawn-time no-fire window so a held shoot key during the
        # round-end pause doesn't immediately fire on the new round.
        self._cooldown = 700.0
        self._fire_flash = 0

    # --- drawing ----------------------------------------------------------
    def _build_image(self) -> pg.Surface:
        """Build the tank surface with its front pointing UP (north)."""
        size = self._size
        margin = 10
        w = size + margin * 2
        h = size + margin * 2 + 6
        s = pg.Surface((w, h), pg.SRCALPHA)
        cx, cy = w // 2, h // 2

        # Side treads (rotate left+right of hull).
        tread_w = 7
        tread_h = size + 4
        for side in (-1, 1):
            tr = pg.Rect(0, 0, tread_w, tread_h)
            tr.center = (cx + side * (size // 2 - 1), cy)
            pg.draw.rect(s, (32, 34, 42), tr, border_radius=3)
            pg.draw.rect(s, (54, 58, 70), tr.inflate(-2, -2), border_radius=2)
            seg = 4
            offset = int(self._tread_offset) % seg
            for i in range(-1, tr.height // seg + 1):
                y = tr.top + (i * seg + offset) % tr.height
                pg.draw.line(s, (22, 24, 30), (tr.left + 1, y), (tr.right - 1, y), 1)

        # Hull.
        hull = pg.Rect(0, 0, size - 4, size - 6)
        hull.center = (cx, cy)
        pg.draw.rect(s, self._colors["secondary"], hull, border_radius=5)
        pg.draw.rect(s, self._colors["primary"], hull.inflate(-6, -6), border_radius=4)
        pg.draw.rect(s, self._colors["accent"], hull.inflate(-14, -14), border_radius=3, width=1)

        # Barrel (extends up from centre).
        barrel = pg.Rect(0, 0, 6, size // 2 + 6)
        barrel.midbottom = (cx, cy + 3)
        pg.draw.rect(s, (28, 30, 38), barrel, border_radius=2)
        pg.draw.rect(s, self._colors["secondary"], barrel.inflate(-2, -2), border_radius=2)
        # tip
        pg.draw.rect(s, (15, 16, 22), pg.Rect(barrel.left - 1, barrel.top - 2, barrel.width + 2, 4),
                     border_radius=2)

        # Turret (round).
        pg.draw.circle(s, (30, 32, 40), (cx, cy), size // 4 + 2)
        pg.draw.circle(s, self._colors["primary"], (cx, cy), size // 4)
        pg.draw.circle(s, self._colors["accent"], (cx, cy), size // 4 - 3)

        return s

    def _draw_effect_indicators(self, surface: pg.Surface) -> None:
        if not self._effects:
            return
        bx = self._x - (len(self._effects) - 1) * 8
        by = self._y + self._size / 2 + 12
        for i, e in enumerate(self._effects):
            cx = int(bx + i * 16)
            cy = int(by)
            pg.draw.circle(surface, (15, 18, 28), (cx, cy), 7)
            pg.draw.circle(surface, e.COLOR, (cx, cy), 5)
            # remaining-time ring
            r = e.remaining_ratio
            if r > 0:
                pts = []
                steps = max(3, int(28 * r))
                for k in range(steps + 1):
                    t = (k / 28) * math.tau - math.pi / 2
                    pts.append((cx + math.cos(t) * 8, cy + math.sin(t) * 8))
                if len(pts) >= 2:
                    pg.draw.lines(surface, (255, 255, 255), False, pts, 1)

    def draw(self, surface: pg.Surface) -> None:
        if not self._alive:
            return

        # shadow
        sh_r = self._size // 2 + 2
        shadow = pg.Surface((sh_r * 2, sh_r * 2), pg.SRCALPHA)
        pg.draw.ellipse(shadow, (0, 0, 0, 80), (0, sh_r // 2, sh_r * 2, sh_r))
        surface.blit(shadow, (self._x - sh_r, self._y - sh_r // 2 + 2))

        img = self._build_image()
        rotated = pg.transform.rotate(img, self._angle - 90)
        # Tiny powerup: scale the rotated sprite down to the effective size.
        eff_size = self._eff_size()
        if eff_size != self._size and self._size > 0:
            scale = eff_size / self._size
            rotated = pg.transform.smoothscale(
                rotated,
                (max(1, int(rotated.get_width() * scale)),
                 max(1, int(rotated.get_height() * scale))),
            )
        # Ghost powerup: lower alpha for transparency.
        alpha = self._eff_alpha()
        if alpha < 255:
            rotated.set_alpha(alpha)
        surface.blit(rotated, rotated.get_rect(center=(int(self._x), int(self._y))).topleft)

        # muzzle flash
        if self._fire_flash > 0:
            rad = math.radians(self._angle)
            fx = self._x + math.cos(rad) * (self._size * 0.6)
            fy = self._y - math.sin(rad) * (self._size * 0.6)
            t = self._fire_flash / 90.0
            radius = int(10 * t)
            if radius > 0:
                fl = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
                pg.draw.circle(fl, (255, 240, 160, int(200 * t)), (radius, radius), radius)
                surface.blit(fl, (fx - radius, fy - radius))

        self._draw_effect_indicators(surface)
