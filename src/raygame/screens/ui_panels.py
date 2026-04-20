from __future__ import annotations

import math

from pyray import *  # type: ignore

from raygame.content import CARD_DEFS, GROWTH_DEFS
from raygame.labels import ITEM_LABELS
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
)

from .ui_core import begin_layer, centered_rect, clickable, draw_frame, draw_scrim, end_layer, layout, measure_text_width, mouse_point, text_button, wrap_text_lines, wrap_text_lines_any
from .ui_text import ui_text_color, ui_text_size, ui_text_style

INVENTORY_PANEL_WIDTH = 324
INVENTORY_PANEL_RIGHT_OFFSET = 336

def draw_hud(font: Font | None, state: GameState) -> None:
    begin_layer("hud", interactive=(state.modal.kind in {"", "profile"}))
    hud = layout().hud
    draw_frame(hud, Color(20, 22, 29, 245))
    _hud_meter(
        font,
        Rectangle(hud.x + 18, hud.y + 8, 140, 36),
        "生命",
        state.attributes.health,
        state.attributes.max_health,
        Color(214, 112, 112, 255),
        Color(76, 40, 40, 255),
    )
    _hud_meter(
        font,
        Rectangle(hud.x + 210, hud.y + 8, 140, 36),
        "压力",
        state.attributes.stress,
        state.attributes.max_stress,
        Color(208, 182, 108, 255),
        Color(78, 66, 34, 255),
    )
    day_style = ui_text_style("body", "muted")
    draw_text(font, f"第 {state.day} 天", int(hud.x + hud.width - 248), int(hud.y + 17), day_style.size, day_style.color)
    if text_button(font, Rectangle(hud.x + hud.width - 148, hud.y + 10, 120, 34), f"档案 {state.growth_points}", ui_text_size("body"), disabled=(state.modal.kind not in {"", "profile"})):
        if state.modal.kind == "profile":
            close_modal(state)
        else:
            open_modal(state, "profile")
    end_layer("hud")


def draw_hand(font: Font | None, state: GameState, action: ActionDef | None = None) -> None:
    hand = layout().hand
    draw_frame(hand, Color(18, 20, 26, 250))
    hand_title_style = ui_text_style("subtitle")
    pile_title_style = ui_text_style("subtitle", "muted", scale=(20 / 24))
    draw_text(font, "手牌", int(hand.x) + 18, int(hand.y) + 14, hand_title_style.size, hand_title_style.color)
    draw_text(font, "牌堆", int(hand.x) + 520, int(hand.y) + 14, pile_title_style.size, pile_title_style.color)
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
    inventory_rect = _inventory_panel_rect()
    draw_inventory_panel(font, inventory_rect, state, action)


def draw_pile_button(font: Font | None, rect: Rectangle, label: str, count: int, state: GameState, modal_kind: str) -> None:
    active = state.modal.kind == modal_kind
    draw_frame(rect, Color(80, 66, 47, 255) if active else Color(24, 27, 34, 255), Color(190, 162, 96, 255) if active else Color(82, 88, 102, 220))
    label_style = ui_text_style("body")
    count_style = ui_text_style("body", "accent")
    draw_text(font, label, int(rect.x) + 10, int(rect.y) + 6, label_style.size, label_style.color)
    draw_text(font, str(count), int(rect.x) + 76, int(rect.y) + 6, count_style.size, count_style.color)
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
    _draw_hand_card_head(font, rect, card)
    _draw_hand_card_suit(font, rect, card)
    if card.is_negative:
        negative_style = ui_text_style("body", "danger")
        draw_text(font, "负面", int(rect.x) + 12, int(rect.y) + 68, negative_style.size, negative_style.color)
    return clicked


def _draw_hand_card_head(font: Font | None, rect: Rectangle, card) -> None:
    name = _hand_card_style_label(card.title)
    number_text = str(card.points)
    number_style = ui_text_style("title", "danger" if card.is_negative else "accent")
    suffix_style = ui_text_style("body", "muted")
    text_size = max(28, number_style.size - 2)
    suffix_size = suffix_style.size
    x = int(rect.x) + 12
    y = int(rect.y) + 12
    draw_text(font, number_text, x, y, text_size, number_style.color)
    draw_text(font, name, x + int(measure_text_width(font, number_text, text_size)) + 6, y + 1, suffix_size, suffix_style.color)


