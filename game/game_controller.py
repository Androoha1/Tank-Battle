"""Top-level coordinator: owns entity collections and drives the main loop."""
import math
import random
import socket
import pygame as pg


def _detect_lan_ip() -> str:
    """Return this machine's LAN-facing IP, or 127.0.0.1 if offline.

    ``gethostbyname(gethostname())`` returns the loopback on macOS when the
    hostname resolves locally. Opening a UDP "connection" to a public address
    (no packets actually sent) lets the OS pick the right interface and we
    can read its address back via ``getsockname``.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()

from .audio import SoundLibrary
from .controllers.layout_controller import LayoutController
from .controllers.player_controller import PlayerController
from .controllers.powerup_controller import PowerupController
from .entities.particle import Particle
from .entities.wall import Wall
from .events import GameEvent, GameEventObservable
from .menu import Menu
from .network.client import GameClient
from .network.server import GameServer
from . import config


class GameController:
    STATE_MENU = "menu"
    STATE_PLAYING = "playing"
    STATE_PAUSED = "paused"
    STATE_ROUND_END = "round_end"
    STATE_MATCH_OVER = "match_over"
    STATE_HOST_LOBBY = "host_lobby"
    STATE_CLIENT_CONNECTING = "client_connecting"
    STATE_CLIENT_PLAYING = "client_playing"
    STATE_NET_ERROR = "net_error"

    def __init__(self, num_players: int = 2) -> None:
        pg.init()
        pg.display.set_caption("Tankons — Tank Battle")
        self._audio = SoundLibrary()
        self._screen = pg.display.set_mode((config.WIDTH, config.HEIGHT))
        self._clock = pg.time.Clock()
        self._events = GameEventObservable()

        self._layout = LayoutController(self._events)
        self._players_ctrl = PlayerController(num_players, self._events)
        self._powerup_ctrl = PowerupController(self._events)
        self._menu = Menu(self._layout)
        self._initial_num_players = num_players
        self._win_target = 0
        self._mode = "local"
        self._match_winner = None
        self._pause_pulse = 0.0

        # Networking.
        self._server: GameServer | None = None
        self._client: GameClient | None = None
        self._net_error: str | None = None
        self._lobby_pulse = 0.0
        self._lobby_port = 5555
        # Client-side rendering proxies.
        self._client_walls: list[Wall] = []
        self._client_state: dict | None = None

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

    # ------------------------------------------------------------------ ctx
    @property
    def walls(self):
        return self._walls

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

    @property
    def players(self) -> list:
        return self._players_ctrl.players

    def request_shake(self, intensity: float, duration_ms: float) -> None:
        # Take the strongest pending shake.
        if intensity > self._shake_intensity or self._shake_timer <= 0:
            self._shake_intensity = intensity
            self._shake_timer = duration_ms
            self._shake_duration = duration_ms

    def request_flash(self, color: tuple[int, int, int], alpha: int) -> None:
        self._flash_color = color
        self._flash_alpha = alpha

    @property
    def audio(self) -> SoundLibrary:
        return self._audio

    # ----------------------------------------------------------------- init
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
        # Vertical gradient.
        top_c = (24, 28, 42)
        bot_c = (14, 16, 24)
        for y in range(config.HEIGHT):
            t = y / config.HEIGHT
            r = int(top_c[0] * (1 - t) + bot_c[0] * t)
            g = int(top_c[1] * (1 - t) + bot_c[1] * t)
            b = int(top_c[2] * (1 - t) + bot_c[2] * t)
            pg.draw.line(s, (r, g, b), (0, y), (config.WIDTH, y))
        # Grid.
        for x in range(0, config.WIDTH, 48):
            pg.draw.line(s, config.GRID, (x, config.HUD_HEIGHT), (x, config.HEIGHT), 1)
        for y in range(config.HUD_HEIGHT, config.HEIGHT, 48):
            pg.draw.line(s, config.GRID, (0, y), (config.WIDTH, y), 1)
        # Vignette corners.
        for corner in ((0, config.HUD_HEIGHT), (config.WIDTH, config.HUD_HEIGHT),
                       (0, config.HEIGHT), (config.WIDTH, config.HEIGHT)):
            radius = 300
            shade = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
            pg.draw.circle(shade, (0, 0, 0, 90), (radius, radius), radius)
            s.blit(shade, (corner[0] - radius, corner[1] - radius),
                   special_flags=pg.BLEND_PREMULTIPLIED)
        return s

    # ----------------------------------------------------------------- flow
    def begin_match(self, mode: str, num_players: int, win_target: int) -> None:
        """Called from the menu when the user picks START. Resets scores."""
        self._mode = mode
        self._win_target = win_target
        self._match_winner = None
        # Build a fresh PlayerController with the requested player count.
        self._players_ctrl = PlayerController(num_players, self._events)
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

        spawn_count = max(2, self._players_ctrl.num_players)
        spawns = self._layout.get_spawns(self._map_data, spawn_count)
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
                # Match-over check.
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
                                self._start_from_menu(action)
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
                    elif self._state == self.STATE_HOST_LOBBY:
                        if ev.key == pg.K_ESCAPE:
                            self._return_to_menu()
                        elif ev.key in (pg.K_RETURN, pg.K_SPACE):
                            if self._server and self._server.connected_count >= 1:
                                self._begin_host_match()
                    elif self._state == self.STATE_CLIENT_CONNECTING:
                        if ev.key == pg.K_ESCAPE:
                            self._return_to_menu()
                    elif self._state == self.STATE_CLIENT_PLAYING:
                        if ev.key == pg.K_ESCAPE:
                            self._return_to_menu()
                    elif self._state == self.STATE_NET_ERROR:
                        if ev.key in (pg.K_RETURN, pg.K_ESCAPE, pg.K_SPACE):
                            self._return_to_menu()
                else:
                    # Forward IP-input text events to menu too.
                    if self._state == self.STATE_MENU:
                        self._menu.handle_event(ev)

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
            elif self._state == self.STATE_HOST_LOBBY:
                self._lobby_pulse += dt * 0.005
                self._draw_host_lobby()
            elif self._state == self.STATE_CLIENT_CONNECTING:
                self._lobby_pulse += dt * 0.005
                self._tick_client_connect()
                self._draw_client_connecting()
            elif self._state == self.STATE_CLIENT_PLAYING:
                self._tick_client_play(dt)
                self._draw_client_view()
            elif self._state == self.STATE_NET_ERROR:
                self._draw_net_error()

            pg.display.flip()

        self._audio.stop_ambient()
        pg.quit()

    def _start_from_menu(self, payload: dict) -> None:
        mode = payload["mode"]
        port = payload.get("port", 5555)
        if mode == "host_lan":
            self._mode = "host"
            self._lobby_port = port
            self._server = GameServer(port=port, max_clients=3)
            if not self._server.start():
                self._net_error = f"Could not start server: {self._server.error}"
                self._state = self.STATE_NET_ERROR
                return
            self._win_target = payload["win_target"]
            self._state = self.STATE_HOST_LOBBY
            return
        if mode == "join_lan":
            self._mode = "client"
            self._client = GameClient(payload["ip"], port)
            self._client.connect_async()
            self._state = self.STATE_CLIENT_CONNECTING
            self._lobby_pulse = 0.0
            return
        # default local
        self.begin_match(
            mode="local",
            num_players=payload["players"],
            win_target=payload["win_target"],
        )

    def _begin_host_match(self) -> None:
        """Once at least one client has joined, host starts the round."""
        assert self._server is not None
        connected = self._server.connected_slots()
        num_players = 1 + len(connected)
        self.begin_match(mode="host", num_players=num_players, win_target=self._win_target)
        # Slot 0 is host (keyboard). Slots 1+ are networked.
        for idx, p in enumerate(self._players_ctrl.players):
            if idx == 0:
                continue
            p.set_remote_input({})  # start with empty input dict

    def _return_to_menu(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None
        if self._client is not None:
            self._client.disconnect()
            self._client = None
        self._mode = "local"
        self._net_error = None
        self._client_state = None
        self._client_walls = []
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

    # -------------------------------------------------------------- updates
    def _update_play(self, dt: float, *, ignore_winner_check: bool = False) -> None:
        # In host mode, pull latest input from each client and route into the
        # matching Player. Slot 0 is the host (local keyboard); slots 1..N are
        # network-driven.
        if self._mode == "host" and self._server is not None:
            for idx, p in enumerate(self._players_ctrl.players):
                if idx == 0:
                    continue
                p.set_remote_input(self._server.get_input(idx))

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
                if player is s.owner and not s.can_hit_owner:
                    continue
                if s.rect.colliderect(player.rect):
                    player.kill_player(self)
                    s.kill()
                    break
            if not s.alive() and s in self._shots:
                self._shots.remove(s)

        for pt in self._particles[:]:
            pt.update(dt, self)
            if not pt.alive():
                self._particles.remove(pt)

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

        # Decay camera shake + flash.
        if self._shake_timer > 0:
            self._shake_timer = max(0, self._shake_timer - dt)
        if self._flash_alpha > 0:
            self._flash_alpha = max(0, int(self._flash_alpha - dt * 0.35))

        self._powerup_ctrl.update(dt, self._players_ctrl.players, self)

        if not ignore_winner_check:
            self._check_winner()

        # In host mode, broadcast a state snapshot for clients to render.
        if self._mode == "host" and self._server is not None:
            self._server.broadcast(self._build_state_snapshot())

    # ---------------------------------------------------------------- draws
    def _draw_play(self) -> None:
        # Render the world (everything that shakes) onto an offscreen surface.
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

        # Camera-shake offset, decays with remaining time.
        shake_x = shake_y = 0
        if self._shake_timer > 0 and self._shake_duration > 0:
            t = self._shake_timer / self._shake_duration
            amp = self._shake_intensity * t
            shake_x = int(random.uniform(-amp, amp))
            shake_y = int(random.uniform(-amp, amp))
        self._screen.fill((0, 0, 0))
        self._screen.blit(world, (shake_x, shake_y))

        # Global flash overlay.
        if self._flash_alpha > 0 and self._flash_color is not None:
            overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
            overlay.fill((*self._flash_color, self._flash_alpha))
            self._screen.blit(overlay, (0, 0))

        # HUD doesn't shake.
        self._players_ctrl.draw_hud(self._screen)

        if self._map_data:
            info = self._tiny_font.render(
                f"{self._map_data['name']}  ·  Round {self._round_num}",
                True,
                (150, 165, 190),
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

    # =================================================================
    #                          NETWORKING
    # =================================================================
    def _build_state_snapshot(self) -> dict:
        """Compact state snapshot for clients to render."""
        ps = []
        for slot, p in enumerate(self._players_ctrl.players):
            ps.append({
                "i": slot,
                "n": p.name,
                "x": round(p.x, 1),
                "y": round(p.y, 1),
                "a": round(p.angle, 1),
                "al": p.alive(),
                "c": list(p.colors["primary"]),
                "ac": list(p.colors["accent"]),
                "sc": list(p.colors["secondary"]),
                "ef": [
                    {"c": list(e.COLOR), "r": round(e.remaining_ratio, 3)}
                    for e in p.effects
                ],
            })
        shots = [
            {"x": round(s.x, 1), "y": round(s.y, 1),
             "c": list(getattr(s, "_color", (255, 255, 255))),
             "r": int(getattr(s, "_radius", 5))}
            for s in self._shots
        ]
        mines = [{"x": round(m.x, 1), "y": round(m.y, 1)} for m in self._mines]
        pups = [
            {"x": round(pu.x, 1), "y": round(pu.y, 1), "c": list(pu.COLOR), "k": pu.ICON}
            for pu in self._powerup_ctrl.powerups
        ]
        sws = [
            {"x": round(w.x, 1), "y": round(w.y, 1),
             "r": int(getattr(w, "_radius", 10)),
             "m": int(getattr(w, "_max", 100)),
             "c": list(getattr(w, "_color", (255, 255, 255)))}
            for w in self._shockwaves
        ]
        return {
            "t": "STATE",
            "st": self._state,
            "rd": self._round_num,
            "mn": (self._map_data or {}).get("name", ""),
            "wl": [list(map(int, w)) for w in (self._map_data or {}).get("walls", [])],
            "sc": {p.name: self._players_ctrl.scores.get(p, 0) for p in self._players_ctrl.players},
            "ps": ps,
            "sh": shots,
            "mi": mines,
            "pu": pups,
            "sw": sws,
            "wn": self._winner.name if self._winner else None,
            "mw": self._match_winner.name if self._match_winner else None,
        }

    def _tick_client_connect(self) -> None:
        assert self._client is not None
        if self._client.connected:
            self._state = self.STATE_CLIENT_PLAYING
            return
        if self._client.error is not None:
            self._net_error = f"Connect failed: {self._client.error}"
            self._state = self.STATE_NET_ERROR

    def _tick_client_play(self, dt: float) -> None:
        assert self._client is not None
        if not self._client.connected:
            self._net_error = "Lost connection to server."
            self._state = self.STATE_NET_ERROR
            return

        # Send input for the client's slot using the slot's keymap if available,
        # otherwise default to player-1 keymap.
        slot = self._client.slot
        try:
            keymap = PlayerController.DEFAULT_CONTROLS[max(0, slot)]
        except IndexError:
            keymap = PlayerController.DEFAULT_CONTROLS[0]
        keys = pg.key.get_pressed()
        self._client.send_input({
            "left": bool(keys[keymap["left"]]),
            "right": bool(keys[keymap["right"]]),
            "up": bool(keys[keymap["up"]]),
            "down": bool(keys[keymap["down"]]),
            "shoot": bool(keys[keymap["shoot"]]),
        })

        latest = self._client.latest_state()
        if latest is None:
            return
        # Rebuild proxy walls if changed.
        if latest.get("wl") != [
            [int(c) for c in w] for w in (self._client_state or {}).get("wl", [])
        ]:
            self._client_walls = [Wall(x, y, w, h) for (x, y, w, h) in latest.get("wl", [])]
        self._client_state = latest

    def _draw_host_lobby(self) -> None:
        self._screen.blit(self._bg, (0, 0))
        title = self._title_font.render("HOSTING", True, (235, 240, 250))
        self._screen.blit(title, title.get_rect(center=(config.WIDTH // 2, 180)))

        host_ip = _detect_lan_ip()
        info1 = self._sub_font.render(f"Share this address with players:", True, (180, 195, 220))
        info2 = self._title_font.render(f"{host_ip}", True, (140, 220, 255))
        info3 = self._sub_font.render(f"Port: {self._lobby_port}", True, (180, 195, 220))
        self._screen.blit(info1, info1.get_rect(center=(config.WIDTH // 2, 270)))
        self._screen.blit(info2, info2.get_rect(center=(config.WIDTH // 2, 360)))
        self._screen.blit(info3, info3.get_rect(center=(config.WIDTH // 2, 440)))

        count = self._server.connected_count if self._server else 0
        col = (120, 220, 140) if count >= 1 else (220, 160, 80)
        status = self._sub_font.render(
            f"Players connected: {count}", True, col,
        )
        self._screen.blit(status, status.get_rect(center=(config.WIDTH // 2, 510)))

        pulse = (math.sin(self._lobby_pulse * 5) + 1) / 2
        cta_color = (120 + int(80 * pulse), 220, 255)
        ready = "Press ENTER to start" if count >= 1 else "Waiting for at least one client..."
        cta = self._sub_font.render(ready, True, cta_color)
        self._screen.blit(cta, cta.get_rect(center=(config.WIDTH // 2, 600)))

        esc = self._tiny_font.render("ESC to cancel", True, (160, 170, 195))
        self._screen.blit(esc, esc.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 40)))

    def _draw_client_connecting(self) -> None:
        self._screen.blit(self._bg, (0, 0))
        title = self._title_font.render("CONNECTING", True, (235, 240, 250))
        self._screen.blit(title, title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 40)))
        pulse = (math.sin(self._lobby_pulse * 6) + 1) / 2
        dots = "." * (1 + int(pulse * 3))
        sub = self._sub_font.render(f"reaching server{dots}", True, (160, 200, 240))
        self._screen.blit(sub, sub.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 30)))
        esc = self._tiny_font.render("ESC to cancel", True, (160, 170, 195))
        self._screen.blit(esc, esc.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 40)))

    def _draw_net_error(self) -> None:
        self._screen.blit(self._bg, (0, 0))
        title = self._sub_font.render("NETWORK ERROR", True, (255, 120, 120))
        self._screen.blit(title, title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 30)))
        msg = self._tiny_font.render(self._net_error or "unknown error", True, (235, 235, 240))
        self._screen.blit(msg, msg.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 10)))
        hint = self._tiny_font.render("Press ENTER to return to menu", True, (180, 190, 210))
        self._screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 50)))

    def _draw_client_view(self) -> None:
        state = self._client_state
        self._world.blit(self._bg, (0, 0))
        if state is None:
            self._screen.blit(self._world, (0, 0))
            t = self._sub_font.render("Waiting for server state...", True, (180, 195, 220))
            self._screen.blit(t, t.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2)))
            return

        # Walls.
        for w in self._client_walls:
            w.draw(self._world)
        # Powerups (simple proxy render — circle + halo).
        for pu in state.get("pu", []):
            self._draw_proxy_powerup(self._world, pu)
        # Mines.
        for m in state.get("mi", []):
            self._draw_proxy_mine(self._world, m)
        # Players.
        for p in state.get("ps", []):
            self._draw_proxy_player(self._world, p)
        # Shots.
        for s in state.get("sh", []):
            self._draw_proxy_shot(self._world, s)
        # Shockwaves.
        for sw in state.get("sw", []):
            self._draw_proxy_shockwave(self._world, sw)

        self._screen.fill((0, 0, 0))
        self._screen.blit(self._world, (0, 0))

        # HUD (rebuild scoreboard from snapshot).
        self._draw_client_hud(state)

        # Round info.
        if state.get("mn"):
            info = self._tiny_font.render(
                f"{state['mn']}  ·  Round {state.get('rd', 0)}  ·  CLIENT",
                True, (160, 200, 240),
            )
            self._screen.blit(info, (config.WIDTH - info.get_width() - 20, config.HUD_HEIGHT + 10))

        # Round-end / match-over overlay using server state.
        st = state.get("st")
        if st == self.STATE_ROUND_END and state.get("wn"):
            self._draw_text_overlay(f"{state['wn']} WINS THE ROUND", (255, 220, 150))
        elif st == self.STATE_MATCH_OVER and state.get("mw"):
            self._draw_text_overlay(f"{state['mw']} WINS THE MATCH", (255, 220, 150))

    def _draw_text_overlay(self, text: str, color) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        self._screen.blit(overlay, (0, 0))
        surf = self._sub_font.render(text, True, color)
        self._screen.blit(surf, surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2)))

    @staticmethod
    def _draw_proxy_shot(surface, s) -> None:
        cx, cy = int(s["x"]), int(s["y"])
        r = int(s.get("r", 5))
        c = tuple(s.get("c", (255, 255, 255)))
        glow_r = r * 3
        glow = pg.Surface((glow_r * 2, glow_r * 2), pg.SRCALPHA)
        pg.draw.circle(glow, (*c, 90), (glow_r, glow_r), glow_r)
        pg.draw.circle(glow, (*c, 160), (glow_r, glow_r), r * 2)
        surface.blit(glow, (cx - glow_r, cy - glow_r))
        pg.draw.circle(surface, (255, 255, 255), (cx, cy), r)
        pg.draw.circle(surface, c, (cx, cy), max(1, r - 1))

    @staticmethod
    def _draw_proxy_powerup(surface, pu) -> None:
        cx, cy = int(pu["x"]), int(pu["y"])
        c = tuple(pu.get("c", (220, 220, 220)))
        glow = pg.Surface((90, 90), pg.SRCALPHA)
        pg.draw.circle(glow, (*c, 40), (45, 45), 45)
        pg.draw.circle(glow, (*c, 90), (45, 45), 30)
        surface.blit(glow, (cx - 45, cy - 45))
        pg.draw.circle(surface, (250, 250, 250), (cx, cy), 14)
        pg.draw.circle(surface, c, (cx, cy), 11)

    @staticmethod
    def _draw_proxy_mine(surface, m) -> None:
        cx, cy = int(m["x"]), int(m["y"])
        pg.draw.circle(surface, (40, 42, 50), (cx, cy), 12)
        pg.draw.circle(surface, (75, 78, 88), (cx, cy), 10)
        pg.draw.circle(surface, (220, 80, 80), (cx, cy), 4)

    @staticmethod
    def _draw_proxy_player(surface, p) -> None:
        # Use the same drawing approach as Player but with state-only inputs.
        from .entities.player import Player as _P
        colors = {
            "primary": tuple(p["c"]),
            "secondary": tuple(p["sc"]),
            "accent": tuple(p["ac"]),
            "name": p["n"],
        }
        # Build a transient Player object purely for drawing.
        proxy = _P.__new__(_P)
        # Initialise minimal required state.
        proxy._x = float(p["x"])
        proxy._y = float(p["y"])
        proxy._angle = float(p["a"])
        proxy._alive = bool(p["al"])
        proxy._colors = colors
        proxy._size = config.TANK_SIZE
        proxy._effects = [
            type("E", (), {"COLOR": tuple(e["c"]), "remaining_ratio": e["r"]})()
            for e in p.get("ef", [])
        ]
        proxy._tread_offset = 0.0
        proxy._fire_flash = 0
        proxy.draw(surface)

    def _draw_client_hud(self, state: dict) -> None:
        pg.draw.rect(self._screen, config.HUD_BG, (0, 0, config.WIDTH, config.HUD_HEIGHT))
        pg.draw.line(self._screen, config.HUD_LINE, (0, config.HUD_HEIGHT - 1),
                     (config.WIDTH, config.HUD_HEIGHT - 1), 1)
        title = self._mid_font.render("TANKONS", True, (235, 235, 240))
        self._screen.blit(title, (22, (config.HUD_HEIGHT - title.get_height()) // 2))
        sub = self._tiny_font.render("LAN CLIENT", True, (110, 160, 220))
        self._screen.blit(sub, (22 + title.get_width() + 8, (config.HUD_HEIGHT - sub.get_height()) // 2 + 4))

        players = state.get("ps", [])
        scores = state.get("sc", {})
        slot_w = 200
        total = slot_w * len(players)
        start_x = (config.WIDTH - total) // 2
        for i, p in enumerate(players):
            x = start_x + i * slot_w
            pg.draw.rect(self._screen, tuple(p["c"]), (x, 10, 28, 28), border_radius=5)
            pg.draw.rect(self._screen, tuple(p["ac"]), (x, 10, 28, 28), border_radius=5, width=2)
            name = self._mid_font.render(p["n"], True, tuple(p["ac"]))
            self._screen.blit(name, (x + 38, 6))
            score = self._mid_font.render(str(scores.get(p["n"], 0)), True, (235, 235, 240))
            self._screen.blit(score, (x + 38, 26))
            col = (130, 220, 120) if p["al"] else (220, 80, 80)
            pg.draw.circle(self._screen, col, (x + 150, 22), 5)

    @staticmethod
    def _draw_proxy_shockwave(surface, sw) -> None:
        cx, cy = int(sw["x"]), int(sw["y"])
        radius = sw.get("r", 10)
        maxr = max(1, sw.get("m", 100))
        t = 1.0 - (radius / maxr)
        if t <= 0:
            return
        c = tuple(sw.get("c", (255, 255, 255)))
        alpha = int(220 * t * t)
        s = pg.Surface((radius * 2 + 4, radius * 2 + 4), pg.SRCALPHA)
        pg.draw.circle(s, (*c, alpha), (radius + 2, radius + 2), int(radius), max(1, int(3 * t)))
        surface.blit(s, (cx - radius - 2, cy - radius - 2))

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

        # Final scoreboard.
        y = rect.bottom + 30
        for p in self._players_ctrl.players:
            s = self._sub_font.render(
                f"{p.name}: {self._players_ctrl.scores.get(p, 0)}", True, p.colors["accent"]
            )
            self._screen.blit(s, s.get_rect(center=(config.WIDTH // 2, y)))
            y += 36

        hint = self._tiny_font.render("Press ENTER or ESC to return to menu", True, (180, 190, 210))
        self._screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 60)))

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
        # back-panel
        panel = pg.Surface((rect.width + 60, rect.height + 30), pg.SRCALPHA)
        pg.draw.rect(panel, (15, 18, 28, 220), panel.get_rect(), border_radius=10)
        pg.draw.rect(panel, (*color, 180), panel.get_rect(), border_radius=10, width=2)
        self._screen.blit(panel, panel.get_rect(center=rect.center).topleft)
        self._screen.blit(surf, rect)
