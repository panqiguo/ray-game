from __future__ import annotations

from pyray import *  # type: ignore

from raygame.content import CARD_DEFS, GROWTH_DEFS
from raygame.model.defs import ActionDef, InputRequirement
from raygame.model.enums import ResultType, SUIT_LABELS
from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.rules import (
    claim_growth,
    choose_dialogue_option,
    close_modal,
    continue_dialogue,
    finish_dialogue,
    open_modal,
    open_overlay,
    requirement_is_slotted,
    select_card_input,
    select_item_input,
    select_resource_input,
)

from .ui_core import begin_layer, centered_rect, clickable, draw_frame, draw_scrim, end_layer, layout, text_button, wrap_text_lines
from .ui_tags import ITEM_LABELS, RESOURCE_LABELS


def draw_hud(font: Font | None, state: GameState) -> None:
    begin_layer("hud", interactive=(state.modal.kind in {"", "profile"}))
    hud = layout().hud
    draw_frame(hud, Color(20, 22, 29, 245))
    _hud_block(font, Rectangle(hud.x + 18, hud.y + 10, 140, 32), "生命", f"{state.attributes.health}/{state.attributes.max_health}", Color(214, 112, 112, 255))
    _hud_block(font, Rectangle(hud.x + 170, hud.y + 10, 140, 32), "压力", f"{state.attributes.stress}/{state.attributes.max_stress}", Color(208, 182, 108, 255))
    draw_text(font, f"第 {state.day} 天", int(hud.x + hud.width - 248), int(hud.y + 17), 18, Color(198, 198, 198, 255))
    if text_button(font, Rectangle(hud.x + hud.width - 148, hud.y + 10, 120, 34), f"档案 {state.growth_points}", 18, disabled=(state.modal.kind not in {"", "profile"})):
        if state.modal.kind == "profile":
            close_modal(state)
        else:
            open_modal(state, "profile")
    end_layer("hud")


def draw_hand(font: Font | None, state: GameState, action: ActionDef | None = None) -> None:
    hand = layout().hand
    draw_frame(hand, Color(18, 20, 26, 250))
    draw_text(font, "手牌", int(hand.x) + 18, int(hand.y) + 14, 22, RAYWHITE)
    draw_text(font, "牌堆", int(hand.x) + 520, int(hand.y) + 14, 20, LIGHTGRAY)
    draw_pile_button(font, Rectangle(hand.x + 578, hand.y + 10, 112, 32), "牌库", len(state.deck.draw_pile), state, "draw_pile")
    draw_pile_button(font, Rectangle(hand.x + 702, hand.y + 10, 112, 32), "弃牌", len(state.deck.discard_pile), state, "discard_pile")
    x = int(hand.x) + 18
    y = int(hand.y) + 48
    for index, card_id in enumerate(state.deck.hand):
        rect = Rectangle(x, y, 150, 106)
        selected = state.selected_input.kind == "card" and state.selected_input.index == index
        slotted = state.assembly.slotted_card_index == index
        if draw_compact_card(font, rect, card_id, selected or slotted):
            select_card_input(state, card_id, index)
        x += 162
        if x > hand.x + hand.width - 260:
            break
    inventory_rect = Rectangle(hand.x + hand.width - 226, hand.y + 10, 214, hand.height - 20)
    draw_inventory_panel(font, inventory_rect, state, action)


def draw_pile_button(font: Font | None, rect: Rectangle, label: str, count: int, state: GameState, modal_kind: str) -> None:
    active = state.modal.kind == modal_kind
    draw_frame(rect, Color(80, 66, 47, 255) if active else Color(24, 27, 34, 255), Color(190, 162, 96, 255) if active else Color(82, 88, 102, 220))
    draw_text(font, label, int(rect.x) + 10, int(rect.y) + 6, 16, RAYWHITE)
    draw_text(font, str(count), int(rect.x) + 76, int(rect.y) + 6, 16, Color(212, 196, 132, 255))
    if clickable(rect):
        if state.modal.kind == modal_kind:
            close_modal(state)
        elif state.modal.kind == "location":
            open_overlay(state, modal_kind)
        elif state.modal.kind == "":
            open_modal(state, modal_kind)


