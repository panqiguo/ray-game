from __future__ import annotations

import os

from pyray import *  # type: ignore

from sincity.model.state import GameState
from sincity.rendering import draw_text
from sincity.rules.debug_save import debug_load, debug_save, slot_path
from sincity.rules.progression import advance_clock, change_energy, change_health
from sincity.rules.rng import RandomSource
from sincity.screens.widgets import pill, text_button
from .ui_text import ui_text_size, ui_text_style

_selected_slot: int = 2


def draw_debug_panel(font: Font | None, state: GameState, rng: RandomSource) -> None:
    global _selected_slot

    if not state.debug_open:
        return
    rect = Rectangle(1080, 92, 330, 340)
    draw_rectangle_rounded(rect, 0.08, 8, Color(16, 17, 22, 245))
    title_style = ui_text_style("subtitle")
    body_style = ui_text_style("body", "muted")
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

    y = 258
    draw_text(font, "━ 存档 ━", 1096, y, body_style.size, body_style.color)
    y += 20

    # Quick save slot (slot 1) — dedicated buttons
    has_quick = os.path.exists(slot_path(1))
    if text_button(font, Rectangle(1096, y, 145, 30), "快速保存", button_size):
        debug_save(state, rng, slot=1)
    if text_button(font, Rectangle(1249, y, 145, 30), "快速加载", button_size, disabled=not has_quick):
        debug_load(state, rng, slot=1)
    y += 34

    # Manual slots (2-4)
    for slot_num in (2, 3, 4):
        exists = os.path.exists(slot_path(slot_num))
        label = f"{slot_num}  {SLOT_LABELS[slot_num]}  {'已保存' if exists else '空'}"
        is_selected = _selected_slot == slot_num
        if pill(font, Rectangle(1096, y, 298, 26), label, selected=is_selected):
            _selected_slot = slot_num
        y += 30

    # Save/Load for selected slot
    selected_exists = os.path.exists(slot_path(_selected_slot))
    if text_button(font, Rectangle(1096, y, 145, 30), "保存", button_size):
        debug_save(state, rng, slot=_selected_slot)
    if text_button(font, Rectangle(1249, y, 145, 30), "加载", button_size, disabled=not selected_exists):
        debug_load(state, rng, slot=_selected_slot)


SLOT_LABELS: dict[int, str] = {
    2: "save_01",
    3: "save_02",
    4: "save_03",
}
