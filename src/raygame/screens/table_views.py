from __future__ import annotations

from pyray import *  # type: ignore

from raygame.model.defs import ActionDef
from raygame.model.state import GameState, PendingResolutionState
from raygame.rendering import draw_text
from raygame.rules.judgment import RESULT_TABLE, clamp_action_value
from raygame.rules import (
    clear_assembly,
    clear_selected_input,
    focus_action,
    open_modal,
    open_overlay,
    perform_current_action,
    toggle_action_energy_slot,
    toggle_action_requirement_slot,
)

from .city_presenters import PresentedWorldObject
from .table_presenters import ActionSlotModel, PresentedActionCard, PresentedLocationCard
from .ui_core import draw_frame, layout, pill, wrap_text_lines, wrap_text_lines_any
from .ui_cards import draw_table_card
from .ui_panels import draw_result_strip
from .ui_text import ui_text_size, ui_text_style
from .widgets import draw_note_block, draw_scrim, draw_slot_chip, draw_table_shell


MESSAGE_SIDEBAR_GAP = 14.0
MESSAGE_SIDEBAR_WIDTH = 300.0
LOCATION_CARD_WIDTH = 188.0
LOCATION_CARD_MIN_HEIGHT = 96.0
LOCATION_CARD_MAX_HEIGHT = 156.0


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
    laid_out = layout_location_cards(font, rect, cards, columns)
    for presented, (card, scale) in zip(cards, laid_out):
        if draw_table_card(font, card, state, presented.card, scale=scale):
            clear_assembly(state)
            clear_selected_input(state)
            if nested:
                open_overlay(state, "location", presented.location_id)
            else:
                open_modal(state, "location", presented.location_id)


