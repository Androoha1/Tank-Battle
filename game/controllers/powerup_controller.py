"""Spawns power-ups on the active map and routes pickups."""
import random
import pygame as pg

from ..events import GameEvent
from ..powerups.arrow_shot import ArrowShotEffect
from ..powerups.backshot import BackshotEffect
from ..powerups.big_shot import BigShotEffect
from ..powerups.drunk import DrunkEffect
from ..powerups.fire_rate import FireRateEffect
from ..powerups.freeze import FreezeEffect
from ..powerups.ghost import GhostEffect
from ..powerups.giant import GiantEffect
from ..powerups.mine import MinePowerEffect
from ..powerups.pinball import PinballEffect
from ..powerups.rapid_shot import RapidShotEffect
from ..powerups.shield import ShieldEffect
from ..powerups.shotgun import ShotgunEffect
from ..powerups.speed import SpeedEffect
from ..powerups.spinner import SpinnerEffect
from ..powerups.teleport import TeleportEffect
from ..powerups.tiny import TinyEffect
from ..powerups.pickup import PowerUpPickup
from .. import config


class PowerupController:
    POWERUP_CATALOG: list[type] = [
        SpeedEffect, FireRateEffect, RapidShotEffect, ArrowShotEffect,
        ShieldEffect, BigShotEffect, MinePowerEffect, FreezeEffect,
        TinyEffect, GhostEffect, TeleportEffect, DrunkEffect,
        GiantEffect, SpinnerEffect, BackshotEffect, PinballEffect, ShotgunEffect,
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
                        {"player": player, "kind": pu.name},
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
        cls = random.choice(self.POWERUP_CATALOG)
        self._powerups.append(PowerUpPickup(spot[0], spot[1], cls))
