from __future__ import annotations

import os

from pyray import *  # type: ignore

from sincity.model.state import GameState
from sincity.rendering import draw_text
from sincity.rules.debug_save import SAVE_PATH, debug_load, debug_save
from sincity.rules.progression import advance_clock, change_energy, change_health
from sincity.rules.rng import RandomSource
from sincity.screens.widgets import text_button
from .ui_text import ui_text_size, ui_text_style


def draw_debug_panel(font: Font | None, state: GameState, rng: RandomSource) -> None:
    if not state.debug_open:
        return
    rect = Rectangle(1080, 92, 330, 340)
    draw_rectangle_rounded(rect, 0.08, 8, Color(16, 17, 22, 245))
    title_style = ui_text_style("subtitle")
    button_size = ui_text_size("body")
    draw_text(font, "调试", 1096, 104, title_style.size, title_style.color)
    y = 142
    if text_button(font, Rectangle(1096, y, 140, 30), "加钱 +20", button_size):
        state.world.inventory["money"] = state.world.inventory.get("money", 0) + 20
    if text_button(font, Rectangle(1248, y, 140, 30), "精力 -2", button_size):
        change_energy(state, -2)
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
    y += 40
    save_exists = os.path.exists(SAVE_PATH)
    file_label = os.path.basename(SAVE_PATH)
    save_btn = f"{'覆盖' if save_exists else '保存'} {file_label}"
    load_btn = f"加载 {file_label}"
    if text_button(font, Rectangle(1096, y, 145, 30), save_btn, button_size):
        debug_save(state, rng)
    if text_button(font, Rectangle(1249, y, 145, 30), load_btn, button_size, disabled=not save_exists):
        debug_load(state, rng)
