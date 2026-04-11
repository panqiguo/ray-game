from __future__ import annotations

from pyray import *  # type: ignore

from raygame.model.defs import ActionDef
from raygame.model.state import GameState, PendingResolutionState
from raygame.rendering import draw_text
from raygame.rules.judgment import RESULT_TABLE, clamp_action_value
from raygame.rules import (
    clear_assembly,
    clear_selected_input,
    dismiss_pending_resolution,
    focus_action,
    open_modal,
    open_overlay,
    perform_current_action,
    toggle_action_check_slot,
    toggle_action_requirement_slot,
)

from .city_presenters import PresentedWorldObject
from .table_presenters import ActionSlotModel, PresentedActionCard, PresentedLocationCard
from .ui_core import draw_frame, layout, pill, wrap_text_lines
from .ui_cards import draw_table_card
from .ui_panels import draw_result_strip
from .widgets import draw_note_block, draw_scrim, draw_slot_chip, draw_table_shell


MESSAGE_SIDEBAR_GAP = 14.0
MESSAGE_SIDEBAR_WIDTH = 300.0


def split_desktop_area(stage: Rectangle) -> tuple[Rectangle, Rectangle]:
    sidebar_w = min(MESSAGE_SIDEBAR_WIDTH, max(260.0, stage.width * 0.16))
    table_w = stage.width - sidebar_w - MESSAGE_SIDEBAR_GAP - 6.0
    table_rect = Rectangle(stage.x + 2.0, stage.y + 2.0, table_w, stage.height - 4.0)
    message_rect = Rectangle(table_rect.x + table_rect.width + MESSAGE_SIDEBAR_GAP, stage.y + 2.0, sidebar_w, stage.height - 4.0)
    return table_rect, message_rect


def floating_table_rect() -> Rectangle:
    page = layout()
    stage, _ = split_desktop_area(page.stage)
    margin_x = 8.0
    margin_top = 4.0
    margin_bottom = 4.0
    width = min(1040.0, stage.width - margin_x * 2)
    height = min(590.0, stage.height - margin_top - margin_bottom)
    x = stage.x + (stage.width - width) * 0.5
    y = stage.y + margin_top + max(0.0, (stage.height - margin_top - margin_bottom - height) * 0.16)
    return Rectangle(x, y, width, height)


def draw_location_grid(
    font: Font | None,
    state: GameState,
    rect: Rectangle,
    cards: tuple[PresentedLocationCard, ...],
    *,
    columns: int,
    nested: bool = False,
) -> None:
    laid_out = layout_location_cards(rect, cards, columns)
    for presented, (card, scale) in zip(cards, laid_out):
        if draw_table_card(font, card, state, presented.card, scale=scale):
            clear_assembly(state)
            clear_selected_input(state)
            if nested:
                open_overlay(state, "location", presented.location_id)
            else:
                open_modal(state, "location", presented.location_id)


def draw_world_objects(font: Font | None, state: GameState, rng, rect: Rectangle, cards: tuple[PresentedWorldObject, ...]) -> None:
    laid_out = layout_world_objects(rect, cards)
    for presented, (card, scale) in laid_out:
        if presented.kind == "location":
            if draw_table_card(font, card, state, presented.card, scale=scale):
                clear_assembly(state)
                clear_selected_input(state)
                assert presented.location_id is not None
                open_modal(state, "location", presented.location_id)
        else:
            assert presented.action_card is not None
            draw_action_card(font, state, presented.action_card, card, rng, scale=scale)