def _draw_hand_card_suit(font: Font | None, rect: Rectangle, card) -> None:
    if card.suit is None:
        return
    suit_label = SUIT_LABELS[card.suit]
    suit_style = ui_text_style("body", "muted" if not card.is_negative else "subtle")
    draw_text(font, suit_label, int(rect.x) + 12, int(rect.y) + 44, suit_style.size, suit_style.color)


def _hand_card_style_label(title: str) -> str:
    if "·" not in title:
        return title
    head, tail = title.split("·", 1)
    return head


def _draw_selected_card_curve(rect: Rectangle) -> None:
    start = Vector2(rect.x + rect.width * 0.5, rect.y + 8)
    end = mouse_point()
    control = Vector2((start.x + end.x) * 0.5, min(start.y, end.y) - max(40.0, abs(end.x - start.x) * 0.18))
    _draw_quadratic_curve(start, control, end, 4.5, Color(212, 196, 132, 235))
    draw_circle_v(end, 4.0, Color(212, 196, 132, 220))


def _draw_quadratic_curve(start: Vector2, control: Vector2, end: Vector2, thickness: float, color: Color) -> None:
    steps = 18
    prev = start
    for index in range(1, steps + 1):
        t = index / steps
        mt = 1.0 - t
        point = Vector2(
            mt * mt * start.x + 2.0 * mt * t * control.x + t * t * end.x,
            mt * mt * start.y + 2.0 * mt * t * control.y + t * t * end.y,
        )
        draw_line_ex(prev, point, thickness, color)
        prev = point


def draw_selected_card_curve_overlay(state: GameState) -> None:
    if state.selected_input.kind == "card" and state.selected_input.index is not None:
        hand = layout().hand
        x = int(hand.x) + 18
        y = int(hand.y) + 48
        for index, _card_id in enumerate(state.deck.hand):
            if index == state.selected_input.index:
                _draw_selected_card_curve(Rectangle(x, y, 150, 106))
                return
            x += 162
            if x > hand.x + hand.width - 260:
                return
    if state.selected_input.kind == "item":
        rect = _selected_inventory_rect(state)
        if rect is not None:
            _draw_selected_card_curve(rect)


def _selected_inventory_rect(state: GameState) -> Rectangle | None:
    key = state.selected_input.key
    if not key:
        return None
    inventory_rect = _inventory_panel_rect()
    slots = _inventory_slots(state)
    match_index = next(
        (index for index, (kind, slot_key, _label, _amount) in enumerate(slots) if kind == state.selected_input.kind and slot_key == key),
        None,
    )
    if match_index is None:
        return None
    columns = max(1, math.ceil(len(slots) / 2))
    rows = max(1, math.ceil(len(slots) / columns))
    cell_w = (inventory_rect.width - 16 - (columns - 1) * 8) / columns
    cell_h = min(44.0, (inventory_rect.height - 42 - (rows - 1) * 10) / rows)
    col = match_index % columns
    row = match_index // columns
    return Rectangle(
        inventory_rect.x + 8 + col * (cell_w + 8),
        inventory_rect.y + 42 + row * (cell_h + 8),
        cell_w,
        cell_h,
    )


def _inventory_panel_rect() -> Rectangle:
    hand = layout().hand
    return Rectangle(hand.x + hand.width - INVENTORY_PANEL_RIGHT_OFFSET, hand.y + 10, INVENTORY_PANEL_WIDTH, hand.height - 20)


def draw_inventory_panel(font: Font | None, rect: Rectangle, state: GameState, action: ActionDef | None) -> None:
    draw_frame(rect, Color(16, 18, 24, 255), Color(76, 82, 96, 220))
    title_style = ui_text_style("subtitle")
    label_style = ui_text_style("body")
    amount_style = ui_text_style("body", "accent")
    draw_text(font, "物品", int(rect.x) + 14, int(rect.y) + 10, title_style.size, title_style.color)
    slots = _inventory_slots(state)
    columns = max(1, math.ceil(len(slots) / 2))
    rows = max(1, math.ceil(len(slots) / columns))
    cell_w = (rect.width - 16 - (columns - 1) * 8) / columns
    cell_h = min(44.0, (rect.height - 52 - (rows - 1) * 8) / rows)
    for index, (kind, key, label, amount) in enumerate(slots):
        col = index % columns
        row = index // columns
        cell = Rectangle(rect.x + 8 + col * (cell_w + 8), rect.y + 42 + row * (cell_h + 8), cell_w, cell_h)
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
            select_item_input(state, key)
        draw_text(font, label, int(cell.x) + 8, int(cell.y) + 6, label_style.size, label_style.color if not disabled else ui_text_color("disabled"))
        draw_text(font, str(amount), int(cell.x) + 8, int(cell.y) + 24, amount_style.size, amount_style.color if not disabled else ui_text_color("disabled"))


