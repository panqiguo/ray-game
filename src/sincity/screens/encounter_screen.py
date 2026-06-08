from __future__ import annotations

from pyray import *  # type: ignore

from sincity.model.defs import AddFieldPayload, DynamicValue, FieldRef, SetFieldPayload, ShiftClockPayload
from sincity.model.state import GameState
from sincity.rendering import draw_text
from sincity.game.flow import dispatch
from sincity.game.commands import CloseModal, DismissPendingResolution, FastForwardDialogue
from sincity.game.events import DialogueFastForwarded
from sincity.game.actions import current_action
from sincity.game.queries import current_encounter_reaction_table, get_clock_spec_for_state
from sincity.game.conditions import location_is_visible
from sincity.screens.encounter_presenters import (
    current_encounter_clocks,
    current_encounter_root,
    current_encounter_titles,
    present_encounter_action_cards,
    present_encounter_child_location_cards,
    present_encounter_location_clocks,
)
from sincity.screens.table_views import draw_location_contents, floating_table_rect, split_desktop_area
from sincity.screens.widgets import (
    begin_layer,
    any_input_pressed,
    draw_card_pile_modal,
    draw_rendered_clock_row,
    draw_dialogue_modal,
    draw_hand,
    draw_message_feed,
    draw_profile_modal,
    draw_scrim,
    draw_selected_card_curve_overlay,
    draw_table_shell,
    end_layer,
    layout,
)
from .ui_core import Z_HAND, Z_LOCATION_MODAL, Z_MESSAGE, Z_WORLD
from .ui_core import draw_frame, measure_text_width
from .ui_text import ui_text_size, ui_text_style


def draw_encounter_screen(font: Font | None, state: GameState, rng) -> None:
    if state.pending_resolution is not None and state.pending_resolution.settled and any_input_pressed():
        dispatch(state, DismissPendingResolution(), rng)
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    if is_key_pressed(KEY_ESCAPE) and not resolving:
        events = dispatch(state, FastForwardDialogue(), rng)
        if not any(isinstance(e, DialogueFastForwarded) for e in events):
            dispatch(state, CloseModal(), rng)
    page = layout()
    table_rect, message_rect = split_desktop_area(page.stage)
    begin_layer("encounter_root", z=Z_WORLD)
    _draw_encounter_table(font, state, rng, table_rect)
    end_layer("encounter_root")
    draw_card_pile_modal(font, state)
    begin_layer("hand", z=Z_HAND)
    draw_hand(font, state, current_action(state), rng)
    end_layer("hand")
    begin_layer("message", z=Z_MESSAGE)
    draw_message_feed(font, message_rect, state)
    end_layer("message")
    if state.modal.kind == "location" and state.modal.primary_id is not None:
        for i, frame in enumerate(state.modal.stacked_frames):
            if frame.kind == "location" and frame.primary_id is not None:
                begin_layer(f"encounter_location_table_{i}", z=Z_LOCATION_MODAL)
                _draw_encounter_location_table(font, state, rng, depth=i, location_id=frame.primary_id)
                end_layer(f"encounter_location_table_{i}")
        begin_layer("encounter_location_table_top", z=Z_LOCATION_MODAL + len(state.modal.stacked_frames))
        _draw_encounter_location_table(font, state, rng, depth=len(state.modal.stacked_frames))
        end_layer("encounter_location_table_top")
    draw_profile_modal(font, state)
    draw_dialogue_modal(font, state)
    draw_selected_card_curve_overlay(state)


def _draw_encounter_table(font: Font | None, state: GameState, rng, rect: Rectangle) -> None:
    encounter_title, act_title, state_description = current_encounter_titles(state)
    root = current_encounter_root(state)
    title = f"{encounter_title} / {act_title}" if encounter_title else act_title
    sections, _ = draw_table_shell(
        font,
        rect,
        title=title,
        subtitle=state_description or root.description,
    )
    draw_rendered_clock_row(
        font,
        Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 48),
        current_encounter_clocks(state),
    )
    reaction_table = current_encounter_reaction_table(state)
    if reaction_table is not None:
        _draw_reaction_die_table(font, sections.note, state, reaction_table)
    _draw_location_contents(font, state, rng, root, sections.content, nested_locations=False)


def _draw_reaction_die_table(font: Font | None, rect: Rectangle, state: GameState, table) -> None:
    draw_frame(rect, Color(24, 27, 34, 238), Color(88, 78, 56, 210))
    title_style = ui_text_style("body_sm", "warning")
    face_style = ui_text_style("body_sm", "accent")
    empty_style = ui_text_style("body_sm", "disabled")
    body_style = ui_text_style("body_sm", "muted")

    title = "反应骰"
    draw_text(font, title, int(rect.x + 10), int(rect.y + 7), title_style.size, title_style.color)
    title_w = measure_text_width(font, title, title_style.size)
    draw_text(font, "休整掷 1d6", int(rect.x + 16 + title_w), int(rect.y + 7), body_style.size, body_style.color)

    groups = _reaction_face_groups(state, table)
    bar_x = rect.x + 10
    bar_y = rect.y + 30
    bar_w = rect.width - 20
    bar_h = 16.0
    cursor_x = bar_x
    for start, end, title_text, effect_text, is_empty, count in groups:
        seg_w = bar_w * (count / 6)
        fill = Color(22, 24, 30, 220) if is_empty else Color(66, 43, 35, 235)
        border = Color(68, 70, 78, 130) if is_empty else Color(178, 92, 72, 220)
        draw_frame(Rectangle(cursor_x, bar_y, max(1.0, seg_w - 2), bar_h), fill, border)
        cursor_x += seg_w

    line_y = rect.y + 52
    for start, end, title_text, effect_text, is_empty, _count in groups[:3]:
        label_style = empty_style if is_empty else face_style
        range_text = str(start) if start == end else f"{start}-{end}"
        draw_text(font, range_text, int(rect.x + 12), int(line_y), label_style.size, label_style.color)
        draw_text(font, _fit_text(font, title_text, 74, label_style.size), int(rect.x + 44), int(line_y), label_style.size, label_style.color)
        draw_text(font, _fit_text(font, effect_text, rect.width - 128, body_style.size), int(rect.x + 120), int(line_y), body_style.size, body_style.color)
        line_y += body_style.line_height - 2


