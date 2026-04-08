from __future__ import annotations

from pyray import *  # type: ignore

from raygame.content import GROWTH_DEFS, SCENARIO
from raygame.model.defs import ActionDef, LocationNode
from raygame.model.state import GameState, PendingResolutionState
from raygame.rendering import draw_text
from raygame.rules.judgment import RESULT_TABLE, clamp_action_value
from raygame.rules import (
    clear_assembly,
    clear_selected_input,
    close_modal,
    current_action,
    dismiss_pending_resolution,
    focus_action,
    location_is_visible,
    open_modal,
    open_overlay,
    perform_current_action,
    toggle_action_check_slot,
    toggle_action_requirement_slot,
)
from raygame.screens.city_presenters import (
    ActionSlotModel,
    PresentedActionCard,
    PresentedLocationCard,
    present_action_cards,
    present_child_location_cards,
    present_location_clock_ids,
    present_world_location_cards,
)
from raygame.screens.widgets import (
    begin_layer,
    click_pressed,
    consume_click,
    draw_card_pile_modal,
    draw_clock_row,
    draw_frame,
    draw_hand,
    draw_message_feed,
    draw_note_block,
    draw_profile_modal,
    draw_result_strip,
    draw_scrim,
    draw_slot_chip,
    draw_table_card,
    draw_table_shell,
    end_layer,
    layout,
    pill,
    wrap_text_lines,
)


def draw_city_screen(font: Font | None, state: GameState, rng) -> None:
    if state.pending_resolution is not None and state.pending_resolution.settled and click_pressed():
        dismiss_pending_resolution(state)
        consume_click()
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    if is_key_pressed(KEY_ESCAPE) and not resolving:
        close_modal(state)
    page = layout()
    message_rect = Rectangle(page.stage.x + page.stage.width - 266, page.stage.y + 8, 252, 126)
    table_rect = Rectangle(page.stage.x + 2, page.stage.y + 2, page.stage.width - 4, page.stage.height - 4)
    begin_layer("world", interactive=state.modal.kind == "")
    _draw_world_table(font, state, table_rect)
    end_layer("world")
    if state.modal.kind == "location" and state.modal.primary_id is not None:
        begin_layer("location_table", interactive=True)
        _draw_location_table(font, state, rng)
        end_layer("location_table")
    draw_card_pile_modal(font, state)
    begin_layer("hand", interactive=state.modal.kind in {"", "location"} and not resolving)
    draw_hand(font, state, current_action(state))
    end_layer("hand")
    draw_message_feed(font, message_rect, state)
    draw_profile_modal(font, state, GROWTH_DEFS)


def _draw_world_table(font: Font | None, state: GameState, rect: Rectangle) -> None:
    sections, _ = draw_table_shell(
        font,
        rect,
        title=SCENARIO.title,
        subtitle=f"第 {state.day} 天 | 地点像散在桌面上的卡，你可以从这里一层层翻开它们。",
    )
    draw_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 26), SCENARIO.global_clock_ids, state)
    _draw_world_cards(font, state, sections.content)


def _draw_location_table(font: Font | None, state: GameState, rng) -> None:
    assert state.modal.primary_id is not None
    location = SCENARIO.locations_by_id[state.modal.primary_id]
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    rect = _floating_table_rect()
    draw_scrim(layout().stage)
    sections, closed = draw_table_shell(
        font,
        rect,
        title=location.title,
        subtitle=location.description,
        close_label="关闭",
    )
    if closed and not resolving:
        close_modal(state)
        return
    location_clock_ids = present_location_clock_ids(location.id)
    if location_clock_ids:
        draw_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 26), location_clock_ids, state)

    child_ids = tuple(child.id for child in location.children if location_is_visible(child.id, state))
    if child_ids:
        child_strip = Rectangle(sections.content.x, sections.content.y, sections.content.width, 114)
        _draw_location_grid(font, state, child_strip, present_child_location_cards(state, child_ids), columns=max(1, min(3, len(child_ids))), nested=True)
        action_top = child_strip.y + child_strip.height + 18
    else:
        action_top = sections.content.y

    draw_text(font, "行动卡", int(sections.content.x), int(action_top) - 26, 18, LIGHTGRAY)
    action_area = Rectangle(sections.content.x, action_top, sections.content.width, sections.content.y + sections.content.height - action_top)
    _draw_action_grid(font, state, rng, present_action_cards(state, location), action_area)