def draw_compact_card(font: Font | None, rect: Rectangle, card_id: str, selected: bool, interactive: bool = True) -> bool:
    card = CARD_DEFS[card_id]
    fill = Color(62, 43, 40, 255) if card.is_negative else Color(29, 33, 40, 255)
    border = Color(146, 86, 78, 255) if card.is_negative else Color(95, 99, 107, 220)
    if selected:
        border = Color(201, 165, 88, 255)
    clicked = clickable(rect) if interactive else False
    draw_frame(rect, fill, border)
    draw_text(font, card.title, int(rect.x) + 12, int(rect.y) + 12, 22, RAYWHITE)
    draw_text(font, SUIT_LABELS[card.suit], int(rect.x) + 12, int(rect.y) + 44, 18, LIGHTGRAY)
    draw_text(font, f"点数 {card.points}", int(rect.x) + 12, int(rect.y) + 68, 18, Color(212, 196, 132, 255))
    if card.is_negative:
        draw_text(font, "负面", int(rect.x) + 96, int(rect.y) + 68, 18, Color(210, 126, 110, 255))
    return clicked


def draw_inventory_panel(font: Font | None, rect: Rectangle, state: GameState, action: ActionDef | None) -> None:
    draw_frame(rect, Color(16, 18, 24, 255), Color(76, 82, 96, 220))
    draw_text(font, "物品", int(rect.x) + 14, int(rect.y) + 10, 22, RAYWHITE)
    slots = [
        ("resource", "money", "金币", state.resources.money),
        ("resource", "cigarettes", "烟卷", state.resources.cigarettes),
        ("item", "clothes", "华美衣服", state.world.inventory.get("clothes", 0)),
        ("item", "car_key", "钥匙", state.world.inventory.get("car_key", 0)),
        ("item", "repair_case_item", "任务物", state.world.inventory.get("repair_case_item", 0)),
        ("item", "gun", "枪", state.world.inventory.get("gun", 0)),
    ]
    cell_w = (rect.width - 38) * 0.5
    cell_h = 58
    for index, (kind, key, label, amount) in enumerate(slots):
        col = index % 2
        row = index // 2
        cell = Rectangle(rect.x + 14 + col * (cell_w + 10), rect.y + 42 + row * (cell_h + 10), cell_w, cell_h)
        requirement = _find_requirement(action, kind, key)
        active = requirement is not None and requirement_is_slotted(state, requirement)
        selected = state.selected_input.kind == kind and state.selected_input.key == key
        disabled = amount <= 0
        fill = Color(84, 68, 46, 255) if active else Color(24, 27, 34, 255)
        border = Color(190, 162, 96, 255) if (active or selected) else Color(82, 88, 102, 220)
        if disabled:
            fill = Color(20, 22, 28, 255)
            border = Color(60, 64, 74, 180)
        draw_frame(cell, fill, border)
        if not disabled and clickable(cell):
            if kind == "resource":
                select_resource_input(state, key)
            else:
                select_item_input(state, key)
        draw_text(font, label, int(cell.x) + 10, int(cell.y) + 8, 16, RAYWHITE if not disabled else Color(110, 110, 110, 255))
        draw_text(font, str(amount), int(cell.x) + 10, int(cell.y) + 30, 18, Color(212, 196, 132, 255) if not disabled else Color(100, 100, 100, 255))


def draw_result_strip(font: Font | None, rect: Rectangle, row: tuple[ResultType, ...], scale: float = 1.0) -> None:
    cell_w = (rect.width - 20) / 6.0
    x = rect.x
    for result in row:
        if result == ResultType.FAIL:
            fill, label = Color(124, 66, 66, 255), "失"
        elif result == ResultType.COST:
            fill, label = Color(144, 126, 70, 255), "代"
        else:
            fill, label = Color(74, 134, 92, 255), "成"
        cell = Rectangle(x, rect.y, cell_w - 4, rect.height)
        draw_frame(cell, fill, Color(22, 22, 22, 180))
        draw_text(font, label, int(cell.x + 10 * scale), int(cell.y + 4 * scale), max(10, int(round(16 * scale))), RAYWHITE)
        x += cell_w


