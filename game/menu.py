"""Main-menu UI: mode selection, player count, win target, join IP."""
import math
import pygame as pg

from . import config


MODES = ["LOCAL", "HOST LAN", "JOIN LAN"]
PLAYER_COUNTS = [2, 3, 4]
WIN_TARGETS = [5, 10, 0]   # 0 = endless
WIN_LABELS = ["First to 5", "First to 10", "Endless"]


class MenuItem:
    """One row of the menu."""

    def __init__(self, label: str, kind: str, key: str | None = None, enabled_when=None) -> None:
        self.label = label
        self.kind = kind            # "choice" | "action" | "input"
        self.key = key
        self.enabled_when = enabled_when

    def enabled(self, state: dict) -> bool:
        if self.enabled_when is None:
            return True
        if self.enabled_when == "local":
            return state["mode"] == 0
        if self.enabled_when == "join":
            return state["mode"] == 2
        return True


class Menu:
    """Controller for the main menu screen."""

    def __init__(self, layout_controller) -> None:
        self._layout = layout_controller
        self._state = {
            "mode": 0,
            "players": 0,         # index into PLAYER_COUNTS
            "win_target": 0,      # index into WIN_TARGETS
            "ip": "127.0.0.1",
            "port": "5555",
        }
        self._items: list[MenuItem] = [
            MenuItem("MODE", "choice", "mode"),
            MenuItem("PLAYERS", "choice", "players", enabled_when="local"),
            MenuItem("WIN TARGET", "choice", "win_target"),
            MenuItem("SERVER IP", "input", "ip", enabled_when="join"),
            MenuItem("PORT", "input", "port"),
            MenuItem("START GAME", "action", "start"),
            MenuItem("QUIT", "action", "quit"),
        ]
        self._selected = 0
        self._editing = False
        self._pulse = 0.0
        self._cursor_blink = 0.0
        self._title_font = pg.font.SysFont("arialblack", 110, bold=True)
        self._sub_font = pg.font.SysFont("arialblack", 26, bold=True)
        self._mid_font = pg.font.SysFont("arialblack", 22, bold=True)
        self._small_font = pg.font.SysFont("arial", 16, bold=True)
        self._tiny_font = pg.font.SysFont("arial", 14)
        self._map_thumbs: list[tuple[str, pg.Surface]] = self._build_thumbnails()

    # ---------------------------------------------------------------- input
    def handle_event(self, ev: pg.event.Event) -> dict | None:
        if ev.type != pg.KEYDOWN:
            return None

        if self._editing:
            return self._handle_edit(ev)

        item = self._items[self._selected]
        if ev.key in (pg.K_UP, pg.K_w):
            self._move(-1)
        elif ev.key in (pg.K_DOWN, pg.K_s):
            self._move(1)
        elif ev.key in (pg.K_LEFT, pg.K_a):
            self._cycle(-1)
        elif ev.key in (pg.K_RIGHT, pg.K_d):
            self._cycle(1)
        elif ev.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
            if item.kind == "action":
                if item.key == "start":
                    return self.start_payload()
                if item.key == "quit":
                    return {"action": "quit"}
            elif item.kind == "input":
                self._editing = True
        elif ev.key == pg.K_ESCAPE:
            return {"action": "quit"}
        return None

    def _handle_edit(self, ev: pg.event.Event) -> dict | None:
        item = self._items[self._selected]
        if not item.key or item.kind != "input":
            self._editing = False
            return None
        key = item.key
        val: str = str(self._state[key])
        if ev.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_ESCAPE):
            self._editing = False
        elif ev.key == pg.K_BACKSPACE:
            self._state[key] = val[:-1]
        else:
            ch = ev.unicode
            if ch and (ch.isalnum() or ch in ".:-_") and len(val) < 24:
                self._state[key] = val + ch
        return None

    def _move(self, delta: int) -> None:
        n = len(self._items)
        for _ in range(n):
            self._selected = (self._selected + delta) % n
            if self._items[self._selected].enabled(self._state):
                return

    def _cycle(self, delta: int) -> None:
        item = self._items[self._selected]
        if item.kind != "choice" or item.key is None:
            return
        if item.key == "mode":
            self._state["mode"] = (self._state["mode"] + delta) % len(MODES)
        elif item.key == "players":
            self._state["players"] = (self._state["players"] + delta) % len(PLAYER_COUNTS)
        elif item.key == "win_target":
            self._state["win_target"] = (self._state["win_target"] + delta) % len(WIN_TARGETS)

    # --------------------------------------------------------------- public
    def start_payload(self) -> dict:
        s = self._state
        return {
            "action": "start",
            "mode": MODES[s["mode"]].lower().replace(" ", "_"),
            "players": PLAYER_COUNTS[s["players"]],
            "win_target": WIN_TARGETS[s["win_target"]],
            "ip": s["ip"],
            "port": int(s["port"]) if s["port"].isdigit() else 5555,
        }

    # ---------------------------------------------------------------- tick
    def update(self, dt: float) -> None:
        self._pulse = (self._pulse + dt * 0.005) % math.tau
        self._cursor_blink = (self._cursor_blink + dt) % 1000

    # ---------------------------------------------------------------- draw
    def draw(self, surface: pg.Surface, bg: pg.Surface) -> None:
        surface.blit(bg, (0, 0))

        # Title.
        title = self._title_font.render("TANKONS", True, (235, 240, 250))
        title_rect = title.get_rect(center=(config.WIDTH // 2, 130))
        halo = pg.Surface((title.get_width() + 80, title.get_height() + 60), pg.SRCALPHA)
        pg.draw.ellipse(halo, (110, 160, 255, 35), halo.get_rect())
        surface.blit(halo, halo.get_rect(center=title_rect.center).topleft)
        surface.blit(title, title_rect)

        sub = self._sub_font.render("multiplayer top-down tank battle", True, (170, 185, 210))
        surface.blit(sub, sub.get_rect(center=(config.WIDTH // 2, 200)))

        # Menu panel.
        panel_w, panel_h = 540, 360
        panel_x = (config.WIDTH - panel_w) // 2 - 200
        panel_y = 250
        panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        pg.draw.rect(panel, (16, 20, 32, 220), panel.get_rect(), border_radius=12)
        pg.draw.rect(panel, (70, 100, 150, 220), panel.get_rect(), border_radius=12, width=1)
        surface.blit(panel, (panel_x, panel_y))

        y = panel_y + 24
        for i, item in enumerate(self._items):
            enabled = item.enabled(self._state)
            selected = i == self._selected
            self._draw_item(surface, item, panel_x + 22, y, panel_w - 44, selected, enabled)
            y += 44

        # Map thumbs to the right.
        self._draw_thumbs(surface, panel_x + panel_w + 30, panel_y)

        # Footer hints.
        hint = self._tiny_font.render(
            "  W/S or ARROWS: select   ·   A/D or LEFT/RIGHT: change   ·   ENTER: confirm   ·   ESC: quit  ",
            True, (160, 170, 195),
        )
        surface.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 30)))

    def _draw_item(self, surface, item: MenuItem, x: int, y: int, w: int,
                   selected: bool, enabled: bool) -> None:
        # background row
        if selected:
            row = pg.Surface((w, 36), pg.SRCALPHA)
            tint = (90, 160, 240, 60) if enabled else (90, 90, 100, 30)
            pg.draw.rect(row, tint, row.get_rect(), border_radius=6)
            surface.blit(row, (x, y))
            # selection arrow
            pulse = (math.sin(self._pulse * 6) + 1) / 2
            tri = [(x - 12, y + 18 - 6), (x - 4, y + 18), (x - 12, y + 18 + 6)]
            pg.draw.polygon(surface, (140 + int(60 * pulse), 200, 255), tri)

        text_color = (235, 240, 250) if enabled else (90, 95, 110)
        accent = (140, 200, 255) if enabled else (90, 95, 110)

        label = self._mid_font.render(item.label, True, text_color)
        surface.blit(label, (x + 8, y + 6))

        # value
        s = self._state
        if item.kind == "choice":
            if item.key == "mode":
                val = MODES[s["mode"]]
            elif item.key == "players":
                val = f"{PLAYER_COUNTS[s['players']]} players"
            elif item.key == "win_target":
                val = WIN_LABELS[s["win_target"]]
            else:
                val = "?"
            val_surf = self._mid_font.render(val, True, accent)
            surface.blit(val_surf, val_surf.get_rect(midright=(x + w - 10, y + 18)))
        elif item.kind == "input":
            if item.key is None:
                return
            val = str(s[item.key])
            if self._editing and selected:
                cursor = "|" if (self._cursor_blink // 500) % 2 == 0 else " "
                val = val + cursor
            val_surf = self._small_font.render(val, True, accent)
            box_rect = val_surf.get_rect(midright=(x + w - 10, y + 18))
            pg.draw.rect(surface, (30, 35, 55), box_rect.inflate(16, 6), border_radius=4)
            pg.draw.rect(surface, accent, box_rect.inflate(16, 6), border_radius=4, width=1)
            surface.blit(val_surf, box_rect)
        elif item.kind == "action":
            val_surf = self._mid_font.render(">", True, accent)
            surface.blit(val_surf, val_surf.get_rect(midright=(x + w - 10, y + 18)))

    def _build_thumbnails(self) -> list[tuple[str, pg.Surface]]:
        thumbs = []
        for m in self._layout.maps:
            thumb = self._render_map_thumbnail(m)
            thumbs.append((m["name"], thumb))
        return thumbs

    @staticmethod
    def _render_map_thumbnail(map_data: dict, scale: float = 0.18) -> pg.Surface:
        W = config.WIDTH
        H = config.HEIGHT - config.HUD_HEIGHT
        sw = int(W * scale)
        sh = int(H * scale)
        s = pg.Surface((sw, sh), pg.SRCALPHA)
        pg.draw.rect(s, (24, 30, 46, 230), (0, 0, sw, sh), border_radius=4)
        pg.draw.rect(s, (90, 130, 200, 200), (0, 0, sw, sh), border_radius=4, width=1)
        for (x, y, w, h) in map_data["walls"]:
            yy = int((y - config.HUD_HEIGHT) * scale)
            xx = int(x * scale)
            ww = max(1, int(w * scale))
            hh = max(1, int(h * scale))
            pg.draw.rect(s, (160, 180, 220), (xx, yy, ww, hh))
        for (px, py) in map_data["powerup_spots"]:
            yy = int((py - config.HUD_HEIGHT) * scale)
            xx = int(px * scale)
            pg.draw.circle(s, (250, 200, 120), (xx, yy), 2)
        return s

    def _draw_thumbs(self, surface: pg.Surface, x: int, y: int) -> None:
        title = self._small_font.render("MAP POOL", True, (170, 185, 210))
        surface.blit(title, (x, y))
        ty = y + 26
        for name, thumb in self._map_thumbs:
            surface.blit(thumb, (x, ty))
            label = self._tiny_font.render(name, True, (200, 210, 230))
            surface.blit(label, (x + thumb.get_width() + 10,
                                 ty + thumb.get_height() // 2 - label.get_height() // 2))
            ty += thumb.get_height() + 12
