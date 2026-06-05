from __future__ import annotations

import math

from pyray import *  # type: ignore

from sincity.constants import MAX_LOG_LINES
from sincity.content import ACTOR_STATUS_DEFS, CARD_DEFS, GROWTH_DEFS
from sincity.labels import ITEM_LABELS
from sincity.model.defs import ActionDef, InputRequirement
from sincity.model.enums import ResultType, SUIT_LABELS, ScreenName
from sincity.model.state import GameState
from sincity.rendering import draw_text
from sincity.rules.progression import pressure_recovery_threshold
from sincity.rules.deck import list_all_spirit_slots, list_spirit_slots
from sincity.rules.rng import RandomSource
from sincity.rules import (
    card_hint_flash_active,
    can_endure_pressure_during_encounter,
    card_matches_action_check,
    claim_growth,
    close_modal,
    count_spirit_cards,
    current_world_snapshot,
    encounter_action_cards,
    endure_pressure_during_encounter,
    advance_cycle,
    open_modal,
    requirement_is_slotted,
    clear_selected_input,
    select_card_input,
    select_item_input,
    slot_current_value,
    slot_effective_value,
    slot_is_available,
    slot_is_exhausted,
    slot_is_locked,
    slot_trauma_count,
    party_actor,
)

from sincity.rules.notifications import push_notification

from .dialogue_view import draw_dialogue_overlay
from .input_regions import profile_panel_rect
from .task_panel import draw_task_panel
from .ui_core import Z_HAND, Z_HUD, Z_PROFILE_MODAL, begin_layer, clickable, draw_frame, draw_scrim, end_layer, layout, measure_text_width, mouse_point, pointer_pressed, text_button, wrap_text_lines, wrap_text_lines_any
from .ui_text import ui_text_color, ui_text_size, ui_text_style

INVENTORY_PANEL_WIDTH = 324
INVENTORY_PANEL_RIGHT_OFFSET = 336
INVENTORY_PADDING_X = 8.0
INVENTORY_HEADER_HEIGHT = 42.0
INVENTORY_GAP_X = 8.0
INVENTORY_GAP_Y = 8.0
INVENTORY_ITEM_ASPECT = 150.0 / 106.0


def draw_hud(font: Font | None, state: GameState) -> None:
    begin_layer("hud", z=Z_HUD)
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
        "精力",
        state.attributes.energy,
        state.attributes.max_energy,
        Color(208, 182, 108, 255),
        Color(78, 66, 34, 255),
    )
    day_style = ui_text_style("body", "muted")
    relation_text = (
        f"黑帮 {state.world.values.get('gang_relation', 0)}  "
        f"财阀 {state.world.values.get('finance_relation', 0)}  "
        f"警察 {state.world.values.get('police_relation', 0)}"
    )
    draw_text(font, relation_text, int(hud.x + 392), int(hud.y + 17), day_style.size, day_style.color)
    if state.companion_actor_ids:
        companion_text = "同行 " + "、".join(_companion_hud_label(state, actor_id) for actor_id in state.companion_actor_ids)
        companion_x = int(hud.x + 660)
        draw_text(font, companion_text, companion_x, int(hud.y + 17), day_style.size, ui_text_color("accent"))
    draw_text(font, f"第 {state.day} 天", int(hud.x + hud.width - 248), int(hud.y + 17), day_style.size, day_style.color)
    if text_button(font, Rectangle(hud.x + hud.width - 148, hud.y + 10, 120, 34), f"档案 {state.growth_points}", ui_text_size("body")):
        if state.modal.kind == "profile":
            close_modal(state)
        else:
            open_modal(state, "profile")
    end_layer("hud")