def _draw_location_grid(
    font: Font | None,
    state: GameState,
    rect: Rectangle,
    cards: tuple[PresentedLocationCard, ...],
    *,
    columns: int,
    nested: bool = False,
) -> None:
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    card_h = 92
    gap_x = 18
    gap_y = 18
    card_w = (rect.width - gap_x * (columns - 1)) / columns
    for index, presented in enumerate(cards):
        col = index % columns
        row = index // columns
        card = Rectangle(
            rect.x + col * (card_w + gap_x),
            rect.y + row * (card_h + gap_y),
            card_w,
            card_h,
        )
        model = presented.card
        if draw_table_card(font, card, state, model):
            clear_assembly(state)
            clear_selected_input(state)
            if nested:
                open_overlay(state, "location", presented.location_id)
            else:
                open_modal(state, "location", presented.location_id)


def _draw_world_cards(font: Font | None, state: GameState, rect: Rectangle) -> None:
    for presented in present_world_location_cards(state):
        assert presented.location.position is not None
        card = Rectangle(rect.x + presented.location.position[0], rect.y + presented.location.position[1], presented.card.style.width, presented.card.style.height)
        if draw_table_card(font, card, state, presented.card):
            clear_assembly(state)
            clear_selected_input(state)
            open_modal(state, "location", presented.location_id)