def _reaction_face_groups(state: GameState, table) -> list[tuple[int, int, str, str, bool, int]]:
    faces = {face.value: face for face in table.faces}
    groups: list[tuple[int, int, str, str, bool, int]] = []
    current: tuple[str, str, bool] | None = None
    start = 1
    end = 1
    for value in range(1, 7):
        face = faces.get(value)
        is_empty = face is None or (face.title == "空" and not face.description and not face.effects)
        title_text = "空" if face is None else face.title
        effect_text = "无" if face is None or not face.effects else _reaction_effect_summary(state, face.effects)
        key = (title_text, effect_text, is_empty)
        if current is None:
            current = key
            start = value
            end = value
            continue
        if key == current and value == end + 1:
            end = value
            continue
        groups.append((start, end, current[0], current[1], current[2], end - start + 1))
        current = key
        start = value
        end = value
    assert current is not None
    groups.append((start, end, current[0], current[1], current[2], end - start + 1))
    return groups


def _reaction_effect_summary(state: GameState, effects) -> str:
    parts: list[str] = []
    for effect in effects:
        value = effect.value
        if effect.kind == "shift_clock":
            if isinstance(value, ShiftClockPayload):
                key, amount = value.target, value.amount
            elif isinstance(value, str):
                key, raw = value.split(":", 1)
                amount = int(raw)
            else:
                continue
            spec = get_clock_spec_for_state(state, key)
            parts.append(f"{spec.title}{'+' if amount >= 0 else ''}{amount}")
        elif effect.kind == "add_field":
            if isinstance(value, AddFieldPayload):
                key, amount = value.target, value.amount
            elif isinstance(value, str):
                key, raw = value.split(":", 1)
                amount = int(raw)
            else:
                continue
            parts.append(f"{_field_label(key)}{'+' if amount >= 0 else ''}{amount}")
        elif effect.kind == "set_field":
            if isinstance(value, SetFieldPayload):
                key = value.target
                if isinstance(value.value, FieldRef):
                    raw = value.value.name
                elif isinstance(value.value, DynamicValue):
                    raw = "表达式"
                else:
                    raw = value.value
            elif isinstance(value, str):
                key, raw = value.split(":", 1)
            else:
                continue
            if raw == "0":
                parts.append(f"{_field_label(key)}=0")
            else:
                parts.append(f"{_field_label(key)}={raw}")
    return "，".join(parts[:2]) if parts else "变化"


def _field_label(key: str) -> str:
    if key == "health":
        return "生命"
    if key == "energy":
        return "精力"
    return key


def _fit_text(font: Font | None, text: str, max_width: float, size: int) -> str:
    if measure_text_width(font, text, size) <= max_width:
        return text
    result = text
    while len(result) > 1 and measure_text_width(font, result + "…", size) > max_width:
        result = result[:-1]
    return result + "…"


def _draw_encounter_location_table(font: Font | None, state: GameState, rng, *, depth: int = 0, location_id: str | None = None) -> None:
    root = current_encounter_root(state)
    lid = location_id if location_id is not None else state.modal.primary_id
    assert lid is not None
    target = next((child for child in _all_locations(root) if child.id == lid), None)
    if target is None:
        dispatch(state, CloseModal(), rng)
        return
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    offset = depth * 15
    rect = floating_table_rect()
    rect.x += offset
    rect.y += offset
    if depth == 0:
        draw_scrim(layout().stage)
    is_top = lid == state.modal.primary_id
    sections, closed = draw_table_shell(
        font,
        rect,
        title=target.title,
        subtitle=target.description,
        close_label="关闭" if is_top else None,
    )
    if closed and not resolving and is_top:
        dispatch(state, CloseModal(), rng)
        return
    if not is_top:
        return
    location_clocks = present_encounter_location_clocks(state, target.id)
    if location_clocks:
        draw_rendered_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 48), location_clocks)
    _draw_location_contents(font, state, rng, target, sections.content, nested_locations=True)


def _draw_location_contents(font: Font | None, state: GameState, rng, location, content_rect: Rectangle, *, nested_locations: bool) -> None:
    child_ids = tuple(child.id for child in location.children if location_is_visible(child.id, state))
    draw_location_contents(
        font,
        state,
        rng,
        content_rect,
        present_encounter_child_location_cards(state, child_ids),
        present_encounter_action_cards(state, location),
        nested_locations=nested_locations,
    )


def _all_locations(root) -> tuple:
    items = [root]
    for child in root.children:
        items.extend(_all_locations(child))
    return tuple(items)