def draw_hand(font: Font | None, state: GameState, action: ActionDef | None = None, rng: RandomSource | None = None) -> None:
    hand = layout().hand
    draw_frame(hand, Color(18, 20, 26, 250))
    hand_title_style = ui_text_style("subtitle")
    subtitle_style = ui_text_style("body", "muted")
    draw_text(font, "侦探社", int(hand.x) + 18, int(hand.y) + 14, hand_title_style.size, hand_title_style.color)
    encounter_cards = encounter_action_cards(state)
    cards_exhausted = False
    if encounter_cards is not None:
        current, cap = encounter_cards
        cards_exhausted = current <= 0
        energy_style = ui_text_style("subtitle", "danger" if cards_exhausted else "accent", scale=0.8, minimum_size=18)
        energy_label = f"可用 {current}/{cap}"
        energy_x = int(hand.x) + 166
        draw_text(font, energy_label, energy_x, int(hand.y) + 14, energy_style.size, energy_style.color)
        detail = "行动只需要可用行动卡；执行后消耗这张卡。"
        detail_style = ui_text_style("body", "danger" if cards_exhausted else "muted")
        detail_x = energy_x + int(measure_text_width(font, energy_label, energy_style.size)) + 10
        draw_text(font, detail, detail_x, int(hand.y) + 17, detail_style.size, detail_style.color)
        pressure_rect = Rectangle(hand.x + hand.width - INVENTORY_PANEL_RIGHT_OFFSET - 198, hand.y + 12, 84, 30)
        rest_rect = Rectangle(hand.x + hand.width - INVENTORY_PANEL_RIGHT_OFFSET - 104, hand.y + 12, 84, 30)
        action_locked = state.active_dialogue is not None or state.pending_resolution is not None
        pressure_disabled = action_locked or not can_endure_pressure_during_encounter(state)
        if text_button(font, pressure_rect, "承压", ui_text_size("body"), disabled=pressure_disabled):
            endure_pressure_during_encounter(state, rng if rng is not None else RandomSource(state.seed))
        rest_disabled = action_locked
        if text_button(font, rest_rect, "休整", ui_text_size("body"), disabled=rest_disabled):
            advance_cycle(state, rng if rng is not None else RandomSource(state.seed))
    else:
        subtitle = "灰掉表示今天已经使用。行动卡本身无属性，点数受健康影响。"
        draw_text(font, subtitle, int(hand.x) + 166, int(hand.y) + 17, subtitle_style.size, subtitle_style.color)
        rest_rect = Rectangle(hand.x + hand.width - INVENTORY_PANEL_RIGHT_OFFSET - 104, hand.y + 12, 84, 30)
        if text_button(font, rest_rect, "休整", ui_text_size("body")):
            snapshot = current_world_snapshot(state)
            for loc_id, loc in snapshot.locations_by_id.items():
                if loc.title == "办公室":
                    open_modal(state, "location", loc_id)
                    break
    x = int(hand.x) + 18
    y = int(hand.y) + 50
    cards_right_limit = _inventory_panel_rect().x - 12
    clicked_exhausted_card = False
    current_owner = ""
    group_start_x = x
    represented_owners: set[str] = set()
    for slot_index, slot_id in enumerate(list_all_spirit_slots(state.deck)):
        owner_id = slot_id.split(":", 1)[0]
        represented_owners.add(owner_id)
        if owner_id != current_owner:
            _draw_actor_name_bar(font, state, current_owner, group_start_x, y)
            current_owner = owner_id
            if slot_index > 0:
                x += 24
                group_start_x = x
            y = int(hand.y) + 50
        rect = Rectangle(x, y, 150, 106)
        if rect.x + rect.width > cards_right_limit:
            break
        locked = slot_is_locked(state, slot_id)
        actor = party_actor(state, owner_id)
        actor_exhausted = False
        disabled = locked or cards_exhausted or actor_exhausted or slot_is_exhausted(state, slot_id) or not slot_is_available(state, slot_id)
        if disabled and state.selected_input.kind == "card" and state.selected_input.index == slot_index:
            clear_selected_input(state)
        selected = (state.selected_input.kind == "card" and state.selected_input.index == slot_index) and not disabled
        slotted = (state.assembly.slotted_card_index == slot_index) and not disabled
        hinted = (not disabled) and card_hint_flash_active(state, action) and card_matches_action_check(action, slot_id)
        if cards_exhausted and pointer_pressed(rect, z=Z_HAND):
            clicked_exhausted_card = True
        if locked:
            _draw_locked_slot(font, rect, "健康不足", "行动槽位已锁定")
        elif actor_exhausted:
            _draw_locked_slot(font, rect, "精力不足", f"{actor.name} 不能行动")
        elif draw_compact_card(
            font,
            rect,
            slot_id,
            selected or slotted,
            interactive=(not cards_exhausted) and slot_is_available(state, slot_id) and not disabled,
            hinted=hinted,
            disabled=disabled,
            no_energy=cards_exhausted,
            state=state,
            action=action,
        ):
            select_card_input(state, slot_id, slot_index)
        x += 162
    _draw_actor_name_bar(font, state, current_owner, group_start_x, y)
    if state.active_encounter is None:
        x = _draw_absent_companion_status_cards(font, state, x, y, cards_right_limit, represented_owners)
    if clicked_exhausted_card:
        state.action_log.append("行动卡已耗尽：休息后会抽取新的行动卡。")
        del state.action_log[:-MAX_LOG_LINES]
        push_notification(state, "warning", "行动卡已耗尽", "休息后会抽取新的行动卡。")
    inventory_rect = _inventory_panel_rect()
    draw_inventory_panel(font, inventory_rect, state, action)