def draw_message_feed(font: Font | None, rect: Rectangle, state: GameState) -> None:
    draw_frame(rect, Color(16, 18, 24, 232), Color(78, 84, 96, 210))
    draw_text(font, "消息", int(rect.x) + 12, int(rect.y) + 10, 20, RAYWHITE)
    inner_x = int(rect.x) + 12
    inner_w = int(rect.width) - 24
    y = int(rect.y) + 40
    if state.last_resolution is not None:
        draw_text(font, "最近判定", inner_x, y, 15, Color(212, 196, 132, 255))
        y += 18
        meta = ""
        if state.last_resolution.value is not None:
            meta = f"值 {state.last_resolution.value}"
        if meta:
            draw_text(font, meta, inner_x, y, 14, Color(225, 205, 130, 255))
            y += 18
        for line in wrap_text_lines(font, state.last_resolution.text, inner_w, 14):
            draw_text(font, line, inner_x, y, 14, LIGHTGRAY)
            y += 16
        y += 10
        draw_rectangle_rec(Rectangle(rect.x + 12, y, rect.width - 24, 1), Color(70, 74, 84, 180))
        y += 14
    draw_text(font, "行动记录", inner_x, y, 15, Color(212, 196, 132, 255))
    y += 20
    entries = list(reversed(state.action_log[-6:]))
    if not entries:
        draw_text(font, "暂无记录。", inner_x, y, 14, Color(128, 128, 128, 255))
        return
    for entry in entries:
        for line in wrap_text_lines(font, f"· {entry}", inner_w, 14):
            draw_text(font, line, inner_x, y, 14, Color(196, 196, 196, 255))
            y += 16
        y += 4
        if y > rect.y + rect.height - 24:
            break


def draw_profile_modal(font: Font | None, state: GameState, growth_defs=GROWTH_DEFS) -> None:
    if state.modal.kind != "profile":
        return
    begin_layer("profile", interactive=True)
    rect = Rectangle(layout().hud.x + layout().hud.width - 470, layout().hud.y + layout().hud.height + 12, 470, 420)
    draw_scrim(Rectangle(0, 0, float(get_screen_width()), float(get_screen_height())))
    draw_frame(rect, Color(16, 18, 24, 250), Color(118, 118, 118, 220))
    draw_text(font, "个人档案", int(rect.x) + 20, int(rect.y) + 18, 28, RAYWHITE)
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", 16):
        close_modal(state)
        end_layer("profile")
        return
    draw_text(font, f"成长点数 {state.growth_points}", int(rect.x) + 20, int(rect.y) + 64, 18, Color(212, 196, 132, 255))
    draw_text(font, f"已拥有 {len(state.unlocked_growths)} 项成长", int(rect.x) + 180, int(rect.y) + 64, 18, LIGHTGRAY)
    draw_text(font, f"生命 {state.attributes.health}/{state.attributes.max_health}    压力 {state.attributes.stress}/{state.attributes.max_stress}", int(rect.x) + 20, int(rect.y) + 88, 18, LIGHTGRAY)
    inventory = ", ".join(
        f"{ITEM_LABELS.get(key, key)} x{amount}" for key, amount in sorted(state.world.inventory.items()) if amount > 0
    ) or "无"
    draw_text(font, f"持有物：{inventory}", int(rect.x) + 20, int(rect.y) + 114, 17, LIGHTGRAY)
    y = int(rect.y) + 156
    draw_text(font, "可选成长", int(rect.x) + 20, y - 24, 18, Color(212, 196, 132, 255))
    for growth_id in state.pending_growth_choices:
        growth = growth_defs[growth_id]
        disabled = state.growth_points <= 0
        if text_button(font, Rectangle(rect.x + 20, y, 188, 32), growth.title, 18, disabled=disabled):
            claim_growth(state, growth_id)
            end_layer("profile")
            return
        draw_text(font, growth.description, int(rect.x) + 20, y + 40, 17, LIGHTGRAY)
        y += 82
    if not state.pending_growth_choices:
        draw_text(font, "当前没有新的成长可选。", int(rect.x) + 20, y + 4, 17, Color(140, 140, 140, 255))
    if state.unlocked_growths:
        yy = int(rect.y) + 156
        draw_text(font, "已拥有成长", int(rect.x) + 244, yy - 24, 18, Color(212, 196, 132, 255))
        for growth_id in sorted(state.unlocked_growths):
            draw_text(font, f"· {growth_defs[growth_id].title}", int(rect.x) + 244, yy, 17, LIGHTGRAY)
            yy += 24
    end_layer("profile")


