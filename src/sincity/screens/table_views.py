from __future__ import annotations

from pyray import *  # type: ignore

from sincity.model.defs import ActionDef
from sincity.model.state import ActiveActionRevealState, GameState, PendingResolutionState
from sincity.rendering import draw_text
from sincity.game.judgment import RESULT_TABLE, clamp_action_value
from sincity.game.flow import dispatch
from sincity.game.commands import ExecuteAction, OpenAction, ToggleEnergySlot, ToggleRequirementSlot
from sincity.game.actions import (
    clear_action_reveal,
    clear_assembly,
    clear_selected_input,
    focus_action,
    open_modal,
    open_overlay,
)

from .city_presenters import PresentedWorldObject
from .table_presenters import ActionFactorPreview, ActionSlotModel, PresentedActionCard, PresentedLocationCard
from .ui_core import current_layer_z, draw_frame, layout, measure_text_width, pill, register_input_region, wrap_text_lines, wrap_text_lines_any
from .ui_cards import draw_table_card
from .ui_panels import draw_result_strip
from .ui_text import ui_text_color, ui_text_size, ui_text_style
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
    base_z = current_layer_z()
    world_layers: list[int] = []
    for index, (presented, card, _scale) in enumerate(laid_out):
        item_z = base_z + index + 1
        world_layers.append(item_z)
        register_input_region(
            f"world_object:{presented.kind}:{presented.location_id or (presented.action_card.action.id if presented.action_card is not None else '')}",
            card,
            z=item_z,
            interactive=presented.kind == "location",
        )
    for (presented, card, scale), item_z in zip(laid_out, world_layers):
        if presented.kind == "location":
            if draw_table_card(font, card, state, presented.card, scale=scale, z=item_z):
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
    columns = action_grid_columns(rect, cards)
    laid_out = layout_action_cards(rect, cards, columns)
    for presented, (card, scale) in zip(cards, laid_out):
        draw_action_card(font, state, presented, card, rng, scale=scale)