def _draw_absent_companion_status_cards(font: Font | None, state: GameState, x: float, y: float, cards_right_limit: float, represented_owners: set[str]) -> float:
    for actor_id in state.companion_actor_ids:
        if actor_id in represented_owners:
            continue
        actor = party_actor(state, actor_id)
        rect = Rectangle(x + 24, y, 150, 106)
        if rect.x + rect.width > cards_right_limit:
            break
        _draw_companion_status_slot(font, rect, actor)
        _draw_actor_name_bar(font, state, actor_id, rect.x, y)
        x = rect.x + 162
    return x


def _draw_companion_status_slot(font: Font | None, rect: Rectangle, actor) -> None:
    location = _stress_location_label(actor.stress_location)
    if actor.pressure_locked and location:
        title = "暂离行动"
        subtitle = f"在{location}"
    elif actor.pressure_locked:
        title = "暂离行动"
        subtitle = "压力过高"
    else:
        title = "暂无行动"
        subtitle = "不能行动"
    _draw_locked_slot(font, rect, title, subtitle)


def _draw_locked_slot(font: Font | None, rect: Rectangle, title: str, subtitle: str) -> None:
    fill = Color(20, 22, 28, 255)
    border = Color(60, 64, 74, 180)
    draw_frame(rect, fill, border)
    draw_scrim(rect)
    title_style = ui_text_style("body", "disabled")
    draw_text(font, title, int(rect.x) + 12, int(rect.y) + 12, title_style.size, title_style.color)
    sub_style = ui_text_style("body_sm", "disabled")
    draw_text(font, subtitle, int(rect.x) + 12, int(rect.y) + 68, sub_style.size, sub_style.color)