def draw_card_pile_modal(font: Font | None, state: GameState) -> None:
    if state.modal.kind not in {"draw_pile", "discard_pile"}:
        return
    begin_layer("pile_modal", interactive=True)
    pile = state.deck.draw_pile if state.modal.kind == "draw_pile" else state.deck.discard_pile
    title = "牌库" if state.modal.kind == "draw_pile" else "弃牌堆"
    rect = centered_rect(860, 520, -6)
    draw_scrim(layout().stage)
    draw_frame(rect, Color(16, 18, 24, 250), Color(118, 118, 118, 220))
    draw_text(font, title, int(rect.x) + 20, int(rect.y) + 18, 28, RAYWHITE)
    trauma_count = pile.count("trauma")
    draw_text(font, f"共 {len(pile)} 张    创伤 {trauma_count} 张", int(rect.x) + 20, int(rect.y) + 54, 18, Color(212, 196, 132, 255))
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", 16):
        close_modal(state)
        end_layer("pile_modal")
        return
    x = int(rect.x) + 20
    y = int(rect.y) + 92
    for card_id in pile:
        card_rect = Rectangle(x, y, 150, 92)
        draw_compact_card(font, card_rect, card_id, False, interactive=False)
        x += 162
        if x > rect.x + rect.width - 170:
            x = int(rect.x) + 20
            y += 104
    end_layer("pile_modal")


def draw_dialogue_modal(font: Font | None, state: GameState) -> None:
    if state.modal.kind != "dialogue" or state.active_dialogue is None:
        return
    begin_layer("dialogue_modal", interactive=True)
    rect = centered_rect(920, 560, -6)
    draw_scrim(layout().stage)
    draw_frame(rect, Color(16, 18, 24, 250), Color(118, 118, 118, 220))
    draw_text(font, state.active_dialogue.title, int(rect.x) + 24, int(rect.y) + 18, 30, RAYWHITE)
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", 16):
        finish_dialogue(state)
        end_layer("dialogue_modal")
        return
    history_rect = Rectangle(rect.x + 24, rect.y + 64, rect.width - 48, rect.height - 180)
    y = int(history_rect.y)
    for block in state.active_dialogue.history[-12:]:
        for line in wrap_text_lines(font, block, history_rect.width, 18):
            draw_text(font, line, int(history_rect.x), y, 18, LIGHTGRAY)
            y += 22
        y += 12
        if y > history_rect.y + history_rect.height - 32:
            break
    button_y = rect.y + rect.height - 76
    if state.active_dialogue.choices:
        x = rect.x + 24
        for index, choice in enumerate(state.active_dialogue.choices):
            button = Rectangle(x, button_y, rect.width - 48, 36)
            if text_button(font, button, choice, 18):
                choose_dialogue_option(state, index)
                end_layer("dialogue_modal")
                return
            button_y += 44
    elif state.active_dialogue.finished:
        if text_button(font, Rectangle(rect.x + rect.width - 118, rect.y + rect.height - 48, 94, 30), "结束", 16):
            finish_dialogue(state)
            end_layer("dialogue_modal")
            return
    else:
        if text_button(font, Rectangle(rect.x + rect.width - 118, rect.y + rect.height - 48, 94, 30), "继续", 16):
            continue_dialogue(state)
            end_layer("dialogue_modal")
            return
    end_layer("dialogue_modal")


def _hud_block(font: Font | None, rect: Rectangle, label: str, value: str, color: Color) -> None:
    draw_text(font, label, int(rect.x), int(rect.y), 17, Color(170, 170, 170, 255))
    draw_text(font, value, int(rect.x), int(rect.y) + 16, 24, color)


def _find_requirement(action: ActionDef | None, kind: str, key: str) -> InputRequirement | None:
    if action is None:
        return None
    for requirement in action.inputs:
        if requirement.kind == kind and requirement.key == key:
            return requirement
    return None
