"""Selects and renders maps. Maintains a no-repeat map pool."""
import random
from typing import Iterable

from ..entities.wall import Wall
from .. import config


class LayoutController:
    def __init__(self, events) -> None:
        self._events = events
        self._maps: list[dict] = self._build_maps()
        self._available: list[int] = list(range(len(self._maps)))
        self._current: int | None = None

    # ------------------------------------------------------------------ maps
    @staticmethod
    def _build_maps() -> list[dict]:
        W = config.WIDTH
        H = config.HEIGHT
        TOP = config.HUD_HEIGHT
        T = 18
        cx = W // 2
        cy = (TOP + H) // 2

        maps: list[dict] = []

        # 1. Crossfire — a central cross with corner half-walls.
        maps.append({
            "name": "Crossfire",
            "walls": [
                (cx - T // 2, TOP + 90, T, H - TOP - 180),
                (160, cy - T // 2, W - 320, T),
                (90, TOP + 90, 90, T),
                (W - 180, TOP + 90, 90, T),
                (90, H - 100, 90, T),
                (W - 180, H - 100, 90, T),
            ],
            "spawns": [
                (110, TOP + 120, 0),
                (W - 110, H - 120, 180),
                (W - 110, TOP + 120, 270),
                (110, H - 120, 90),
            ],
            "powerup_spots": [
                (cx, TOP + 60),
                (cx, H - 50),
                (90, cy),
                (W - 90, cy),
                (cx - 220, cy - 120),
                (cx + 220, cy + 120),
            ],
        })

        # 2. Pillars — grid of square pillars.
        pillar_rects: list[tuple[int, int, int, int]] = []
        for col_x in (W // 4, W // 2, 3 * W // 4):
            for row_y in (TOP + 130, (TOP + H) // 2, H - 90):
                pillar_rects.append((col_x - 32, row_y - 32, 64, 64))
        maps.append({
            "name": "Pillars",
            "walls": pillar_rects,
            "spawns": [
                (70, TOP + 60, 0),
                (W - 70, H - 60, 180),
                (70, H - 60, 90),
                (W - 70, TOP + 60, 270),
            ],
            "powerup_spots": [
                (W // 2, TOP + 70),
                (W // 2, H - 50),
                (70, cy),
                (W - 70, cy),
                (W // 8, (TOP + H) // 2),
                (W - W // 8, (TOP + H) // 2),
            ],
        })

        # 3. Labyrinth — interlocking L-shapes around centre passage.
        maps.append({
            "name": "Labyrinth",
            "walls": [
                (200, TOP + 80, T, 180),
                (200, TOP + 80, 200, T),
                (400 - T, TOP + 80, T, 100),
                (W - 400, TOP + 80, T, 180),
                (W - 400, TOP + 80, 200, T),
                (W - 200 - T, TOP + 80, T, 100),
                (200, H - 260, T, 180),
                (200, H - 100, 200, T),
                (400 - T, H - 180, T, 100),
                (W - 400, H - 260, T, 180),
                (W - 400, H - 100, 200, T),
                (W - 200 - T, H - 180, T, 100),
                (cx - 110, cy - 80, 220, T),
                (cx - 110, cy + 80, 220, T),
            ],
            "spawns": [
                (90, TOP + 70, 0),
                (W - 90, H - 70, 180),
                (W - 90, TOP + 70, 270),
                (90, H - 70, 90),
            ],
            "powerup_spots": [
                (cx, cy),
                (cx - 240, TOP + 70),
                (cx + 240, H - 60),
                (90, cy),
                (W - 90, cy),
            ],
        })

        # 5. Bunkers — L-shaped corner cover + a small centre block.
        maps.append({
            "name": "Bunkers",
            "walls": [
                # top-left L
                (90, TOP + 90, 200, T),
                (90, TOP + 90, T, 110),
                # top-right L
                (W - 290, TOP + 90, 200, T),
                (W - 90 - T, TOP + 90, T, 110),
                # bottom-left L
                (90, H - 90 - T, 200, T),
                (90, H - 200, T, 110),
                # bottom-right L
                (W - 290, H - 90 - T, 200, T),
                (W - 90 - T, H - 200, T, 110),
                # centre cross
                (cx - 50, cy - T // 2, 100, T),
                (cx - T // 2, cy - 50, T, 100),
            ],
            "spawns": [
                (60, TOP + 60, 0),
                (W - 60, H - 60, 180),
                (W - 60, TOP + 60, 270),
                (60, H - 60, 90),
            ],
            "powerup_spots": [
                (cx, cy),
                (cx, TOP + 80),
                (cx, H - 60),
                (60, cy),
                (W - 60, cy),
            ],
        })

        # 6. Channels — alternating long horizontal walls (zig-zag corridors).
        ch_t = T
        maps.append({
            "name": "Channels",
            "walls": [
                (140, TOP + 130, int(W * 0.55), ch_t),
                (int(W * 0.30), TOP + 280, int(W * 0.55), ch_t),
                (140, cy + 30, int(W * 0.55), ch_t),
                (int(W * 0.30), H - 200, int(W * 0.55), ch_t),
                (140, H - 90, int(W * 0.55), ch_t),
            ],
            "spawns": [
                (70, TOP + 70, 0),
                (W - 70, H - 70, 180),
                (W - 70, TOP + 70, 0),
                (70, H - 70, 180),
            ],
            "powerup_spots": [
                (cx, TOP + 200),
                (cx, cy),
                (cx, H - 160),
                (60, cy),
                (W - 60, cy),
            ],
        })

        # 7. Arena — wide-open arena with four small pillars.
        maps.append({
            "name": "Arena",
            "walls": [
                (int(W * 0.30) - 30, cy - 30, 60, 60),
                (int(W * 0.70) - 30, cy - 30, 60, 60),
                (cx - 30, TOP + 170, 60, 60),
                (cx - 30, H - 230, 60, 60),
            ],
            "spawns": [
                (90, TOP + 90, 0),
                (W - 90, H - 90, 180),
                (W - 90, TOP + 90, 270),
                (90, H - 90, 90),
            ],
            "powerup_spots": [
                (cx, cy),
                (cx, TOP + 80),
                (cx, H - 60),
                (140, cy),
                (W - 140, cy),
                (int(W * 0.30), cy - 130),
                (int(W * 0.70), cy + 130),
            ],
        })

        # 4. Coliseum — central fortress with door gaps.
        maps.append({
            "name": "Coliseum",
            "walls": [
                (cx - 130, cy - 110, 110, T),
                (cx + 20, cy - 110, 110, T),
                (cx - 130, cy + 110 - T, 110, T),
                (cx + 20, cy + 110 - T, 110, T),
                (cx - 130, cy - 110, T, 90),
                (cx - 130, cy + 25, T, 85),
                (cx + 130 - T, cy - 110, T, 90),
                (cx + 130 - T, cy + 25, T, 85),
                (220, TOP + 110, 70, T),
                (220, TOP + 110, T, 70),
                (W - 290, TOP + 110, 70, T),
                (W - 220 - T, TOP + 110, T, 70),
                (220, H - 110 - T, 70, T),
                (220, H - 180, T, 70),
                (W - 290, H - 110 - T, 70, T),
                (W - 220 - T, H - 180, T, 70),
            ],
            "spawns": [
                (90, TOP + 70, 0),
                (W - 90, H - 70, 180),
                (W - 90, TOP + 70, 270),
                (90, H - 70, 90),
            ],
            "powerup_spots": [
                (cx, cy),
                (cx, TOP + 70),
                (cx, H - 50),
                (90, cy),
                (W - 90, cy),
            ],
        })

        return maps

    # ------------------------------------------------------------------ API
    def select_map(self) -> dict:
        if not self._available:
            self._available = [i for i in range(len(self._maps)) if i != self._current]
        idx = random.choice(self._available)
        self._available.remove(idx)
        self._current = idx
        return self._maps[idx]

    @property
    def current_map(self) -> dict | None:
        return None if self._current is None else self._maps[self._current]

    @property
    def maps(self) -> list[dict]:
        return self._maps

    def build_walls(self, map_data: dict) -> list[Wall]:
        return [Wall(x, y, w, h) for (x, y, w, h) in map_data["walls"]]

    def get_spawns(self, map_data: dict, count: int) -> list[tuple[float, float, float]]:
        spawns = list(map_data["spawns"])
        random.shuffle(spawns)
        return spawns[:count]

    def get_powerup_spot(
        self,
        map_data: dict,
        occupied: Iterable[tuple[float, float]],
    ) -> tuple[float, float] | None:
        occ = set(occupied)
        spots = [s for s in map_data["powerup_spots"] if s not in occ]
        return random.choice(spots) if spots else None