def action_grid_columns(rect: Rectangle, cards: tuple[PresentedActionCard, ...]) -> int:
    card_w = 232.0
    reserved_w = card_w + 2 * action_factor_reserve(cards)
    comfortable = max(1, int((rect.width + 18.0) // (reserved_w + 18.0)))
    compact = max(1, int((rect.width + 18.0) // (card_w + 18.0)))
    if comfortable >= len(cards):
        return len(cards)
    return min(len(cards), max(comfortable, min(compact, 3)))


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
    draw_mixed_location_flow(font, state, rng, content_rect, child_cards, action_cards, nested_locations=nested_locations)


def draw_mixed_location_flow(
    font: Font | None,
    state: GameState,
    rng,
    rect: Rectangle,
    child_cards: tuple[PresentedLocationCard, ...],
    action_cards: tuple[PresentedActionCard, ...],
    *,
    nested_locations: bool,
) -> None:
    gap_x = 18.0
    gap_y = 18.0
    action_reserve = action_factor_reserve(action_cards)
    rows: list[list[tuple[str, PresentedLocationCard | PresentedActionCard, float, float, float]]] = []
    current_row: list[tuple[str, PresentedLocationCard | PresentedActionCard, float, float, float]] = []
    current_w = 0.0

    for item in _mixed_location_items(font, child_cards, action_cards, action_reserve):
        item_w = item[2]
        next_w = item_w if not current_row else current_w + gap_x + item_w
        if current_row and next_w > rect.width:
            rows.append(current_row)
            current_row = [item]
            current_w = item_w
        else:
            current_row.append(item)
            current_w = next_w
    if current_row:
        rows.append(current_row)
    if not rows:
        return

    row_heights = [max(item[4] for item in row) for row in rows]
    row_widths = [sum(item[2] for item in row) + gap_x * max(0, len(row) - 1) for row in rows]
    natural_h = sum(row_heights) + gap_y * max(0, len(rows) - 1)
    natural_w = max(row_widths)
    scale = min(1.0, rect.width / natural_w, rect.height / natural_h)
    block_h = natural_h * scale
    y = rect.y + max(0.0, (rect.height - block_h) * 0.5)
    for row, row_w, row_h in zip(rows, row_widths, row_heights):
        x = rect.x + max(0.0, (rect.width - row_w * scale) * 0.5)
        for kind, presented, cell_w, card_h, _layout_h in row:
            if kind == "location":
                assert isinstance(presented, PresentedLocationCard)
                card = Rectangle(x, y, cell_w * scale, card_h * scale)
                if draw_table_card(font, card, state, presented.card, scale=scale):
                    clear_assembly(state)
                    clear_selected_input(state)
                    if nested_locations:
                        open_overlay(state, "location", presented.location_id)
                    else:
                        open_modal(state, "location", presented.location_id)
            else:
                assert isinstance(presented, PresentedActionCard)
                card = Rectangle(x + action_reserve * scale, y, (cell_w - action_reserve * 2) * scale, card_h * scale)
                draw_action_card(font, state, presented, card, rng, scale=scale)
            x += (cell_w + gap_x) * scale
        y += (row_h + gap_y) * scale


def _mixed_location_items(
    font: Font | None,
    child_cards: tuple[PresentedLocationCard, ...],
    action_cards: tuple[PresentedActionCard, ...],
    action_reserve: float,
) -> tuple[tuple[str, PresentedLocationCard | PresentedActionCard, float, float, float], ...]:
    items: list[tuple[str, PresentedLocationCard | PresentedActionCard, float, float, float]] = []
    for card in child_cards:
        height = preferred_location_height(font, card)
        items.append(("location", card, LOCATION_CARD_WIDTH, height, height))
    for card in action_cards:
        card_height = card.card.style.height
        button_space = 36.0 if card.attachment is not None else 0.0
        items.append(("action", card, card.card.style.width + action_reserve * 2, card_height, card_height + button_space))
    return tuple(items)


def draw_action_card(font: Font | None, state: GameState, presented: PresentedActionCard, rect: Rectangle, rng, scale: float = 1.0) -> None:
    action = presented.action
    pending = state.pending_resolution if state.pending_resolution and state.pending_resolution.resolution.action_id == action.id else None
    draw_table_card(font, rect, state, presented.card, scale=scale)
    draw_action_factor_sidebars(font, rect, presented, scale=scale)

    mode = presented.attachment.mode if presented.attachment is not None else ""
    is_direct = mode in ("instant_ready", "reveal_ready")
    is_revealing = mode == "reveal"

    button_rects: tuple[Rectangle, Rectangle] | tuple[Rectangle] | None = None
    button_z = current_layer_z() + 1
    if presented.attachment is not None and not is_revealing:
        if is_direct:
            btn_w = 78.0 * scale
            btn_h = 22.0 * scale
            execute_rect = Rectangle(rect.x + (rect.width - btn_w) * 0.5, rect.y + rect.height - 32.0 * scale, btn_w, btn_h)
            register_input_region("action_execute_button", execute_rect, z=button_z, interactive=presented.attachment.can_execute)
            button_rects = (execute_rect,)
        else:
            button_strip = Rectangle(rect.x + 18.0 * scale, rect.y + rect.height + 8.0 * scale, rect.width - 36.0 * scale, 24.0 * scale)
            retract_rect = Rectangle(button_strip.x, button_strip.y, 78.0 * scale, 22.0 * scale)
            execute_rect = Rectangle(button_strip.x + button_strip.width - 78.0 * scale, button_strip.y, 78.0 * scale, 22.0 * scale)
            register_input_region("action_retract_button", retract_rect, z=button_z)
            register_input_region("action_execute_button", execute_rect, z=button_z, interactive=presented.attachment.can_execute)
            button_rects = (retract_rect, execute_rect)
    elif is_revealing:
        btn_w = 78.0 * scale
        btn_h = 22.0 * scale
        reveal_close_rect = Rectangle(rect.x + (rect.width - btn_w) * 0.5, rect.y + rect.height - 32.0 * scale, btn_w, btn_h)
        register_input_region("action_reveal_close_button", reveal_close_rect, z=button_z)
        button_rects = (reveal_close_rect,)

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
        if is_revealing:
            assert button_rects is not None
            reveal_close_rect = button_rects[0]
            if pill(font, reveal_close_rect, "收起", False, scale=scale, z=button_z):
                    clear_action_reveal(state)
                    return
            reveal_attachment_h = 14.0 * scale if state.action_reveal is not None and state.action_reveal.duration > 0 else 0.0
            if reveal_attachment_h > 0:
                preview_rect = Rectangle(rect.x + 2.0 * scale, rect.y + rect.height - reveal_attachment_h, rect.width - 4.0 * scale, reveal_attachment_h)
                draw_reveal_progress_bar(font, preview_rect, state.action_reveal, scale=scale)
        elif is_direct:
            execute_rect = button_rects[0]
            default_label = "查看" if action.reveal is not None else "执行"
            label = action.button_label or default_label
            if pill(font, execute_rect, label, False, disabled=not presented.attachment.can_execute, scale=scale, z=button_z):
                if state.assembly.action_id != action.id:
                    focus_action(state, action.id)
                dispatch(state, ExecuteAction(), rng)
        else:
            preview_rect = Rectangle(rect.x + 14.0 * scale, rect.y + rect.height - 90.0 * scale, rect.width - 28.0 * scale, 68.0 * scale)
            assert button_rects is not None
            draw_action_attachment(font, state, action, presented, preview_rect, button_rects, rng, pending, scale=scale, button_z=button_z)
    elif presented.card.disabled:
        disabled_style = ui_text_style("body_sm", "subtle", scale=scale, minimum_size=10)
        draw_text(font, "条件未满足或当前资源不足。", int(rect.x + 14.0 * scale), int(rect.y + rect.height - 26.0 * scale), disabled_style.size, disabled_style.color)


def draw_action_factor_sidebars(font: Font | None, rect: Rectangle, presented: PresentedActionCard, scale: float = 1.0) -> None:
    sidebar_w = (96.0 if scale >= 0.9 else 72.0) * scale
    offset = (72.0 if scale >= 0.9 else 48.0) * scale
    if presented.actor_factors:
        draw_factor_stack(font, Rectangle(rect.x - offset, rect.y + 104.0 * scale, sidebar_w, 96.0 * scale), presented.actor_factors, align="right", scale=scale)
    if presented.environment_factors:
        draw_factor_stack(font, Rectangle(rect.x + rect.width + 10.0 * scale, rect.y + 104.0 * scale, sidebar_w, 96.0 * scale), presented.environment_factors, align="left", scale=scale)


def draw_factor_stack(font: Font | None, rect: Rectangle, factors: tuple[ActionFactorPreview, ...], *, align: str, scale: float = 1.0) -> None:
    chip_h = 18.0 * scale
    gap = 5.0 * scale
    y = rect.y
    for factor in factors[:5]:
        label = _factor_label(factor)
        style = ui_text_style("body_sm", scale=scale, minimum_size=9)
        chip_w = min(rect.width, measure_text_width(font, label, style.size) + 18.0 * scale)
        x = rect.x + rect.width - chip_w if align == "right" else rect.x
        color = _factor_theme_color(factor)
        chip = Rectangle(x, y, chip_w, chip_h)
        draw_frame(chip, Color(color.r, color.g, color.b, 78), Color(color.r, color.g, color.b, 178))
        draw_text(font, label, int(chip.x + 8.0 * scale), int(chip.y + 2.0 * scale), style.size, ui_text_color("default"))
        y += chip_h + gap


def _factor_label(factor: ActionFactorPreview) -> str:
    sign = "+" if factor.value > 0 else ""
    return f"{factor.label} {sign}{factor.value}"


def _factor_theme_color(factor: ActionFactorPreview) -> Color:
    if factor.actor_id == "cole":
        return Color(194, 158, 78, 255)
    if factor.actor_id == "lena":
        return Color(70, 142, 190, 255)
    if factor.actor_id == "marco":
        return Color(122, 106, 190, 255)
    if factor.source == "environment":
        return Color(104, 122, 142, 255)
    return Color(140, 146, 158, 255)


def draw_action_attachment(
    font: Font | None,
    state: GameState,
    action: ActionDef,
    presented: PresentedActionCard,
    rect: Rectangle,
    button_rects: tuple[Rectangle, Rectangle] | tuple[Rectangle],
    rng,
    pending: PendingResolutionState | None,
    scale: float = 1.0,
    button_z: int | None = None,
) -> None:
    draw_frame(rect, Color(18, 20, 26, 255), Color(78, 84, 98, 220))
    if pending is not None:
        draw_pending_attachment(font, state, rect, button_rects, pending, scale=scale, button_z=button_z)
        return
    assert presented.attachment is not None
    mode = presented.attachment.mode

    title_style = ui_text_style(
        "body",
        "warning" if mode == "preview" and presented.attachment.row else "muted",
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
    retract_rect, execute_rect = button_rects
    if pill(font, retract_rect, "收回", False, scale=scale, z=button_z):
        clear_assembly(state)
    if pill(font, execute_rect, "执行", False, disabled=not presented.attachment.can_execute, scale=scale, z=button_z):
        if state.assembly.action_id != action.id:
            focus_action(state, action.id)
        dispatch(state, ExecuteAction(), rng)


def draw_pending_attachment(font: Font | None, state: GameState, rect: Rectangle, button_rects: tuple[Rectangle, Rectangle], pending: PendingResolutionState, scale: float = 1.0, button_z: int | None = None) -> None:
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
        if not pending.settled:
            draw_pending_progress_bar(font, Rectangle(rect.x + 10.0 * scale, rect.y + 30.0 * scale, rect.width - 20.0 * scale, 14.0 * scale), pending, scale=scale)
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
        draw_text(font, "完成后生效。", int(rect.x + 10.0 * scale), int(rect.y + 50.0 * scale), body_style.size, title_style.color)


def draw_pending_progress_bar(font: Font | None, rect: Rectangle, pending: PendingResolutionState, scale: float = 1.0) -> None:
    del font, scale
    progress = max(0.0, min(1.0, pending.progress))
    draw_frame(rect, Color(32, 36, 44, 220), Color(18, 20, 26, 255))
    fill_w = rect.width * progress
    if fill_w > 2.0:
        draw_frame(Rectangle(rect.x, rect.y, fill_w, rect.height), Color(180, 150, 84, 220), Color(18, 20, 26, 255))


def draw_reveal_progress_bar(font: Font | None, rect: Rectangle, reveal: ActiveActionRevealState | None, scale: float = 1.0) -> None:
    if reveal is None:
        return
    progress = min(1.0, reveal.elapsed / reveal.duration) if reveal.duration > 0 else 0.0
    filled_w = rect.width * progress
    bar_color = Color(104, 122, 142, 200)
    bg_color = Color(32, 36, 44, 200)
    draw_frame(Rectangle(rect.x, rect.y, rect.width, rect.height), bg_color, Color(18, 20, 26, 255))
    if filled_w > 2.0:
        draw_frame(Rectangle(rect.x, rect.y, filled_w, rect.height), bar_color, Color(18, 20, 26, 255))


def toggle_presented_slot(state: GameState, action: ActionDef, slot: ActionSlotModel) -> None:
    if slot.slot_kind == "energy":
        dispatch(state, ToggleEnergySlot(action.id))
        return
    if slot.slot_kind == "requirement":
        assert slot.requirement is not None
        dispatch(state, ToggleRequirementSlot(action.id, slot.requirement.key))
        return
    dispatch(state, OpenAction(action.id))


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
    reserve = action_factor_reserve(cards)
    laid_out = fit_grid_cards(rect, len(cards), 232.0 + reserve * 2, 224.0, 18.0, 96.0, columns)
    result: list[tuple[Rectangle, float]] = []
    for cell, scale in laid_out:
        result.append((Rectangle(cell.x + reserve * scale, cell.y, 232.0 * scale, cell.height), scale))
    return result


def action_factor_reserve(cards: tuple[PresentedActionCard, ...]) -> float:
    if not any(card.actor_factors or card.environment_factors for card in cards):
        return 0.0
    return 72.0


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
