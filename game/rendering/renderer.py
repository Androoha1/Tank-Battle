"""Renderer: background surface and world composite."""
import pygame as pg

from .. import config


class Renderer:
    """Owns the off-screen world buffer, the background tile, and all fonts.

    State classes call :meth:`draw_play` to composite the game world, then
    draw their own state-specific overlays using the font properties exposed
    here.
    """

    def __init__(self) -> None:
        self._world_surf = pg.Surface((config.WIDTH, config.HEIGHT))
        self._bg = self._build_background()

        self._title_font = pg.font.SysFont("arialblack", 110, bold=True)
        self._sub_font = pg.font.SysFont("arialblack", 30, bold=True)
        self._mid_font = pg.font.SysFont("arialblack", 24, bold=True)
        self._tiny_font = pg.font.SysFont("arial", 18, bold=True)

    @property
    def background(self) -> pg.Surface:
        return self._bg

    @property
    def title_font(self) -> pg.font.Font:
        return self._title_font

    @property
    def sub_font(self) -> pg.font.Font:
        return self._sub_font

    @property
    def mid_font(self) -> pg.font.Font:
        return self._mid_font

    @property
    def tiny_font(self) -> pg.font.Font:
        return self._tiny_font

    # ---------------------------------------------------------------- setup
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
        for corner in (
            (0, config.HUD_HEIGHT),
            (config.WIDTH, config.HUD_HEIGHT),
            (0, config.HEIGHT),
            (config.WIDTH, config.HEIGHT),
        ):
            radius = 300
            shade = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
            pg.draw.circle(shade, (0, 0, 0, 90), (radius, radius), radius)
            s.blit(
                shade,
                (corner[0] - radius, corner[1] - radius),
                special_flags=pg.BLEND_PREMULTIPLIED,
            )
        return s

    # ---------------------------------------------------------------- world
    def draw_play(
        self,
        screen: pg.Surface,
        world,
        camera,
        powerup_ctrl,
        players_ctrl,
        map_data: dict | None,
        round_num: int,
        match,
    ) -> None:
        ws = self._world_surf
        ws.blit(self._bg, (0, 0))

        for w in world.walls:
            w.draw(ws)
        powerup_ctrl.draw(ws)
        for m in world.mines:
            m.draw(ws)
        for pt in world.particles:
            pt.draw(ws)
        for d in world.debris:
            d.draw(ws)
        for p in players_ctrl.players:
            p.draw(ws)
        for s in world.shots:
            s.draw(ws)
        for sw in world.shockwaves:
            sw.draw(ws)

        ox, oy = camera.shake_offset
        screen.fill((0, 0, 0))
        screen.blit(ws, (ox, oy))

        if camera.flash_alpha > 0 and camera.flash_color is not None:
            overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
            overlay.fill((*camera.flash_color, camera.flash_alpha))
            screen.blit(overlay, (0, 0))

        players_ctrl.draw_hud(screen, match)

        if map_data:
            info = self._tiny_font.render(
                f"{map_data['name']}  ·  Round {round_num}",
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
            screen.blit(bg, box.topleft)
            screen.blit(info, (box.left + pad, box.top + pad // 2))