def _inventory_slots(state: GameState) -> list[tuple[str, str, str, int]]:
    slots: list[tuple[str, str, str, int]] = [
        ("item", "money", ITEM_LABELS["money"], state.world.inventory.get("money", 0)),
        ("item", "cigarettes", ITEM_LABELS["cigarettes"], state.world.inventory.get("cigarettes", 0)),
    ]
    preferred_items = ("clothes", "hotel_pass", "car_key", "repair_case_item", "gun")
    seen: set[str] = {"money", "cigarettes"}
    for key in preferred_items:
        amount = state.world.inventory.get(key, 0)
        if amount > 0 or key in ITEM_LABELS:
            slots.append(("item", key, ITEM_LABELS.get(key, key), amount))
            seen.add(key)
    for key, amount in sorted(state.world.inventory.items()):
        if key in seen:
            continue
        slots.append(("item", key, ITEM_LABELS.get(key, key), amount))
    return slots


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
        label_style = ui_text_style("body", scale=scale, minimum_size=10)
        draw_text(font, label, int(cell.x + 10 * scale), int(cell.y + 4 * scale), label_style.size, label_style.color)
        x += cell_w


def draw_message_feed(font: Font | None, rect: Rectangle, state: GameState) -> None:
    draw_frame(rect, Color(16, 18, 24, 232), Color(78, 84, 96, 210))
    feed_title_style = ui_text_style("subtitle", scale=(20 / 24))
    section_style = ui_text_style("body_sm", "accent")
    body_style = ui_text_style("body_sm", "muted")
    faint_style = ui_text_style("body_sm", "subtle")
    draw_text(font, "消息", int(rect.x) + 12, int(rect.y) + 10, feed_title_style.size, feed_title_style.color)
    inner_x = int(rect.x) + 12
    inner_w = int(rect.width) - 24
    y = int(rect.y) + 40
    if state.last_resolution is not None:
        draw_text(font, "最近判定", inner_x, y, section_style.size, section_style.color)
        y += 18
        meta = ""
        if state.last_resolution.value is not None:
            meta = f"值 {state.last_resolution.value}"
        if meta:
            draw_text(font, meta, inner_x, y, body_style.size, ui_text_color("accent"))
            y += 18
        for line in wrap_text_lines(font, state.last_resolution.text, inner_w, body_style.size):
            draw_text(font, line, inner_x, y, body_style.size, body_style.color)
            y += body_style.line_height - 2
        y += 10
        draw_rectangle_rec(Rectangle(rect.x + 12, y, rect.width - 24, 1), Color(70, 74, 84, 180))
        y += 14
    draw_text(font, "行动记录", inner_x, y, section_style.size, section_style.color)
    y += 20
    entries = list(reversed(state.action_log[-6:]))
    if not entries:
        draw_text(font, "暂无记录。", inner_x, y, body_style.size, faint_style.color)
        return
    for entry in entries:
        for line in wrap_text_lines(font, f"· {entry}", inner_w, body_style.size):
            draw_text(font, line, inner_x, y, body_style.size, body_style.color)
            y += body_style.line_height - 2
        y += 4
        if y > rect.y + rect.height - 24:
            break


