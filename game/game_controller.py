"""Top-level coordinator: owns entity collections and drives the main loop.

Local 2-player hot-seat only.
"""
import math
import random
import pygame as pg

from .audio import SoundLibrary
from .controllers.layout_controller import LayoutController
from .controllers.player_controller import PlayerController
from .controllers.powerup_controller import PowerupController
from .entities.particle import Particle
from .events import GameEvent, GameEventObservable
from .menu import Menu
from . import config


class GameController:
    STATE_MENU = "menu"
    STATE_PLAYING = "playing"
    STATE_PAUSED = "paused"
    STATE_ROUND_END = "round_end"
    STATE_MATCH_OVER = "match_over"

    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption("Tankons — Tank Battle")
        self._audio = SoundLibrary()
        # Fullscreen with SDL's SCALED renderer — keeps the logical 1280x720
        # internal resolution and stretches to the display, with smooth filtering.
        self._screen = pg.display.set_mode(
            (config.WIDTH, config.HEIGHT),
            pg.FULLSCREEN | pg.SCALED,
        )
        pg.mouse.set_visible(False)
        self._clock = pg.time.Clock()
        self._events = GameEventObservable()

        self._layout = LayoutController(self._events)
        self._players_ctrl = PlayerController(2, self._events)
        self._powerup_ctrl = PowerupController(self._events)
        self._menu = Menu(self._layout)

        self._win_target = 0
        self._match_winner = None
        self._pause_pulse = 0.0

        self._shots: list = []
        self._mines: list = []
        self._particles: list = []
        self._debris: list = []
        self._shockwaves: list = []
        self._walls: list = []
        self._map_data: dict | None = None
        self._state = self.STATE_MENU
        self._round_end_timer = 0.0
        self._winner = None
        self._round_num = 0

        # Camera shake + screen flash.
        self._shake_intensity = 0.0
        self._shake_timer = 0.0
        self._shake_duration = 0.0
        self._flash_color: tuple[int, int, int] | None = None
        self._flash_alpha = 0
        self._world = pg.Surface((config.WIDTH, config.HEIGHT))

        self._title_font = pg.font.SysFont("arialblack", 110, bold=True)
        self._sub_font = pg.font.SysFont("arialblack", 30, bold=True)
        self._mid_font = pg.font.SysFont("arialblack", 24, bold=True)
        self._tiny_font = pg.font.SysFont("arial", 18, bold=True)

        self._bg = self._build_background()
        self._setup_subscriptions()

    # =============================================================== ctx
    @property
    def walls(self):
        return self._walls

    @property
    def players(self) -> list:
        return self._players_ctrl.players

    @property
    def audio(self) -> SoundLibrary:
        return self._audio

    def add_shot(self, s) -> None:
        self._shots.append(s)

    def add_mine(self, m) -> None:
        self._mines.append(m)

    def add_particle(self, p) -> None:
        self._particles.append(p)

    def add_debris(self, d) -> None:
        self._debris.append(d)

    def add_shockwave(self, w) -> None:
        self._shockwaves.append(w)

    def random_spawn_point(self) -> tuple[float, float, float] | None:
        """Return a random (x, y, angle) spawn for the current map, or None."""
        if self._map_data is None:
            return None
        return random.choice(self._map_data["spawns"])

    def request_shake(self, intensity: float, duration_ms: float) -> None:
        if intensity > self._shake_intensity or self._shake_timer <= 0:
            self._shake_intensity = intensity
            self._shake_timer = duration_ms
            self._shake_duration = duration_ms

    def request_flash(self, color: tuple[int, int, int], alpha: int) -> None:
        self._flash_color = color
        self._flash_alpha = alpha

    # ============================================================== init
    def _setup_subscriptions(self) -> None:
        self._events.subscribe(GameEvent.SHOT_FIRED, self._on_shot_fired)
        self._events.subscribe(GameEvent.TANK_DESTROYED, self._on_tank_destroyed)
        self._events.subscribe(GameEvent.POWERUP_PICKED, self._on_powerup_picked)

    def _on_shot_fired(self, payload) -> None:
        kind = payload.get("kind") if payload else None
        self._audio.play_shoot(kind)

    def _on_tank_destroyed(self, payload) -> None:
        self._audio.play_explosion()

    def _on_powerup_picked(self, payload) -> None:
        player = payload["player"]
        for _ in range(14):
            self.add_particle(
                Particle(player.x, player.y, player.colors["accent"], lifetime=320, size=3)
            )
        self._audio.play_pickup()

    def _build_background(self) -> pg.Surface:
        s = pg.Surface((config.WIDTH, config.HEIGHT))
        top_c = (24, 28, 42)
        bot_c = (14, 16, 24)
        for y in range(config.HEIGHT):
            t = y / config.HEIGHT
            r = int(top_c[0] * (1 - t) + bot_c[0] * t)
            g = int(top_c[1] * (1 - t) + bot_c[1] * t)
            b = int(top_c[2] * (1 - t) + bot_c[2] * t)
            pg.draw.line(s, (r, g, b), (0, y), (config.WIDTH, y))
        for x in range(0, config.WIDTH, 48):
            pg.draw.line(s, config.GRID, (x, config.HUD_HEIGHT), (x, config.HEIGHT), 1)
        for y in range(config.HUD_HEIGHT, config.HEIGHT, 48):
            pg.draw.line(s, config.GRID, (0, y), (config.WIDTH, y), 1)
        for corner in ((0, config.HUD_HEIGHT), (config.WIDTH, config.HUD_HEIGHT),
                       (0, config.HEIGHT), (config.WIDTH, config.HEIGHT)):
            radius = 300
            shade = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
            pg.draw.circle(shade, (0, 0, 0, 90), (radius, radius), radius)
            s.blit(shade, (corner[0] - radius, corner[1] - radius),
                   special_flags=pg.BLEND_PREMULTIPLIED)
        return s

    # ============================================================== flow
    def begin_match(self, win_target: int) -> None:
        self._win_target = win_target
        self._match_winner = None
        self._players_ctrl = PlayerController(2, self._events)
        self._round_num = 0
        self.start_round()

    def start_round(self) -> None:
        if self._round_num == 0:
            self._audio.start_ambient()
        self._round_num += 1
        self._shots = []
        self._mines = []
        self._particles = []
        self._debris = []
        self._shockwaves = []
        self._shake_intensity = 0
        self._shake_timer = 0
        self._flash_alpha = 0
        self._map_data = self._layout.select_map()
        self._walls = self._layout.build_walls(self._map_data)

        spawns = self._layout.get_spawns(self._map_data, 2)
        if not self._players_ctrl.players:
            self._players_ctrl.spawn(spawns)
        else:
            self._players_ctrl.reset_for_new_round(spawns)
        self._powerup_ctrl.set_layout(self._layout, self._map_data)
        self._winner = None
        self._state = self.STATE_PLAYING

    def _check_winner(self) -> None:
        alive = self._players_ctrl.alive_players()
        if len(alive) <= 1 and len(self._players_ctrl.players) >= 2:
            self._state = self.STATE_ROUND_END
            self._round_end_timer = config.ROUND_END_DELAY_MS
            self._winner = alive[0] if alive else None
            if self._winner:
                self._players_ctrl.award_winner(self._winner)
                if self._win_target > 0:
                    score = self._players_ctrl.scores.get(self._winner, 0)
                    if score >= self._win_target:
                        self._match_winner = self._winner
            self._events.publish(GameEvent.ROUND_RESET, {"winner": self._winner})

    def run(self) -> None:
        running = True
        while running:
            dt = self._clock.tick(config.FPS)
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False
                elif ev.type == pg.KEYDOWN:
                    if self._state == self.STATE_MENU:
                        action = self._menu.handle_event(ev)
                        if action:
                            if action["action"] == "quit":
                                running = False
                            elif action["action"] == "start":
                                self.begin_match(action["win_target"])
                    elif self._state == self.STATE_PLAYING:
                        if ev.key in (pg.K_p, pg.K_PAUSE):
                            self._state = self.STATE_PAUSED
                        elif ev.key == pg.K_ESCAPE:
                            self._return_to_menu()
                    elif self._state == self.STATE_PAUSED:
                        if ev.key in (pg.K_p, pg.K_PAUSE, pg.K_ESCAPE, pg.K_RETURN):
                            self._state = self.STATE_PLAYING
                        elif ev.key == pg.K_q:
                            self._return_to_menu()
                    elif self._state == self.STATE_MATCH_OVER:
                        if ev.key in (pg.K_RETURN, pg.K_SPACE, pg.K_ESCAPE):
                            self._return_to_menu()
                    elif self._state == self.STATE_ROUND_END:
                        if ev.key == pg.K_ESCAPE:
                            self._return_to_menu()

            if self._state == self.STATE_MENU:
                self._menu.update(dt)
                self._menu.draw(self._screen, self._bg)
            elif self._state == self.STATE_PLAYING:
                self._update_play(dt)
                self._draw_play()
            elif self._state == self.STATE_PAUSED:
                self._draw_play()
                self._pause_pulse += dt * 0.004
                self._draw_pause()
            elif self._state == self.STATE_ROUND_END:
                self._update_play(dt, ignore_winner_check=True)
                self._round_end_timer -= dt
                self._draw_play()
                self._draw_round_end()
                if self._round_end_timer <= 0:
                    if self._match_winner is not None:
                        self._state = self.STATE_MATCH_OVER
                    else:
                        self.start_round()
            elif self._state == self.STATE_MATCH_OVER:
                self._draw_play()
                self._draw_match_over()

            pg.display.flip()

        self._audio.stop_ambient()
        pg.quit()

    def _return_to_menu(self) -> None:
        self._state = self.STATE_MENU
        self._round_num = 0
        self._match_winner = None
        self._winner = None
        self._players_ctrl = PlayerController(2, self._events)
        self._shots = []
        self._mines = []
        self._particles = []
        self._debris = []
        self._shockwaves = []
        self._walls = []
        self._map_data = None

    # =========================================================== updates
    def _update_play(self, dt: float, *, ignore_winner_check: bool = False) -> None:
        for p in self._players_ctrl.players:
            p.update(dt, self)

        for s in self._shots[:]:
            s.update(dt, self)
            if not s.alive():
                self._shots.remove(s)
                continue
            for player in self._players_ctrl.players:
                if not player.alive():
                    continue
                # No friendly fire — your own bullets never hit you, even after bouncing.
                if player is s.owner:
                    continue
                if s.rect.colliderect(player.rect):
                    player.kill_player(self)
                    s.kill()
                    break
            if not s.alive() and s in self._shots:
                self._shots.remove(s)

        for m in self._mines[:]:
            m.update(dt, self)
            if not m.alive():
                self._mines.remove(m)

        for d in self._debris[:]:
            d.update(dt, self)
            if not d.alive():
                self._debris.remove(d)

        for w in self._shockwaves[:]:
            w.update(dt, self)
            if not w.alive():
                self._shockwaves.remove(w)

        for pt in self._particles[:]:
            pt.update(dt, self)
            if not pt.alive():
                self._particles.remove(pt)

        if self._shake_timer > 0:
            self._shake_timer = max(0, self._shake_timer - dt)
        if self._flash_alpha > 0:
            self._flash_alpha = max(0, int(self._flash_alpha - dt * 0.35))

        self._powerup_ctrl.update(dt, self._players_ctrl.players, self)

        if not ignore_winner_check:
            self._check_winner()

    # =========================================================== drawing
    def _draw_play(self) -> None:
        world = self._world
        world.blit(self._bg, (0, 0))

        for w in self._walls:
            w.draw(world)
        self._powerup_ctrl.draw(world)
        for m in self._mines:
            m.draw(world)
        for pt in self._particles:
            pt.draw(world)
        for d in self._debris:
            d.draw(world)
        for p in self._players_ctrl.players:
            p.draw(world)
        for s in self._shots:
            s.draw(world)
        for sw in self._shockwaves:
            sw.draw(world)

        shake_x = shake_y = 0
        if self._shake_timer > 0 and self._shake_duration > 0:
            t = self._shake_timer / self._shake_duration
            amp = self._shake_intensity * t
            shake_x = int(random.uniform(-amp, amp))
            shake_y = int(random.uniform(-amp, amp))
        self._screen.fill((0, 0, 0))
        self._screen.blit(world, (shake_x, shake_y))

        if self._flash_alpha > 0 and self._flash_color is not None:
            overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
            overlay.fill((*self._flash_color, self._flash_alpha))
            self._screen.blit(overlay, (0, 0))

        self._players_ctrl.draw_hud(self._screen)

        if self._map_data:
            info = self._tiny_font.render(
                f"{self._map_data['name']}  ·  Round {self._round_num}",
                True, (150, 165, 190),
            )
            pad = 10
            box = pg.Rect(
                config.WIDTH - info.get_width() - pad * 2 - 16,
                config.HUD_HEIGHT + 8,
                info.get_width() + pad * 2,
                info.get_height() + pad,
            )
            bg = pg.Surface((box.width, box.height), pg.SRCALPHA)
            pg.draw.rect(bg, (20, 24, 36, 200), bg.get_rect(), border_radius=6)
            self._screen.blit(bg, box.topleft)
            self._screen.blit(info, (box.left + pad, box.top + pad // 2))

    def _draw_pause(self) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self._screen.blit(overlay, (0, 0))

        pulse = (math.sin(self._pause_pulse * 4) + 1) / 2
        title = self._title_font.render("PAUSED", True, (235, 240, 250))
        self._screen.blit(title, title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 60)))

        col = (int(140 + 80 * pulse), 210, 255)
        hint = self._sub_font.render("P / ESC : resume    ·    Q : quit to menu", True, col)
        self._screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 40)))

    def _draw_round_end(self) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        self._screen.blit(overlay, (0, 0))
        if self._winner:
            text = f"{self._winner.name} WINS THE ROUND"
            color = self._winner.colors["accent"]
        else:
            text = "DRAW"
            color = (220, 220, 230)
        surf = self._sub_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
        panel = pg.Surface((rect.width + 60, rect.height + 30), pg.SRCALPHA)
        pg.draw.rect(panel, (15, 18, 28, 220), panel.get_rect(), border_radius=10)
        pg.draw.rect(panel, (*color, 180), panel.get_rect(), border_radius=10, width=2)
        self._screen.blit(panel, panel.get_rect(center=rect.center).topleft)
        self._screen.blit(surf, rect)

    def _draw_match_over(self) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self._screen.blit(overlay, (0, 0))

        winner = self._match_winner
        if winner:
            text = f"{winner.name} WINS THE MATCH"
            color = winner.colors["accent"]
        else:
            text = "MATCH OVER"
            color = (220, 220, 230)
        surf = self._title_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 30))
        self._screen.blit(surf, rect)

        y = rect.bottom + 30
        for p in self._players_ctrl.players:
            s = self._sub_font.render(
                f"{p.name}: {self._players_ctrl.scores.get(p, 0)}", True, p.colors["accent"]
            )
            self._screen.blit(s, s.get_rect(center=(config.WIDTH // 2, y)))
            y += 36

        hint = self._tiny_font.render("Press ENTER or ESC to return to menu", True, (180, 190, 210))
        self._screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 60)))