def _draw_action_grid(font: Font | None, state: GameState, rng, cards: tuple[PresentedActionCard, ...], rect: Rectangle) -> None:
    if not cards:
        draw_note_block(font, Rectangle(rect.x, rect.y, rect.width, 86), "这里暂时没有可做的事", "换个地方，或者先满足别的条件。")
        return
    card_w = 232.0
    card_h = 224.0
    gap_x = 18
    gap_y = 96
    columns = max(1, min(len(cards), int((rect.width + gap_x) // (card_w + gap_x))))
    for index, presented in enumerate(cards):
        col = index % columns
        row = index // columns
        card = Rectangle(rect.x + col * (card_w + gap_x), rect.y + row * (card_h + gap_y), card_w, card_h)
        _draw_action_card(font, state, presented, card, rng)


def _draw_action_card(font: Font | None, state: GameState, presented: PresentedActionCard, rect: Rectangle, rng) -> None:
    action = presented.action
    pending = state.pending_resolution if state.pending_resolution and state.pending_resolution.resolution.action_id == action.id else None
    draw_table_card(font, rect, state, presented.card)

    slot_y = rect.y + 124
    slot_x = rect.x + 14
    for slot in presented.slots:
        if draw_slot_chip(
            font,
            Rectangle(slot_x, slot_y, rect.width - 28, 28),
            slot.label,
            filled=slot.filled,
            receptive=slot.receptive,
            disabled=slot.disabled,
        ):
            _toggle_presented_slot(state, action, slot)
        slot_y += 34

    if presented.attachment is not None:
        preview_rect = Rectangle(rect.x + 14, rect.y + rect.height - 90, rect.width - 28, 68)
        button_rect = Rectangle(rect.x + 18, rect.y + rect.height + 8, rect.width - 36, 24)
        _draw_action_attachment(font, state, action, presented, preview_rect, button_rect, rng, pending)
    elif presented.card.disabled:
        draw_text(font, "条件未满足或当前资源不足。", int(rect.x) + 14, int(rect.y) + rect.height - 26, 14, Color(132, 132, 132, 255))


def _draw_action_attachment(
    font: Font | None,
    state: GameState,
    action: ActionDef,
    presented: PresentedActionCard,
    rect: Rectangle,
    button_rect: Rectangle,
    rng,
    pending: PendingResolutionState | None,
) -> None:
    draw_frame(rect, Color(18, 20, 26, 255), Color(78, 84, 98, 220))
    if pending is not None:
        _draw_pending_attachment(font, state, rect, button_rect, pending)
        return
    assert presented.attachment is not None
    draw_text(font, presented.attachment.title, int(rect.x) + 10, int(rect.y) + 6, 16, Color(224, 192, 112, 255) if presented.attachment.mode == "preview" and presented.attachment.row else LIGHTGRAY)
    if presented.attachment.row:
        draw_result_strip(font, Rectangle(rect.x + 10, rect.y + 28, rect.width - 20, 20), presented.attachment.row)
    elif presented.attachment.hint:
        draw_text(font, presented.attachment.hint, int(rect.x) + 10, int(rect.y) + 28, 14, LIGHTGRAY)
    if pill(font, Rectangle(button_rect.x, button_rect.y, 78, 22), "收回", False):
        clear_assembly(state)
    if pill(font, Rectangle(button_rect.x + button_rect.width - 78, button_rect.y, 78, 22), "执行", False, disabled=not presented.attachment.can_execute):
        perform_current_action(state, rng)


def _floating_table_rect() -> Rectangle:
    page = layout()
    stage = page.stage
    margin_x = 8.0
    margin_top = 4.0
    margin_bottom = 4.0
    width = min(1040.0, stage.width - margin_x * 2)
    height = min(590.0, stage.height - margin_top - margin_bottom)
    x = stage.x + (stage.width - width) * 0.5
    y = stage.y + margin_top + max(0.0, (stage.height - margin_top - margin_bottom - height) * 0.16)
    return Rectangle(x, y, width, height)


def _draw_pending_attachment(font: Font | None, state: GameState, rect: Rectangle, button_rect: Rectangle, pending: PendingResolutionState) -> None:
    resolution = pending.resolution
    if resolution.result is not None and resolution.value is not None:
        draw_text(font, "判定中", int(rect.x) + 10, int(rect.y) + 6, 16, LIGHTGRAY)
        _draw_inline_resolution_strip(font, Rectangle(rect.x + 10, rect.y + 26, rect.width - 20, 20), pending)
    else:
        draw_text(font, "执行中", int(rect.x) + 10, int(rect.y) + 6, 16, LIGHTGRAY)
    if pending.settled:
        result_rect = _pending_result_rect(font, rect, resolution)
        draw_frame(result_rect, Color(16, 18, 24, 248), Color(78, 84, 98, 220))
        text_width = result_rect.width - 20
        text_y = int(result_rect.y) + 10
        for line in wrap_text_lines(font, resolution.text, text_width, 14):
            draw_text(font, line, int(result_rect.x) + 10, text_y, 14, RAYWHITE)
            text_y += 16
        if resolution.effect_lines:
            for line in wrap_text_lines(font, " | ".join(resolution.effect_lines[:2]), text_width, 13):
                draw_text(font, line, int(result_rect.x) + 10, text_y + 2, 13, Color(212, 196, 132, 255))
                text_y += 15
        continue_rect = Rectangle(result_rect.x + result_rect.width - 88, result_rect.y + result_rect.height + 8, 78, 22)
        if pill(font, continue_rect, "继续", False):
            dismiss_pending_resolution(state)
    else:
        draw_text(font, "结果会在这张卡下面落定。", int(rect.x) + 10, int(rect.y) + 44, 14, LIGHTGRAY)


def _toggle_presented_slot(state: GameState, action: ActionDef, slot: ActionSlotModel) -> None:
    if slot.slot_kind == "check":
        toggle_action_check_slot(state, action)
        return
    if slot.slot_kind == "requirement":
        assert slot.requirement is not None
        toggle_action_requirement_slot(state, action, slot.requirement)
        return
    if state.assembly.action_id == action.id:
        clear_assembly(state)
    else:
        focus_action(state, action.id)


def _draw_inline_resolution_strip(font: Font | None, rect: Rectangle, pending: PendingResolutionState) -> None:
    resolution = pending.resolution
    assert resolution.value is not None
    row = RESULT_TABLE[clamp_action_value(resolution.value)]
    active_index = (resolution.die_roll - 1) if pending.settled and resolution.die_roll is not None else int(pending.progress * 24) % 6
    cell_w = (rect.width - 20) / 6.0
    x = rect.x
    for index, result in enumerate(row):
        if result.value == "fail":
            fill, label = Color(124, 66, 66, 255), "失"
        elif result.value == "cost":
            fill, label = Color(144, 126, 70, 255), "代"
        else:
            fill, label = Color(74, 134, 92, 255), "成"
        cell = Rectangle(x, rect.y, cell_w - 4, rect.height)
        draw_frame(cell, fill, Color(22, 22, 22, 180))
        if index == active_index:
            draw_rectangle_rounded_lines_ex(cell, 0.035, 6, 3.0, Color(233, 216, 152, 255))
        draw_text(font, label, int(cell.x + 10), int(cell.y + 4), 16, RAYWHITE)
        x += cell_w


def _pending_result_rect(font: Font | None, preview_rect: Rectangle, resolution) -> Rectangle:
    text_width = preview_rect.width - 168
    line_count = len(wrap_text_lines(font, resolution.text, text_width, 14))
    if resolution.effect_lines:
        line_count += len(wrap_text_lines(font, " | ".join(resolution.effect_lines[:2]), text_width, 13))
    height = max(46.0, 20.0 + line_count * 16.0)
    return Rectangle(preview_rect.x, preview_rect.y + preview_rect.height + 8, preview_rect.width, height)
