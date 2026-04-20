from __future__ import annotations

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.rules.progression import advance_clock, change_health, change_stress
from raygame.screens.widgets import text_button
from .ui_text import ui_text_size, ui_text_style


def draw_debug_panel(font: Font | None, state: GameState) -> None:
    if not state.debug_open:
        return
    rect = Rectangle(1080, 92, 330, 300)
    draw_rectangle_rounded(rect, 0.08, 8, Color(16, 17, 22, 245))
    title_style = ui_text_style("subtitle")
    button_size = ui_text_size("body")
    draw_text(font, "调试", 1096, 104, title_style.size, title_style.color)
    y = 142
    if text_button(font, Rectangle(1096, y, 140, 30), "加钱 +20", button_size):
        state.world.inventory["money"] = state.world.inventory.get("money", 0) + 20
    if text_button(font, Rectangle(1248, y, 140, 30), "压力 +2", button_size):
        change_stress(state, 2)
    y += 40
    if text_button(font, Rectangle(1096, y, 140, 30), "生命 -1", button_size):
        change_health(state, -1)
    if text_button(font, Rectangle(1248, y, 140, 30), "烟卷 +1", button_size):
        state.world.inventory["cigarettes"] = state.world.inventory.get("cigarettes", 0) + 1
    y += 40
    if text_button(font, Rectangle(1096, y, 140, 30), "钥匙 +1", button_size):
        state.world.inventory["car_key"] = state.world.inventory.get("car_key", 0) + 1
    if text_button(font, Rectangle(1248, y, 140, 30), "追击 +1", button_size):
        advance_clock(state, "pursuit", 1)
