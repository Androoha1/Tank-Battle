"""Renderer: background surface, world composite, and per-state overlays."""
import math
import pygame as pg

from .. import config


class Renderer:
    """Owns the off-screen world buffer, the background tile, and all fonts.

    State classes call :meth:`draw_play` to composite the game world, then
    call one of the overlay methods (draw_pause / draw_round_end /
    draw_match_over) for their own state-specific chrome.
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

        players_ctrl.draw_hud(screen)

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

    # ---------------------------------------------------------------- overlays
    def draw_pause(self, screen: pg.Surface, pulse: float) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        anim = (math.sin(pulse * 4) + 1) / 2
        title = self._title_font.render("PAUSED", True, (235, 240, 250))
        screen.blit(title, title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 60)))

        col = (int(140 + 80 * anim), 210, 255)
        hint = self._sub_font.render(
            "P / ESC : resume    ·    Q : quit to menu", True, col
        )
        screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 40)))

    def draw_round_end(self, screen: pg.Surface, winner) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        screen.blit(overlay, (0, 0))

        if winner:
            text = f"{winner.name} WINS THE ROUND"
            color = winner.colors["accent"]
        else:
            text = "DRAW"
            color = (220, 220, 230)
        surf = self._sub_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
        panel = pg.Surface((rect.width + 60, rect.height + 30), pg.SRCALPHA)
        pg.draw.rect(panel, (15, 18, 28, 220), panel.get_rect(), border_radius=10)
        pg.draw.rect(panel, (*color, 180), panel.get_rect(), border_radius=10, width=2)
        screen.blit(panel, panel.get_rect(center=rect.center).topleft)
        screen.blit(surf, rect)

    def draw_match_over(self, screen: pg.Surface, match_winner, players_ctrl) -> None:
        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        if match_winner:
            text = f"{match_winner.name} WINS THE MATCH"
            color = match_winner.colors["accent"]
        else:
            text = "MATCH OVER"
            color = (220, 220, 230)
        surf = self._title_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 30))
        screen.blit(surf, rect)

        y = rect.bottom + 30
        for p in players_ctrl.players:
            s = self._sub_font.render(
                f"{p.name}: {players_ctrl.scores.get(p, 0)}", True, p.colors["accent"]
            )
            screen.blit(s, s.get_rect(center=(config.WIDTH // 2, y)))
            y += 36

        hint = self._tiny_font.render(
            "Press ENTER or ESC to return to menu", True, (180, 190, 210)
        )
        screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 60)))
