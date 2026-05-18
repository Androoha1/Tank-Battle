"""Top-level coordinator: wires components together and drives the main loop.

Local 2-player hot-seat only.

Public entry point is unchanged: ``GameController().run()``.

Entity classes (Player, Shot, Mine, …) call back into this object as *ctx*
using the methods/properties below (add_shot, walls, request_shake, …).
Those methods simply delegate to the appropriate component so entity code
requires no changes.
"""
import random
import pygame as pg

from .audio import SoundLibrary
from .controllers.layout_controller import LayoutController
from .controllers.player_controller import PlayerController
from .controllers.powerup_controller import PowerupController
from .entities.particle import Particle
from .events import GameEvent, GameEventObservable
from .menu import Menu
from .rendering.renderer import Renderer
from .states.base import GameState
from .states.match_over_state import MatchOverState
from .states.menu_state import MenuState
from .states.paused_state import PausedState
from .states.playing_state import PlayingState
from .states.round_end_state import RoundEndState
from .systems.camera_effects import CameraEffects
from .systems.collision_system import CollisionSystem
from .systems.world import World
from . import config


class GameController:
    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption("Tankons — Tank Battle")
        self._audio = SoundLibrary()
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
        self._winner = None
        self._round_num = 0
        self._map_data: dict | None = None

        self._world = World()
        self._camera = CameraEffects()
        self._collision = CollisionSystem()
        self._renderer = Renderer()

        self._setup_subscriptions()

        _states: dict[str, GameState] = {
            "menu": MenuState(self, self._menu, self._renderer),
            "playing": PlayingState(self, self._renderer),
            "paused": PausedState(self, self._renderer),
            "round_end": RoundEndState(self, self._renderer),
            "match_over": MatchOverState(self, self._renderer),
        }
        self._states = _states
        self._current_state: GameState = _states["menu"]

    # ================================================================= ctx API
    # Entity classes call these methods on the GameController as *ctx*.
    # They delegate to the appropriate component so entity code is untouched.

    @property
    def walls(self) -> list:
        return self._world.walls

    @property
    def players(self) -> list:
        return self._players_ctrl.players

    @property
    def players_ctrl(self) -> PlayerController:
        return self._players_ctrl

    @property
    def audio(self) -> SoundLibrary:
        return self._audio

    def add_shot(self, s) -> None:
        self._world.add_shot(s)

    def add_mine(self, m) -> None:
        self._world.add_mine(m)

    def add_particle(self, p) -> None:
        self._world.add_particle(p)

    def add_debris(self, d) -> None:
        self._world.add_debris(d)

    def add_shockwave(self, w) -> None:
        self._world.add_shockwave(w)

    def random_spawn_point(self) -> tuple[float, float, float] | None:
        """Return a random (x, y, angle) spawn for the current map, or None."""
        if self._map_data is None:
            return None
        return random.choice(self._map_data["spawns"])

    def request_shake(self, intensity: float, duration_ms: float) -> None:
        self._camera.request_shake(intensity, duration_ms)

    def request_flash(self, color: tuple[int, int, int], alpha: int) -> None:
        self._camera.request_flash(color, alpha)

    # ============================================================== properties
    @property
    def winner(self):
        return self._winner

    @property
    def match_winner(self):
        return self._match_winner

    # ========================================================== subscriptions
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

    # ================================================================== flow
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
        self._world.clear()
        self._camera.reset()
        self._map_data = self._layout.select_map()
        self._world.set_walls(self._layout.build_walls(self._map_data))

        spawns = self._layout.get_spawns(self._map_data, 2)
        if not self._players_ctrl.players:
            self._players_ctrl.spawn(spawns)
        else:
            self._players_ctrl.reset_for_new_round(spawns)
        self._powerup_ctrl.set_layout(self._layout, self._map_data)
        self._winner = None

    def return_to_menu(self) -> None:
        self._round_num = 0
        self._match_winner = None
        self._winner = None
        self._players_ctrl = PlayerController(2, self._events)
        self._world.clear()
        self._world.set_walls([])
        self._map_data = None

    # ================================================================= update
    def update_play(self, dt: float, *, ignore_winner_check: bool = False) -> str | None:
        for p in self._players_ctrl.players:
            p.update(dt, self)

        for s in self._world.shots[:]:
            s.update(dt, self)
            if not s.alive():
                self._world.shots.remove(s)

        self._collision.process(self._world, self._players_ctrl.players, self)

        for m in self._world.mines[:]:
            m.update(dt, self)
            if not m.alive():
                self._world.mines.remove(m)

        for d in self._world.debris[:]:
            d.update(dt, self)
            if not d.alive():
                self._world.debris.remove(d)

        for w in self._world.shockwaves[:]:
            w.update(dt, self)
            if not w.alive():
                self._world.shockwaves.remove(w)

        for pt in self._world.particles[:]:
            pt.update(dt, self)
            if not pt.alive():
                self._world.particles.remove(pt)

        self._camera.update(dt)
        self._powerup_ctrl.update(dt, self._players_ctrl.players, self)

        if not ignore_winner_check and self._check_winner():
            return "round_end"
        return None

    def _check_winner(self) -> bool:
        alive = self._players_ctrl.alive_players()
        if len(alive) <= 1 and len(self._players_ctrl.players) >= 2:
            self._winner = alive[0] if alive else None
            if self._winner:
                self._players_ctrl.award_winner(self._winner)
                if self._win_target > 0:
                    score = self._players_ctrl.scores.get(self._winner, 0)
                    if score >= self._win_target:
                        self._match_winner = self._winner
            self._events.publish(GameEvent.ROUND_RESET, {"winner": self._winner})
            return True
        return False

    # ================================================================== draw
    def draw_play(self) -> None:
        self._renderer.draw_play(
            self._screen,
            self._world,
            self._camera,
            self._powerup_ctrl,
            self._players_ctrl,
            self._map_data,
            self._round_num,
        )

    # =============================================================== main loop
    def _switch_state(self, key: str) -> None:
        self._current_state = self._states[key]
        self._current_state.on_enter()

    def run(self) -> None:
        running = True
        while running:
            dt = self._clock.tick(config.FPS)
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False
                    break
                transition = self._current_state.handle_event(ev)
                if transition == "quit":
                    running = False
                    break
                elif transition:
                    self._switch_state(transition)

            if not running:
                break

            transition = self._current_state.update(dt)
            if transition == "quit":
                running = False
            elif transition:
                self._switch_state(transition)

            self._current_state.draw(self._screen)
            pg.display.flip()

        self._audio.stop_ambient()
        pg.quit()