def draw_action_grid(font: Font | None, state: GameState, rng, cards: tuple[PresentedActionCard, ...], rect: Rectangle) -> None:
    if not cards:
        draw_note_block(font, Rectangle(rect.x, rect.y, rect.width, 86), "这里暂时没有可做的事", "换个地方，或者先满足别的条件。")
        return
    columns = max(1, min(len(cards), int((rect.width + 18.0) // (232.0 + 18.0))))
    laid_out = layout_action_cards(rect, cards, columns)
    for presented, (card, scale) in zip(cards, laid_out):
        draw_action_card(font, state, presented, card, rng, scale=scale)


def draw_location_contents(
    font: Font | None,
    state: GameState,
    rng,
    content_rect: Rectangle,
    child_cards: tuple[PresentedLocationCard, ...],
    action_cards: tuple[PresentedActionCard, ...],
) -> None:
    if child_cards:
        child_strip = Rectangle(content_rect.x, content_rect.y, content_rect.width, 114)
        draw_location_grid(
            font,
            state,
            child_strip,
            child_cards,
            columns=max(1, min(3, len(child_cards))),
            nested=True,
        )
        action_top = child_strip.y + child_strip.height + 18
    else:
        action_top = content_rect.y
    action_area = Rectangle(content_rect.x, action_top, content_rect.width, content_rect.y + content_rect.height - action_top)
    draw_action_grid(font, state, rng, action_cards, action_area)


def draw_action_card(font: Font | None, state: GameState, presented: PresentedActionCard, rect: Rectangle, rng, scale: float = 1.0) -> None:
    action = presented.action
    pending = state.pending_resolution if state.pending_resolution and state.pending_resolution.resolution.action_id == action.id else None
    draw_table_card(font, rect, state, presented.card, scale=scale)

    slot_y = rect.y + 124.0 * scale
    slot_x = rect.x + 14.0 * scale
    for slot in presented.slots:
        if draw_slot_chip(
            font,
            Rectangle(slot_x, slot_y, rect.width - 28.0 * scale, 34.0 * scale),
            slot.label,
            filled=slot.filled,
            receptive=slot.receptive,
            disabled=slot.disabled,
            scale=scale,
        ):
            toggle_presented_slot(state, action, slot)
        slot_y += 40.0 * scale

    if presented.attachment is not None:
        preview_rect = Rectangle(rect.x + 14.0 * scale, rect.y + rect.height - 90.0 * scale, rect.width - 28.0 * scale, 68.0 * scale)
        button_rect = Rectangle(rect.x + 18.0 * scale, rect.y + rect.height + 8.0 * scale, rect.width - 36.0 * scale, 24.0 * scale)
        draw_action_attachment(font, state, action, presented, preview_rect, button_rect, rng, pending, scale=scale)
    elif presented.card.disabled:
        draw_text(font, "条件未满足或当前资源不足。", int(rect.x + 14.0 * scale), int(rect.y + rect.height - 26.0 * scale), max(10, int(round(14 * scale))), Color(132, 132, 132, 255))


def draw_action_attachment(
    font: Font | None,
    state: GameState,
    action: ActionDef,
    presented: PresentedActionCard,
    rect: Rectangle,
    button_rect: Rectangle,
    rng,
    pending: PendingResolutionState | None,
    scale: float = 1.0,
) -> None:
    draw_frame(rect, Color(18, 20, 26, 255), Color(78, 84, 98, 220))
    if pending is not None:
        draw_pending_attachment(font, state, rect, button_rect, pending, scale=scale)
        return
    assert presented.attachment is not None
    draw_text(font, presented.attachment.title, int(rect.x + 10.0 * scale), int(rect.y + 6.0 * scale), max(10, int(round(16 * scale))), Color(224, 192, 112, 255) if presented.attachment.mode == "preview" and presented.attachment.row else LIGHTGRAY)
    if presented.attachment.row:
        draw_result_strip(font, Rectangle(rect.x + 10.0 * scale, rect.y + 28.0 * scale, rect.width - 20.0 * scale, 20.0 * scale), presented.attachment.row, scale=scale)
    elif presented.attachment.hint:
        draw_text(font, presented.attachment.hint, int(rect.x + 10.0 * scale), int(rect.y + 28.0 * scale), max(9, int(round(14 * scale))), LIGHTGRAY)
    if pill(font, Rectangle(button_rect.x, button_rect.y, 78.0 * scale, 22.0 * scale), "收回", False, scale=scale):
        clear_assembly(state)
    if pill(font, Rectangle(button_rect.x + button_rect.width - 78.0 * scale, button_rect.y, 78.0 * scale, 22.0 * scale), "执行", False, disabled=not presented.attachment.can_execute, scale=scale):
        perform_current_action(state, rng)


def draw_pending_attachment(font: Font | None, state: GameState, rect: Rectangle, button_rect: Rectangle, pending: PendingResolutionState, scale: float = 1.0) -> None:
    resolution = pending.resolution
    if resolution.result is not None and resolution.value is not None:
        draw_text(font, "判定中", int(rect.x + 10.0 * scale), int(rect.y + 6.0 * scale), max(10, int(round(16 * scale))), LIGHTGRAY)
        draw_inline_resolution_strip(font, Rectangle(rect.x + 10.0 * scale, rect.y + 26.0 * scale, rect.width - 20.0 * scale, 20.0 * scale), pending, scale=scale)
    else:
        draw_text(font, "执行中", int(rect.x + 10.0 * scale), int(rect.y + 6.0 * scale), max(10, int(round(16 * scale))), LIGHTGRAY)
    if pending.settled:
        result_rect = pending_result_rect(font, rect, resolution)
        draw_frame(result_rect, Color(16, 18, 24, 248), Color(78, 84, 98, 220))
        text_width = result_rect.width - 20.0 * scale
        text_y = int(result_rect.y + 10.0 * scale)
        for line in wrap_text_lines(font, resolution.text, text_width, max(10, int(round(14 * scale)))):
            draw_text(font, line, int(result_rect.x + 10.0 * scale), text_y, max(10, int(round(14 * scale))), RAYWHITE)
            text_y += int(round(16 * scale))
        if resolution.effect_lines:
            for line in wrap_text_lines(font, " | ".join(resolution.effect_lines[:2]), text_width, max(9, int(round(13 * scale)))):
                draw_text(font, line, int(result_rect.x + 10.0 * scale), text_y + 2, max(9, int(round(13 * scale))), Color(212, 196, 132, 255))
                text_y += int(round(15 * scale))
        continue_rect = Rectangle(result_rect.x + result_rect.width - 88.0 * scale, result_rect.y + result_rect.height + 8.0 * scale, 78.0 * scale, 22.0 * scale)
        if pill(font, continue_rect, "继续", False, scale=scale):
            dismiss_pending_resolution(state)
    else:
        draw_text(font, "结果会在这张卡下面落定。", int(rect.x + 10.0 * scale), int(rect.y + 44.0 * scale), max(9, int(round(14 * scale))), LIGHTGRAY)


def toggle_presented_slot(state: GameState, action: ActionDef, slot: ActionSlotModel) -> None:
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


def draw_inline_resolution_strip(font: Font | None, rect: Rectangle, pending: PendingResolutionState, scale: float = 1.0) -> None:
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
        draw_text(font, label, int(cell.x + 10.0 * scale), int(cell.y + 4.0 * scale), max(10, int(round(16 * scale))), RAYWHITE)
        x += cell_w


def pending_result_rect(font: Font | None, preview_rect: Rectangle, resolution) -> Rectangle:
    text_width = preview_rect.width - 168
    line_count = len(wrap_text_lines(font, resolution.text, text_width, 14))
    if resolution.effect_lines:
        line_count += len(wrap_text_lines(font, " | ".join(resolution.effect_lines[:2]), text_width, 13))
    height = max(46.0, 20.0 + line_count * 16.0)
    return Rectangle(preview_rect.x, preview_rect.y + preview_rect.height + 8, preview_rect.width, height)


def fit_grid_cards(
    rect: Rectangle,
    count: int,
    card_w: float,
    card_h: float,
    gap_x: float,
    gap_y: float,
    columns: int,
) -> list[tuple[Rectangle, float]]:
    if count <= 0:
        return []
    columns = max(1, min(columns, count))
    rows = max(1, (count + columns - 1) // columns)
    base_w = columns * card_w + (columns - 1) * gap_x
    base_h = rows * card_h + (rows - 1) * gap_y
    scale = min(1.0, rect.width / base_w, rect.height / base_h)
    scaled_w = base_w * scale
    scaled_h = base_h * scale
    origin_x = rect.x + (rect.width - scaled_w) * 0.5
    origin_y = rect.y + (rect.height - scaled_h) * 0.5
    laid_out: list[tuple[Rectangle, float]] = []
    for index in range(count):
        col = index % columns
        row = index // columns
        laid_out.append(
            (
                Rectangle(
                    origin_x + col * (card_w + gap_x) * scale,
                    origin_y + row * (card_h + gap_y) * scale,
                    card_w * scale,
                    card_h * scale,
                ),
                scale,
            )
        )
    return laid_out


def fit_absolute_world_objects(rect: Rectangle, cards: tuple[PresentedWorldObject, ...]) -> list[tuple[PresentedWorldObject, tuple[Rectangle, float]]]:
    if not cards:
        return []
    min_x = min(card.position[0] for card in cards)
    min_y = min(card.position[1] for card in cards)
    max_x = max(card.position[0] + card.card.style.width * card.scale_bias for card in cards)
    max_y = max(card.position[1] + card.card.style.height * card.scale_bias for card in cards)
    base_w = max_x - min_x
    base_h = max_y - min_y
    scale = min(1.0, rect.width / base_w, rect.height / base_h)
    scaled_w = base_w * scale
    scaled_h = base_h * scale
    origin_x = rect.x + (rect.width - scaled_w) * 0.5 - min_x * scale
    origin_y = rect.y + (rect.height - scaled_h) * 0.5 - min_y * scale
    laid_out: list[tuple[PresentedWorldObject, tuple[Rectangle, float]]] = []
    for presented in cards:
        laid_out.append(
            (
                presented,
                (
                    Rectangle(
                        origin_x + presented.position[0] * scale,
                        origin_y + presented.position[1] * scale,
                        presented.card.style.width * scale * presented.scale_bias,
                        presented.card.style.height * scale * presented.scale_bias,
                    ),
                    scale * presented.scale_bias,
                ),
            )
        )
    return laid_out


def layout_world_objects(rect: Rectangle, cards: tuple[PresentedWorldObject, ...]) -> list[tuple[PresentedWorldObject, tuple[Rectangle, float]]]:
    return fit_absolute_world_objects(rect, cards) if all_positioned(card.position for card in cards) else []


def layout_location_cards(rect: Rectangle, cards: tuple[PresentedLocationCard, ...], columns: int) -> list[tuple[Rectangle, float]]:
    if all_positioned(card.position for card in cards):
        return fit_absolute_card_positions(rect, cards, lambda item: item.position, lambda item: item.card.style.width, lambda item: item.card.style.height)
    return fit_grid_cards(rect, len(cards), 188.0, 96.0, 18.0, 18.0, columns)


def layout_action_cards(rect: Rectangle, cards: tuple[PresentedActionCard, ...], columns: int) -> list[tuple[Rectangle, float]]:
    if all_positioned(card.position for card in cards):
        return fit_absolute_card_positions(rect, cards, lambda item: item.position, lambda item: item.card.style.width, lambda item: item.card.style.height)
    return fit_grid_cards(rect, len(cards), 232.0, 224.0, 18.0, 96.0, columns)


def all_positioned(positions) -> bool:
    positions = tuple(positions)
    return bool(positions) and all(position is not None for position in positions)


def fit_absolute_card_positions(rect: Rectangle, cards, position_getter, width_getter, height_getter) -> list[tuple[Rectangle, float]]:
    if not cards:
        return []
    min_x = min(position_getter(card)[0] for card in cards)
    min_y = min(position_getter(card)[1] for card in cards)
    max_x = max(position_getter(card)[0] + width_getter(card) for card in cards)
    max_y = max(position_getter(card)[1] + height_getter(card) for card in cards)
    base_w = max_x - min_x
    base_h = max_y - min_y
    scale = min(1.0, rect.width / base_w, rect.height / base_h)
    scaled_w = base_w * scale
    scaled_h = base_h * scale
    origin_x = rect.x + (rect.width - scaled_w) * 0.5 - min_x * scale
    origin_y = rect.y + (rect.height - scaled_h) * 0.5 - min_y * scale
    return [
        (
            Rectangle(
                origin_x + position_getter(card)[0] * scale,
                origin_y + position_getter(card)[1] * scale,
                width_getter(card) * scale,
                height_getter(card) * scale,
            ),
            scale,
        )
        for card in cards
    ]