def draw_world_objects(font: Font | None, state: GameState, rng, rect: Rectangle, cards: tuple[PresentedWorldObject, ...]) -> None:
    laid_out = layout_world_objects(font, rect, cards)
    for presented, card, scale in laid_out:
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
    *,
    nested_locations: bool = True,
) -> None:
    if not child_cards and not action_cards:
        draw_note_block(font, Rectangle(content_rect.x, content_rect.y, content_rect.width, 86), "这里暂时没有可做的事", "换个地方，或者先满足别的条件。")
        return
    if child_cards:
        child_strip = Rectangle(content_rect.x, content_rect.y, content_rect.width, 114)
        draw_location_grid(
            font,
            state,
            child_strip,
            child_cards,
            columns=max(1, min(3, len(child_cards))),
            nested=nested_locations,
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

    metadata_rows = max(0, len(presented.card.metadata) - 1)
    slot_y = rect.y + (124.0 + metadata_rows * 18.0) * scale
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
        disabled_style = ui_text_style("body_sm", "subtle", scale=scale, minimum_size=10)
        draw_text(font, "条件未满足或当前资源不足。", int(rect.x + 14.0 * scale), int(rect.y + rect.height - 26.0 * scale), disabled_style.size, disabled_style.color)


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
    title_style = ui_text_style(
        "body",
        "warning" if presented.attachment.mode == "preview" and presented.attachment.row else "muted",
        scale=scale,
        minimum_size=10,
    )
    body_style = ui_text_style("body_sm", "muted", scale=scale, minimum_size=9)
    draw_text(font, presented.attachment.title, int(rect.x + 10.0 * scale), int(rect.y + 6.0 * scale), title_style.size, title_style.color)
    if presented.attachment.row:
        draw_result_strip(font, Rectangle(rect.x + 10.0 * scale, rect.y + 28.0 * scale, rect.width - 20.0 * scale, 20.0 * scale), presented.attachment.row, scale=scale)
    elif presented.attachment.hint:
        hint_rect = Rectangle(rect.x + 8.0 * scale, rect.y + 26.0 * scale, rect.width - 16.0 * scale, rect.height - 30.0 * scale)
        hint_width = max(20.0, hint_rect.width - 12.0 * scale)
        hint_x = int(hint_rect.x + 6.0 * scale)
        hint_y = int(hint_rect.y + 4.0 * scale)
        begin_scissor_mode(int(hint_rect.x), int(hint_rect.y), int(hint_rect.width), int(hint_rect.height))
        for line in wrap_text_lines_any(font, presented.attachment.hint, hint_width, body_style.size)[:3]:
            draw_text(font, line, hint_x, hint_y, body_style.size, body_style.color)
            hint_y += body_style.line_height - 1
        end_scissor_mode()
    if pill(font, Rectangle(button_rect.x, button_rect.y, 78.0 * scale, 22.0 * scale), "收回", False, scale=scale):
        clear_assembly(state)
    if pill(font, Rectangle(button_rect.x + button_rect.width - 78.0 * scale, button_rect.y, 78.0 * scale, 22.0 * scale), "执行", False, disabled=not presented.attachment.can_execute, scale=scale):
        perform_current_action(state, rng)


def draw_pending_attachment(font: Font | None, state: GameState, rect: Rectangle, button_rect: Rectangle, pending: PendingResolutionState, scale: float = 1.0) -> None:
    resolution = pending.resolution
    title_style = ui_text_style("body", "muted", scale=scale, minimum_size=10)
    body_style = ui_text_style("body_sm", scale=scale, minimum_size=10)
    accent_style = ui_text_style("caption", "accent", scale=scale, minimum_size=9)
    caption_style = ui_text_style("caption", "subtle", scale=scale, minimum_size=9)
    if resolution.result is not None and resolution.value is not None:
        draw_text(font, "判定中", int(rect.x + 10.0 * scale), int(rect.y + 6.0 * scale), title_style.size, title_style.color)
        draw_inline_resolution_strip(font, Rectangle(rect.x + 10.0 * scale, rect.y + 26.0 * scale, rect.width - 20.0 * scale, 20.0 * scale), pending, scale=scale)
    else:
        draw_text(font, "执行中", int(rect.x + 10.0 * scale), int(rect.y + 6.0 * scale), title_style.size, title_style.color)
    if pending.settled:
        result_rect = pending_result_rect(font, rect, resolution)
        draw_frame(result_rect, Color(16, 18, 24, 248), Color(78, 84, 98, 220))
        text_width = result_rect.width - 20.0 * scale
        text_y = int(result_rect.y + 10.0 * scale)
        for line in wrap_text_lines(font, resolution.text, text_width, body_style.size):
            draw_text(font, line, int(result_rect.x + 10.0 * scale), text_y, body_style.size, body_style.color)
            text_y += body_style.line_height - 2
        if resolution.effect_lines:
            for line in wrap_text_lines(font, " | ".join(resolution.effect_lines[:2]), text_width, accent_style.size):
                draw_text(font, line, int(result_rect.x + 10.0 * scale), text_y + 2, accent_style.size, accent_style.color)
                text_y += accent_style.line_height - 1
        draw_text(
            font,
            "任意输入后自动关闭",
            int(result_rect.x + 10.0 * scale),
            int(result_rect.y + result_rect.height - 18.0 * scale),
            caption_style.size,
            caption_style.color,
        )
    else:
        draw_text(font, "结果会在这张卡下面落定。", int(rect.x + 10.0 * scale), int(rect.y + 44.0 * scale), body_style.size, title_style.color)


def toggle_presented_slot(state: GameState, action: ActionDef, slot: ActionSlotModel) -> None:
    if slot.slot_kind == "energy":
        toggle_action_energy_slot(state, action)
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
            fill, label = Color(124, 66, 66, 255), "坏"
        elif result.value == "cost":
            fill, label = Color(144, 126, 70, 255), "中"
        else:
            fill, label = Color(74, 134, 92, 255), "好"
        cell = Rectangle(x, rect.y, cell_w - 4, rect.height)
        draw_frame(cell, fill, Color(22, 22, 22, 180))
        if index == active_index:
            draw_rectangle_rounded_lines_ex(cell, 0.035, 6, 3.0, Color(233, 216, 152, 255))
        label_style = ui_text_style("body", scale=scale, minimum_size=10)
        draw_text(font, label, int(cell.x + 10.0 * scale), int(cell.y + 4.0 * scale), label_style.size, label_style.color)
        x += cell_w


def pending_result_rect(font: Font | None, preview_rect: Rectangle, resolution) -> Rectangle:
    text_width = preview_rect.width - 168
    line_count = len(wrap_text_lines(font, resolution.text, text_width, ui_text_size("body_sm")))
    if resolution.effect_lines:
        line_count += len(wrap_text_lines(font, " | ".join(resolution.effect_lines[:2]), text_width, ui_text_size("caption")))
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


def layout_world_objects(
    font: Font | None,
    rect: Rectangle,
    cards: tuple[PresentedWorldObject, ...],
) -> list[tuple[PresentedWorldObject, Rectangle, float]]:
    if not cards:
        return []
    if all_positioned(card.position for card in cards):
        laid_out = fit_absolute_card_positions(
            rect,
            cards,
            lambda item: item.position,
            lambda item: item.card.style.width,
            lambda item: preferred_world_object_height(font, item),
        )
        return [(presented, card, scale) for presented, (card, scale) in zip(cards, laid_out)]
    return []


def layout_location_cards(font: Font | None, rect: Rectangle, cards: tuple[PresentedLocationCard, ...], columns: int) -> list[tuple[Rectangle, float]]:
    if all_positioned(card.position for card in cards):
        return fit_absolute_card_positions(
            rect,
            cards,
            lambda item: item.position,
            lambda item: item.card.style.width,
            lambda item: preferred_location_height(font, item),
        )
    card_h = max(preferred_location_height(font, card) for card in cards) if cards else LOCATION_CARD_MIN_HEIGHT
    return fit_grid_cards(rect, len(cards), LOCATION_CARD_WIDTH, card_h, 18.0, 18.0, columns)


def layout_action_cards(rect: Rectangle, cards: tuple[PresentedActionCard, ...], columns: int) -> list[tuple[Rectangle, float]]:
    if all_positioned(card.position for card in cards):
        return fit_absolute_card_positions(rect, cards, lambda item: item.position, lambda item: item.card.style.width, lambda item: item.card.style.height)
    return fit_grid_cards(rect, len(cards), 232.0, 224.0, 18.0, 96.0, columns)


def all_positioned(positions) -> bool:
    positions = tuple(positions)
    return bool(positions) and all(position is not None for position in positions)


def preferred_location_height(font: Font | None, card: PresentedLocationCard) -> float:
    return _preferred_card_height(font, card.card.body, card.card.style.body_size, card.card.style.width)


def preferred_world_object_height(font: Font | None, card: PresentedWorldObject) -> float:
    if card.kind == "location":
        return _preferred_card_height(font, card.card.body, card.card.style.body_size, card.card.style.width)
    return card.card.style.height


def _preferred_card_height(font: Font | None, body: str, body_size: int, width: float) -> float:
    body_w = max(1.0, width - 28.0)
    body_lines = wrap_text_lines_any(font, body, body_w, body_size)
    line_h = max(12, int(round(body_size + 2)))
    height = 42.0 + len(body_lines) * line_h + 12.0
    return max(LOCATION_CARD_MIN_HEIGHT, min(LOCATION_CARD_MAX_HEIGHT, height))


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
