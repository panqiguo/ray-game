from __future__ import annotations

import os
import time

from pyray import *  # type: ignore

from sincity.model.state import GameState
from sincity.rendering import draw_text
from sincity.rules.debug_save import debug_load, debug_save, slot_path
from sincity.rules.progression import add_next_companion_for_debug, remove_companions_for_debug
from sincity.rules.rng import RandomSource

from sincity.game.fields import change_energy, change_health
from sincity.game.notifications import push_notification

from .input_regions import debug_panel_rect
from .ui_core import Z_DEBUG, begin_layer, end_layer
from .ui_text import ui_text_size, ui_text_style
from .widgets import pill, text_button

_selected_slot: int = 2


def draw_debug_panel(font: Font | None, state: GameState, rng: RandomSource) -> None:
    global _selected_slot

    if not state.debug_open:
        return
    begin_layer("debug", z=Z_DEBUG)
    rect = debug_panel_rect()
    draw_rectangle_rec(rect, Color(16, 17, 22, 245))
    draw_rectangle_lines_ex(rect, 1.5, Color(110, 110, 110, 210))
    title_style = ui_text_style("subtitle")
    body_style = ui_text_style("body", "muted")
    button_size = ui_text_size("body")
    draw_text(font, "调试", 1096, 104, title_style.size, title_style.color)
    y = 142
    if text_button(font, Rectangle(1096, y, 140, 30), "加钱 +20", button_size):
        state.world.inventory["money"] = state.world.inventory.get("money", 0) + 20
        state.world.seen_items.add("money")
    if text_button(font, Rectangle(1248, y, 140, 30), "精力 -2", button_size):
        change_energy(state, -2)
    y += 40
    if text_button(font, Rectangle(1096, y, 140, 30), "生命 -1", button_size):
        change_health(state, -1)
    if text_button(font, Rectangle(1248, y, 140, 30), "重启", button_size):
        state.pending_restart = True
    y += 40
    draw_text(font, "同伴：" + _companion_summary(state), 1096, y + 6, body_style.size, body_style.color)
    y += 34
    if text_button(font, Rectangle(1096, y, 140, 30), "添加同伴", button_size, disabled=len(state.companion_actor_ids) >= 2):
        name = add_next_companion_for_debug(state, rng)
        push_notification(state, "success", "同伴加入", name or "队伍已满")
    if text_button(font, Rectangle(1248, y, 140, 30), "移除同伴", button_size, disabled=not state.companion_actor_ids):
        removed = remove_companions_for_debug(state, rng)
        push_notification(state, "warning", "同伴离队", "、".join(removed) if removed else "没有同伴")

    y = 298
    draw_text(font, "━ 存档 ━", 1096, y, body_style.size, body_style.color)
    y += 20

    has_quick = os.path.exists(slot_path(1))
    if text_button(font, Rectangle(1096, y, 145, 30), "快速保存", button_size):
        debug_save(state, rng, slot=1)
        push_notification(state, "success", "快速保存成功")
    if text_button(font, Rectangle(1249, y, 145, 30), "快速加载", button_size, disabled=not has_quick):
        debug_load(state, rng, slot=1)
        push_notification(state, "success", "加载完成")
    y += 34

    for slot_num in (2, 3, 4):
        sp = slot_path(slot_num)
        exists = os.path.exists(sp)
        if exists:
            lt = time.localtime(os.path.getmtime(sp))
            label = f"{slot_num}  {lt.tm_mon}月{lt.tm_mday}日 {lt.tm_hour:02d}:{lt.tm_min:02d}"
        else:
            label = f"{slot_num}  空"
        is_selected = _selected_slot == slot_num
        if pill(font, Rectangle(1096, y, 298, 26), label, selected=is_selected):
            _selected_slot = slot_num
        y += 30

    selected_exists = os.path.exists(slot_path(_selected_slot))
    slot_name = f"存档 {_selected_slot}"
    if text_button(font, Rectangle(1096, y, 145, 30), "保存", button_size):
        debug_save(state, rng, slot=_selected_slot)
        push_notification(state, "success", f"{slot_name} 保存成功")
    if text_button(font, Rectangle(1249, y, 145, 30), "加载", button_size, disabled=not selected_exists):
        debug_load(state, rng, slot=_selected_slot)
        push_notification(state, "success", f"{slot_name} 加载完成")
    end_layer("debug")


def _companion_summary(state: GameState) -> str:
    if not state.companion_actor_ids:
        return "无"
    parts: list[str] = []
    for actor_id in state.companion_actor_ids:
        actor = state.party[actor_id]
        best = max((("暴力", actor.force), ("魅力", actor.charm), ("知识", actor.knowledge), ("敏锐", actor.sense)), key=lambda item: item[1])
        parts.append(f"{actor.name} {best[0]}{best[1]}")
    return "，".join(parts)
