"""Spawns power-ups on the active map and routes pickups."""
import random
import pygame as pg

from ..events import GameEvent
from ..powerups.arrow_shot import ArrowShot
from ..powerups.backshot import Backshot
from ..powerups.big_shot import BigShot
from ..powerups.drunk import Drunk
from ..powerups.fire_rate import FireRate
from ..powerups.freeze import Freeze
from ..powerups.ghost import Ghost
from ..powerups.giant import Giant
from ..powerups.mine import MinePower
from ..powerups.pinball import Pinball
from ..powerups.rapid_shot import RapidShot
from ..powerups.shield import Shield
from ..powerups.shotgun import Shotgun
from ..powerups.speed import Speed
from ..powerups.spinner import Spinner
from ..powerups.teleport import Teleport
from ..powerups.tiny import Tiny
from .. import config


class PowerupController:
    POWERUP_CLASSES: list[type] = [
        Speed, FireRate, RapidShot, ArrowShot,
        Shield, BigShot, MinePower, Freeze,
        Tiny, Ghost, Teleport, Drunk,
        Giant, Spinner, Backshot, Pinball, Shotgun,
    ]

    def __init__(self, events) -> None:
        self._events = events
        self._powerups: list = []
        self._spawn_timer: float = 1500.0
        self._layout: tuple | None = None

    def set_layout(self, layout_controller, map_data: dict) -> None:
        self._layout = (layout_controller, map_data)
        self._powerups = []
        self._spawn_timer = 1500.0

    def clear(self) -> None:
        self._powerups = []

    @property
    def powerups(self) -> list:
        return self._powerups

    def update(self, dt: float, players, ctx) -> None:
        self._spawn_timer -= dt
        if (
            self._spawn_timer <= 0
            and len(self._powerups) < config.MAX_POWERUPS_ON_MAP
            and self._layout
        ):
            self._try_spawn()
            self._spawn_timer = config.POWERUP_SPAWN_INTERVAL_MS + random.randint(-1200, 1500)

        for pu in self._powerups[:]:
            pu.update(dt, ctx)
            for player in players:
                if not player.alive():
                    continue
                if pu.rect.colliderect(player.rect):
                    pu.apply(player, ctx)
                    self._events.publish(
                        GameEvent.POWERUP_PICKED,
                        {"player": player, "kind": type(pu).__name__},
                    )
                    self._powerups.remove(pu)
                    break

    def draw(self, surface: pg.Surface) -> None:
        for pu in self._powerups:
            pu.draw(surface)

    # -------------------------------------------------------------- internals
    def _try_spawn(self) -> None:
        if not self._layout:
            return
        layout, map_data = self._layout
        occupied = {(pu.x, pu.y) for pu in self._powerups}
        spot = layout.get_powerup_spot(map_data, occupied)
        if spot is None:
            return
        cls = random.choice(self.POWERUP_CLASSES)
        self._powerups.append(cls(spot[0], spot[1]))