def _draw_actor_name_bar(font: Font | None, state: GameState, owner_id: str, group_start_x: float, card_y: float) -> None:
    if not owner_id:
        return
    actor = state.party.get(owner_id)
    if actor is None:
        return
    bar_y = card_y + 106 + 4
    name_style = ui_text_style("body_sm", "accent" if actor.is_player else "muted")
    label = actor.name if actor.is_player else f"同伴 · {actor.name}"
    draw_text(font, label, int(group_start_x), int(bar_y), name_style.size, name_style.color)
    label_w = measure_text_width(font, label, name_style.size)
    segments = actor.max_pressure
    chip_size = 10
    spacing = chip_size + 4
    start_x = int(group_start_x) + int(label_w) + 10
    max_seg_x = int(layout().hand.x + layout().hand.width - INVENTORY_PANEL_RIGHT_OFFSET - 12)
    shown = min(segments, max(1, (max_seg_x - start_x) // spacing))
    fill_color = Color(180, 72, 52, 220)
    empty_color = Color(50, 50, 55, 200)
    border_color = Color(80, 80, 90, 180)
    threshold = pressure_recovery_threshold(actor)
    for index in range(shown):
        cell = Rectangle(start_x + index * spacing, bar_y + 2, chip_size, chip_size)
        if index < actor.pressure:
            draw_rectangle_rounded(cell, 0.25, 4, fill_color)
        else:
            draw_rectangle_rounded(cell, 0.25, 4, empty_color)
        draw_rectangle_rounded_lines_ex(cell, 0.25, 4, 1.0, border_color)
        if index == threshold:
            draw_line(int(cell.x - 1), int(cell.y - 2), int(cell.x - 1), int(cell.y + cell.height + 2), Color(200, 200, 120, 180))
    value_x = start_x + shown * spacing + 4
    value_text = f"{actor.pressure}/{actor.max_pressure}"
    if actor.pressure_locked:
        location = _stress_location_label(actor.stress_location)
        value_text += f" {location}" if location else " 锁"
        value_style = ui_text_style("body_sm", "danger")
    else:
        value_style = ui_text_style("body_sm", "muted")
    draw_text(font, value_text, value_x, int(bar_y), value_style.size, value_style.color)


def draw_compact_card(
    font: Font | None,
    rect: Rectangle,
    card_id: str,
    selected: bool,
    interactive: bool = True,
    *,
    hinted: bool = False,
    disabled: bool | None = None,
    no_energy: bool = False,
    state: GameState | None = None,
    action: ActionDef | None = None,
) -> bool:
    owner_id = card_id.split(":", 1)[0]
    owner_name = party_actor(state, owner_id).name if state is not None else owner_id
    owner_is_player = party_actor(state, owner_id).is_player if state is not None else owner_id == "cole"
    boosted = state is not None and state.deck.action_card_bonuses.get(card_id, 0) > 0
    if disabled is None:
        disabled = state is not None and (slot_is_exhausted(state, card_id) or not slot_is_available(state, card_id))
    hinted = hinted and not disabled
    selected = selected and not disabled
    fill = Color(20, 22, 28, 255) if disabled else Color(29, 33, 40, 255)
    border = Color(72, 76, 88, 180) if disabled else Color(95, 99, 107, 220)
    if selected:
        border = Color(201, 165, 88, 255)
    elif boosted:
        border = Color(214, 184, 96, 245)
    elif hinted:
        border = Color(230, 206, 126, 255)
    clicked = clickable(rect) if (interactive and not disabled) else False
    draw_frame(rect, fill, border)
    if not disabled and not owner_is_player:
        _draw_actor_card_tint(rect, _actor_theme_color(owner_id))
    if hinted and not selected:
        draw_rectangle_rounded_lines_ex(rect, 0.03, 8, 2.0, Color(230, 206, 126, 190))
    if disabled:
        draw_scrim(rect)
    _draw_hand_card_head(font, rect, owner_name, card_id=card_id, state=state, disabled=disabled)
    _draw_hand_card_suit(font, rect, owner_name, card_id=card_id, state=state, action=action, disabled=disabled, no_energy=no_energy)
    return clicked


def _draw_hand_card_head(font: Font | None, rect: Rectangle, name: str, *, card_id: str, state: GameState | None, disabled: bool) -> None:
    number_text = str(slot_current_value(state, card_id) if state is not None else 0)
    trauma = slot_trauma_count(state, card_id) if state is not None else 0
    bonus = state.deck.action_card_bonuses.get(card_id, 0) if state is not None else 0
    penalty = state.deck.action_card_penalties.get(card_id, 0) if state is not None else 0
    card_label = state.deck.action_card_labels.get(card_id, "") if state is not None else ""
    number_style = ui_text_style("title", "disabled" if disabled else ("warning" if trauma or penalty < 0 else "accent"))
    suffix_style = ui_text_style("body", "disabled" if disabled else "muted")
    text_size = max(28, number_style.size - 2)
    suffix_size = suffix_style.size
    x = int(rect.x) + 12
    y = int(rect.y) + 12
    draw_text(font, number_text, x, y, text_size, number_style.color)
    name_x = x + int(measure_text_width(font, number_text, text_size)) + 8
    owner_id = card_id.split(":", 1)[0]
    owner_is_player = state is None or party_actor(state, owner_id).is_player
    if not owner_is_player and not disabled:
        _draw_actor_name_chip(font, Rectangle(name_x, y + 1, rect.width - (name_x - rect.x) - 14, 22), name, _actor_theme_color(owner_id), suffix_size)
    else:
        draw_text(font, name, name_x, y + 1, suffix_size, suffix_style.color)
    if bonus > 0 and not disabled:
        bonus_rect = Rectangle(rect.x + rect.width - 48, rect.y + 10, 34, 20)
        draw_frame(bonus_rect, Color(84, 68, 46, 255), Color(214, 184, 96, 245))
        bonus_style = ui_text_style("caption", "accent")
        draw_text(font, f"+{bonus}", int(bonus_rect.x) + 8, int(bonus_rect.y) + 3, bonus_style.size, bonus_style.color)
    if penalty < 0 and card_label and not disabled:
        label_style = ui_text_style("body_sm", "warning")
        draw_text(font, f"{card_label} {penalty}", x, y + 34, label_style.size, label_style.color)
    if trauma and not disabled:
        trauma_style = ui_text_style("body_sm", "warning")
        trauma_y = y + (52 if penalty < 0 and card_label else 34)
        draw_text(font, f"创伤 {trauma}", x, trauma_y, trauma_style.size, trauma_style.color)


def _actor_theme_color(actor_id: str) -> Color:
    if actor_id == "lena":
        return Color(70, 142, 190, 255)
    if actor_id == "marco":
        return Color(122, 106, 190, 255)
    return Color(140, 146, 158, 255)


def _draw_actor_card_tint(rect: Rectangle, color: Color) -> None:
    draw_rectangle_rec(
        Rectangle(rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4),
        Color(color.r, color.g, color.b, 24),
    )
    draw_rectangle_rec(
        Rectangle(rect.x + 2, rect.y + 2, 8, rect.height - 4),
        Color(color.r, color.g, color.b, 96),
    )


def _draw_actor_name_chip(font: Font | None, rect: Rectangle, name: str, color: Color, size: int) -> None:
    padding_x = 8
    chip_w = min(rect.width, measure_text_width(font, name, size) + padding_x * 2)
    chip = Rectangle(rect.x, rect.y, chip_w, 20)
    draw_rectangle_rec(chip, Color(color.r, color.g, color.b, 96))
    draw_text(font, name, int(chip.x + padding_x), int(chip.y + 2), size, ui_text_color("default"))


def _draw_hand_card_suit(
    font: Font | None,
    rect: Rectangle,
    owner_name: str,
    *,
    card_id: str,
    state: GameState | None,
    action: ActionDef | None,
    disabled: bool,
    no_energy: bool,
) -> None:
    suit_label = owner_name
    if action is not None and action.check is not None and state is not None:
        effective = slot_effective_value(state, card_id, action.check)
        if slot_is_exhausted(state, card_id):
            suit_label = "已使用"
        elif no_energy:
            suit_label = "精力不足"
        elif disabled:
            suit_label = "不可用"
        else:
            suit_label = f"预览：状态档 {effective}"
    elif disabled:
        suit_label = f"{suit_label}  不可用"
    suit_style = ui_text_style("body", "subtle" if disabled else "muted")
    draw_text(font, suit_label, int(rect.x) + 12, int(rect.y) + 68, suit_style.size, suit_style.color)


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
        y = int(hand.y) + 50
        cards_right_limit = _inventory_panel_rect().x - 12
        current_owner = ""
        for index, card_id in enumerate(list_all_spirit_slots(state.deck)):
            owner_id = card_id.split(":", 1)[0]
            if owner_id != current_owner:
                current_owner = owner_id
                if index > 0:
                    x += 24
                    y = int(hand.y) + 50
                y += 20
            rect = Rectangle(x, y, 150, 106)
            if rect.x + rect.width > cards_right_limit:
                return
            if index == state.selected_input.index:
                if not slot_is_available(state, card_id) or slot_is_locked(state, card_id):
                    return
                _draw_selected_card_curve(rect)
                return
            x += 162
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
    return _inventory_item_rects(inventory_rect, len(slots))[match_index]


def _inventory_panel_rect() -> Rectangle:
    hand = layout().hand
    return Rectangle(hand.x + hand.width - INVENTORY_PANEL_RIGHT_OFFSET, hand.y + 10, INVENTORY_PANEL_WIDTH, hand.height - 20)


def draw_inventory_panel(font: Font | None, rect: Rectangle, state: GameState, action: ActionDef | None) -> None:
    draw_frame(rect, Color(16, 18, 24, 255), Color(76, 82, 96, 220))
    title_style = ui_text_style("subtitle")
    draw_text(font, "物品", int(rect.x) + 14, int(rect.y) + 10, title_style.size, title_style.color)
    slots = _inventory_slots(state)
    item_rects = _inventory_item_rects(rect, len(slots))
    for (kind, key, label, amount), cell in zip(slots, item_rects):
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
        scale = max(0.55, min(1.0, cell.height / 44.0))
        label_style = ui_text_style("body", scale=scale, minimum_size=10)
        amount_style = ui_text_style("body", "accent", scale=scale, minimum_size=10)
        text_x = int(cell.x + 8.0 * scale)
        draw_text(font, _fit_inventory_label(font, label, cell.width - 16.0 * scale, label_style.size), text_x, int(cell.y + 6.0 * scale), label_style.size, label_style.color if not disabled else ui_text_color("disabled"))
        draw_text(font, str(amount), text_x, int(cell.y + cell.height - (amount_style.line_height + 3.0 * scale)), amount_style.size, amount_style.color if not disabled else ui_text_color("disabled"))


def _inventory_item_rects(rect: Rectangle, count: int) -> list[Rectangle]:
    if count <= 0:
        return []
    content_x = rect.x + INVENTORY_PADDING_X
    content_y = rect.y + INVENTORY_HEADER_HEIGHT
    content_w = rect.width - INVENTORY_PADDING_X * 2
    content_h = max(1.0, rect.height - INVENTORY_HEADER_HEIGHT - 10.0)
    cell_h = _inventory_cell_height(content_w, content_h, count)
    cell_w = min(content_w, cell_h * INVENTORY_ITEM_ASPECT)
    columns = max(1, int((content_w + INVENTORY_GAP_X) // (cell_w + INVENTORY_GAP_X)))
    rows = max(1, math.ceil(count / columns))
    block_h = rows * cell_h + (rows - 1) * INVENTORY_GAP_Y
    y0 = content_y + max(0.0, (content_h - block_h) * 0.5)
    rects: list[Rectangle] = []
    for index in range(count):
        col = index % columns
        row = index // columns
        rects.append(Rectangle(content_x + col * (cell_w + INVENTORY_GAP_X), y0 + row * (cell_h + INVENTORY_GAP_Y), cell_w, cell_h))
    return rects


def _inventory_cell_height(content_w: float, content_h: float, count: int) -> float:
    height = content_h
    while height > 12.0:
        width = min(content_w, height * INVENTORY_ITEM_ASPECT)
        columns = max(1, int((content_w + INVENTORY_GAP_X) // (width + INVENTORY_GAP_X)))
        rows = math.ceil(count / columns)
        if rows * height + (rows - 1) * INVENTORY_GAP_Y <= content_h:
            return height
        height *= 0.5
    width = max(1.0, 12.0 * INVENTORY_ITEM_ASPECT)
    columns = max(1, int((content_w + INVENTORY_GAP_X) // (width + INVENTORY_GAP_X)))
    rows = max(1, math.ceil(count / columns))
    return max(8.0, (content_h - (rows - 1) * INVENTORY_GAP_Y) / rows)


def _fit_inventory_label(font: Font | None, text: str, max_width: float, size: int) -> str:
    if measure_text_width(font, text, size) <= max_width:
        return text
    result = text
    while result and measure_text_width(font, result + "...", size) > max_width:
        result = result[:-1]
    return (result + "...") if result else text[:1]


def _inventory_slots(state: GameState) -> list[tuple[str, str, str, int]]:
    slots: list[tuple[str, str, str, int]] = []
    for key in sorted(state.world.seen_items):
        amount = state.world.inventory.get(key, 0)
        label = ITEM_LABELS.get(key, key)
        slots.append(("item", key, label, amount))
    return slots


def draw_result_strip(font: Font | None, rect: Rectangle, row: tuple[ResultType, ...], scale: float = 1.0) -> None:
    cell_w = (rect.width - 20) / 6.0
    x = rect.x
    for result in row:
        if result == ResultType.FAIL:
            fill, label = Color(124, 66, 66, 255), "坏"
        elif result == ResultType.COST:
            fill, label = Color(144, 126, 70, 255), "中"
        else:
            fill, label = Color(74, 134, 92, 255), "好"
        cell = Rectangle(x, rect.y, cell_w - 4, rect.height)
        draw_frame(cell, fill, Color(22, 22, 22, 180))
        label_style = ui_text_style("body", scale=scale, minimum_size=10)
        draw_text(font, label, int(cell.x + 10 * scale), int(cell.y + 4 * scale), label_style.size, label_style.color)
        x += cell_w


def draw_message_feed(font: Font | None, rect: Rectangle, state: GameState) -> None:
    draw_frame(rect, Color(16, 18, 24, 232), Color(78, 84, 96, 210))
    task_height = min(max(132.0, rect.height * 0.34), max(96.0, rect.height - 156.0))
    task_rect = Rectangle(rect.x, rect.y, rect.width, task_height)
    draw_task_panel(font, task_rect, state)
    separator_y = rect.y + task_height
    draw_rectangle_rec(Rectangle(rect.x + 12, separator_y, rect.width - 24, 1), Color(70, 74, 84, 180))
    log_rect = Rectangle(rect.x, separator_y + 1, rect.width, rect.height - task_height - 1)
    _draw_message_log(font, log_rect, state)


def _draw_message_log(font: Font | None, rect: Rectangle, state: GameState) -> None:
    feed_title_style = ui_text_style("subtitle", scale=(20 / 24))
    section_style = ui_text_style("body_sm", "accent")
    body_style = ui_text_style("body_sm", "muted")
    faint_style = ui_text_style("body_sm", "subtle")
    draw_text(font, "消息", int(rect.x) + 12, int(rect.y) + 10, feed_title_style.size, feed_title_style.color)
    inner_x = int(rect.x) + 12
    inner_w = int(rect.width) - 24
    y = int(rect.y) + 40
    draw_text(font, "行动记录", inner_x, y, section_style.size, section_style.color)
    y += 20
    entries = list(reversed(state.action_log[-6:]))
    if not entries:
        draw_text(font, "暂无记录。", inner_x, y, body_style.size, faint_style.color)
        return
    for i, entry in enumerate(entries):
        if i == 1:
            y += 4
            draw_rectangle_rec(Rectangle(rect.x + 12, y, rect.width - 24, 1), Color(70, 74, 84, 180))
            y += 8
        for line in wrap_text_lines(font, f"· {entry}", inner_w, body_style.size):
            draw_text(font, line, inner_x, y, body_style.size, body_style.color)
            y += body_style.line_height - 2
        y += 4
        if y > rect.y + rect.height - 24:
            break


def draw_profile_modal(font: Font | None, state: GameState, growth_defs=GROWTH_DEFS) -> None:
    if state.modal.kind != "profile":
        return
    begin_layer("profile", z=Z_PROFILE_MODAL)
    rect = profile_panel_rect()
    draw_scrim(Rectangle(0, 0, float(get_screen_width()), float(get_screen_height())))
    draw_frame(rect, Color(16, 18, 24, 250), Color(118, 118, 118, 220))
    title_style = ui_text_style("title")
    stats_style = ui_text_style("body", "accent")
    meta_style = ui_text_style("body", "muted")
    section_style = ui_text_style("body", "accent")
    body_style = ui_text_style("body_sm", "muted")
    faint_style = ui_text_style("body", "subtle")
    draw_text(font, "队伍档案", int(rect.x) + 20, int(rect.y) + 18, title_style.size, title_style.color)
    if text_button(font, Rectangle(rect.x + rect.width - 98, rect.y + 18, 70, 28), "关闭", ui_text_size("body")):
        close_modal(state)
        end_layer("profile")
        return
    header_y = int(rect.y) + 64
    draw_text(font, f"成长点数 {state.growth_points}", int(rect.x) + 20, header_y, stats_style.size, stats_style.color)
    draw_text(font, "每完成一个主线或支线任务获得 1 点。", int(rect.x) + 175, header_y, meta_style.size, meta_style.color)

    content_y = int(rect.y) + 96
    content_h = int(rect.height) - 118
    left = Rectangle(rect.x + 20, content_y, 380, content_h)
    right = Rectangle(left.x + left.width + 10, content_y, 210, content_h)
    companions = Rectangle(right.x + right.width + 10, content_y, rect.x + rect.width - (right.x + right.width + 30), content_h)
    draw_frame(left, Color(18, 20, 26, 240), Color(78, 84, 96, 210))
    draw_frame(right, Color(18, 20, 26, 240), Color(78, 84, 96, 210))
    draw_frame(companions, Color(18, 20, 26, 240), Color(78, 84, 96, 210))
    draw_text(font, "成长选项", int(left.x) + 12, int(left.y) + 10, section_style.size, section_style.color)
    draw_text(font, "主角", int(right.x) + 12, int(right.y) + 10, section_style.size, section_style.color)
    draw_text(font, "同伴", int(companions.x) + 12, int(companions.y) + 10, section_style.size, section_style.color)

    counts = count_spirit_cards(state)
    growth_ids = (
        "upgrade_force",
        "upgrade_charm",
        "upgrade_knowledge",
        "upgrade_sense",
    )
    card_gap = 10
    card_w = (left.width - 30) / 2
    card_h = min(104, (left.height - 58 - card_gap * 2) / 3)
    for index, growth_id in enumerate(growth_ids):
        growth = growth_defs[growth_id]
        can_claim = state.growth_points > 0
        unmet_labels = tuple(condition.label for condition in growth.conditions if condition.label)
        if unmet_labels:
            can_claim = False
        col = index % 2
        row = index // 2
        card_rect = Rectangle(left.x + 12 + col * (card_w + card_gap), left.y + 40 + row * (card_h + card_gap), card_w, card_h)
        draw_frame(card_rect, Color(24, 26, 34, 255), Color(60, 63, 72, 220))
        draw_text(font, growth.title, int(card_rect.x) + 8, int(card_rect.y) + 6, body_style.size, body_style.color)
        body_y = int(card_rect.y) + 26
        for line in wrap_text_lines(font, growth.description, int(card_w) - 16, body_style.size):
            draw_text(font, line, int(card_rect.x) + 8, body_y, body_style.size, faint_style.color)
            body_y += body_style.line_height - 2
        if unmet_labels and not can_claim:
            draw_text(font, unmet_labels[0], int(card_rect.x) + 10, int(card_rect.y + card_rect.height) - 24, body_style.size, faint_style.color)
        button_label = "确认" if can_claim else "不可用"
        if text_button(font, Rectangle(card_rect.x + card_rect.width - 76, card_rect.y + card_rect.height - 26, 66, 20), button_label, ui_text_size("body_sm"), disabled=not can_claim):
            claim_growth(state, growth_id)
            end_layer("profile")
            return

    _draw_profile_column(font, right, state, state.player_actor_id, meta_style.size, faint_style)
    _draw_profile_column(font, companions, state, state.companion_actor_ids[0] if state.companion_actor_ids else None, meta_style.size, faint_style)
    end_layer("profile")


def _draw_profile_column(font: Font | None, rect: Rectangle, state: GameState, actor_id: str | None, text_size: int, small_style: dict) -> None:
    if actor_id is None:
        empty_style = ui_text_style("body", "subtle")
        draw_text(font, "暂无同行同伴。", int(rect.x) + 12, int(rect.y) + 42, empty_style.size, empty_style.color)
        return
    y = int(rect.y) + 42
    label_style = ui_text_style("body", "muted")
    actor = party_actor(state, actor_id)
    color = _actor_theme_color(actor_id)
    draw_rectangle_rec(Rectangle(rect.x + 12, y, rect.width - 24, 28), Color(color.r, color.g, color.b, 70))
    draw_text(font, actor.name, int(rect.x) + 22, y + 5, label_style.size, ui_text_color("default"))
    y += 36
    if actor.is_player:
        draw_text(font, f"生命 {actor.health}/{actor.max_health}  精力 {actor.energy}/{actor.max_energy}", int(rect.x) + 16, y, text_size, label_style.color)
    else:
        draw_text(font, f"生命 {actor.health}/{actor.max_health}", int(rect.x) + 16, y, text_size, label_style.color)
    y += 24
    pressure_text = f"压力 {actor.pressure}/{actor.max_pressure}"
    if actor.pressure_locked:
        lock_style = ui_text_style("body", "danger")
        location = _stress_location_label(actor.stress_location)
        suffix = f"  在{location}" if location else " 锁"
        draw_text(font, pressure_text + suffix, int(rect.x) + 16, y, text_size, lock_style.color)
    else:
        draw_text(font, pressure_text, int(rect.x) + 16, y, text_size, label_style.color)
    y += 24
    if actor.statuses:
        status_text = "  ".join(
            f"{ACTOR_STATUS_DEFS.get(status.id).title if ACTOR_STATUS_DEFS.get(status.id) else status.id} {status.cycles}"
            for status in actor.statuses
        )
        draw_text(font, status_text, int(rect.x) + 16, y, text_size, ui_text_style("body", "warning").color)
        y += 24
    for label, key in (("暴力", actor.force), ("魅力", actor.charm), ("知识", actor.knowledge), ("敏锐", actor.sense)):
        draw_text(font, f"{label} {key}", int(rect.x) + 16, y, text_size, label_style.color)
        y += 20


def _companion_hud_label(state: GameState, actor_id: str) -> str:
    actor = state.party[actor_id]
    location = _stress_location_label(actor.stress_location)
    if actor.pressure_locked and location:
        return f"{actor.name}（{location}，压力过高）"
    if actor.pressure_locked:
        return f"{actor.name}（压力过高）"
    return actor.name


def _stress_location_label(location: str) -> str:
    return location


def draw_card_pile_modal(font: Font | None, state: GameState) -> None:
    del font, state


def draw_dialogue_modal(font: Font | None, state: GameState) -> None:
    draw_dialogue_overlay(font, state)


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