def draw_profile_modal(font: Font | None, state: GameState, growth_defs=GROWTH_DEFS) -> None:
    if state.modal.kind != "profile":
        return
    begin_layer("profile", interactive=True)
    rect = Rectangle(layout().hud.x + layout().hud.width - 500, layout().hud.y + layout().hud.height + 12, 500, 440)
    draw_scrim(Rectangle(0, 0, float(get_screen_width()), float(get_screen_height())))
    draw_frame(rect, Color(16, 18, 24, 250), Color(118, 118, 118, 220))
    title_style = ui_text_style("title")
    stats_style = ui_text_style("body", "accent")
    meta_style = ui_text_style("body", "muted")
    section_style = ui_text_style("body", "accent")
    body_style = ui_text_style("body_sm", "muted")
    faint_style = ui_text_style("body", "subtle")
    draw_text(font, "个人档案", int(rect.x) + 20, int(rect.y) + 18, title_style.size, title_style.color)
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", ui_text_size("body")):
        close_modal(state)
        end_layer("profile")
        return
    header_y = int(rect.y) + 64
    draw_text(font, f"成长点数 {state.growth_points}", int(rect.x) + 20, header_y, stats_style.size, stats_style.color)
    draw_text(font, f"已拥有 {len(state.unlocked_growths)} 项成长", int(rect.x) + 175, header_y, meta_style.size, meta_style.color)

    content_y = int(rect.y) + 96
    content_h = int(rect.height) - 118
    left = Rectangle(rect.x + 20, content_y, 300, content_h)
    right = Rectangle(rect.x + 330, content_y, rect.width - 350, content_h)
    draw_frame(left, Color(18, 20, 26, 240), Color(78, 84, 96, 210))
    draw_frame(right, Color(18, 20, 26, 240), Color(78, 84, 96, 210))
    draw_text(font, "可选成长", int(left.x) + 12, int(left.y) + 10, section_style.size, section_style.color)
    draw_text(font, "已拥有成长", int(right.x) + 12, int(right.y) + 10, section_style.size, section_style.color)

    choice_y = int(left.y) + 38
    if state.pending_growth_choices:
        for growth_id in state.pending_growth_choices:
            growth = growth_defs[growth_id]
            can_claim = state.growth_points > 0
            card_rect = Rectangle(left.x + 10, choice_y, left.width - 20, 92)
            draw_frame(card_rect, Color(24, 27, 34, 255), Color(92, 96, 104, 220) if can_claim else Color(70, 72, 78, 180))
            draw_text(font, growth.title, int(card_rect.x) + 12, int(card_rect.y) + 10, section_style.size, section_style.color if can_claim else ui_text_color("disabled"))
            body_lines = wrap_text_lines_any(font, growth.description, card_rect.width - 24, body_style.size)
            body_y = int(card_rect.y) + 34
            for line in body_lines[:2]:
                draw_text(font, line, int(card_rect.x) + 12, body_y, body_style.size, body_style.color)
                body_y += body_style.line_height - 2
            button_label = "解锁" if can_claim else "点数不足"
            if text_button(font, Rectangle(card_rect.x + card_rect.width - 92, card_rect.y + card_rect.height - 28, 80, 20), button_label, ui_text_size("body_sm"), disabled=not can_claim):
                claim_growth(state, growth_id)
                end_layer("profile")
                return
            choice_y += 102
    else:
        draw_text(font, "当前没有新的成长可选。", int(left.x) + 12, choice_y + 6, meta_style.size, faint_style.color)

    owned_y = int(right.y) + 40
    if state.unlocked_growths:
        for growth_id in sorted(state.unlocked_growths):
            growth = growth_defs[growth_id]
            draw_text(font, f"· {growth.title}", int(right.x) + 12, owned_y, meta_style.size, meta_style.color)
            owned_y += 24
    else:
        draw_text(font, "暂无已拥有成长。", int(right.x) + 12, owned_y + 6, meta_style.size, faint_style.color)
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
    title_style = ui_text_style("title")
    summary_style = ui_text_style("body", "accent")
    draw_text(font, title, int(rect.x) + 20, int(rect.y) + 18, title_style.size, title_style.color)
    trauma_count = pile.count("trauma")
    draw_text(font, f"共 {len(pile)} 张    创伤 {trauma_count} 张", int(rect.x) + 20, int(rect.y) + 54, summary_style.size, summary_style.color)
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", ui_text_size("body")):
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
    title_style = ui_text_style("title")
    body_style = ui_text_style("body", "muted")
    draw_text(font, state.active_dialogue.title, int(rect.x) + 24, int(rect.y) + 18, title_style.size, title_style.color)
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", ui_text_size("body")):
        finish_dialogue(state)
        end_layer("dialogue_modal")
        return
    history_rect = Rectangle(rect.x + 24, rect.y + 64, rect.width - 48, rect.height - 180)
    line_height = body_style.line_height
    block_gap = 12
    rendered_lines: list[tuple[str, bool]] = []
    for block in state.active_dialogue.history:
        for line in wrap_text_lines_any(font, block, history_rect.width, body_style.size):
            rendered_lines.append((line, False))
        rendered_lines.append(("", True))
    if rendered_lines and rendered_lines[-1][1]:
        rendered_lines.pop()
    max_visible_lines = max(1, int((history_rect.height + block_gap) // line_height))
    max_scroll = max(0, len(rendered_lines) - max_visible_lines)
    if check_collision_point_rec(mouse_point(), history_rect):
        wheel = int(get_mouse_wheel_move())
        if wheel != 0:
            state.active_dialogue.history_scroll = max(
                0,
                min(max_scroll, state.active_dialogue.history_scroll - wheel * 3),
            )
    scroll = max(0, min(max_scroll, state.active_dialogue.history_scroll))
    state.active_dialogue.history_scroll = scroll
    start = max(0, len(rendered_lines) - max_visible_lines - scroll)
    visible_lines = rendered_lines[start : start + max_visible_lines]
    y = int(history_rect.y)
    for line, spacer in visible_lines:
        if spacer:
            y += block_gap
            continue
        draw_text(font, line, int(history_rect.x), y, body_style.size, body_style.color)
        y += line_height
    button_y = rect.y + rect.height - 76
    if state.active_dialogue.choices:
        x = rect.x + 24
        for index, choice in enumerate(state.active_dialogue.choices):
            button = Rectangle(x, button_y, rect.width - 48, 36)
            if text_button(font, button, choice, ui_text_size("body")):
                choose_dialogue_option(state, index)
                end_layer("dialogue_modal")
                return
            button_y += 44
    elif state.active_dialogue.finished:
        if text_button(font, Rectangle(rect.x + rect.width - 118, rect.y + rect.height - 48, 94, 30), "结束", ui_text_size("body")):
            finish_dialogue(state)
            end_layer("dialogue_modal")
            return
    else:
        if text_button(font, Rectangle(rect.x + rect.width - 118, rect.y + rect.height - 48, 94, 30), "继续", ui_text_size("body")):
            continue_dialogue(state)
            end_layer("dialogue_modal")
            return
    end_layer("dialogue_modal")


def _hud_block(font: Font | None, rect: Rectangle, label: str, value: str, color: Color) -> None:
    label_style = ui_text_style("body_sm", "subtle")
    value_style = ui_text_style("subtitle", color=color)
    draw_text(font, label, int(rect.x), int(rect.y), label_style.size, label_style.color)
    draw_text(font, value, int(rect.x), int(rect.y) + 16, value_style.size, value_style.color)


def _hud_meter(font: Font | None, rect: Rectangle, label: str, value: int, maximum: int, fill: Color, track: Color) -> None:
    label_style = ui_text_style("body", "subtle")
    value_style = ui_text_style("body", color=fill)
    draw_text(font, label, int(rect.x), int(rect.y), label_style.size, label_style.color)
    bar = Rectangle(rect.x, rect.y + 18, rect.width, 12)
    draw_frame(bar, Color(18, 20, 24, 255), Color(74, 78, 90, 220))
    inner = Rectangle(bar.x + 2, bar.y + 2, max(0, bar.width - 4), max(0, bar.height - 4))
    draw_rectangle_rec(inner, track)
    segments = max(1, maximum)
    gap = 2.0
    seg_w = max(3.0, (inner.width - gap * (segments - 1)) / segments)
    for index in range(segments):
        seg_x = inner.x + index * (seg_w + gap)
        seg = Rectangle(seg_x, inner.y, seg_w, inner.height)
        draw_rectangle_rec(seg, fill if index < value else track)
    draw_text(font, f"{value}/{maximum}", int(rect.x + rect.width + 10), int(rect.y + 11), value_style.size, value_style.color)


def _find_requirement(action: ActionDef | None, kind: str, key: str) -> InputRequirement | None:
    if action is None:
        return None
    for requirement in action.inputs:
        if requirement.kind == kind and requirement.key == key:
            return requirement
    return None
