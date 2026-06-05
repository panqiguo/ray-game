from __future__ import annotations

from pyray import *  # type: ignore

from sincity.content import GROWTH_DEFS
from sincity.model.state import GameState
from sincity.rules import close_modal, current_action, current_world_snapshot, dismiss_pending_resolution, fast_forward_dialogue, location_is_visible
from sincity.screens.city_presenters import (
    current_world_titles,
    present_action_cards,
    present_child_location_cards,
    present_location_clock_ids,
    present_world_objects,
)
from sincity.screens.table_views import (
    draw_location_contents,
    draw_world_objects,
    floating_table_rect,
    split_desktop_area,
)
from sincity.screens.widgets import (
    begin_layer,
    any_input_pressed,
    draw_card_pile_modal,
    draw_clock_row,
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
from .ui_core import Z_HAND, Z_HUD, Z_LOCATION_MODAL, Z_MESSAGE, Z_WORLD


def draw_city_screen(font: Font | None, state: GameState, rng) -> None:
    if state.pending_resolution is not None and state.pending_resolution.settled and any_input_pressed():
        dismiss_pending_resolution(state)
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    if is_key_pressed(KEY_ESCAPE) and not resolving:
        if not fast_forward_dialogue(state):
            close_modal(state)
    page = layout()
    table_rect, message_rect = split_desktop_area(page.stage)
    begin_layer("world", z=Z_WORLD)
    _draw_world_table(font, state, table_rect, rng)
    end_layer("world")
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
                begin_layer(f"location_table_{i}", z=Z_LOCATION_MODAL)
                _draw_location_table(font, state, rng, depth=i, location_id=frame.primary_id)
                end_layer(f"location_table_{i}")
        begin_layer("location_table_top", z=Z_LOCATION_MODAL + len(state.modal.stacked_frames))
        _draw_location_table(font, state, rng, depth=len(state.modal.stacked_frames))
        end_layer("location_table_top")
    draw_profile_modal(font, state, GROWTH_DEFS)
    draw_dialogue_modal(font, state)
    draw_selected_card_curve_overlay(state)


def _draw_world_table(font: Font | None, state: GameState, rect: Rectangle, rng) -> None:
    snapshot = current_world_snapshot(state)
    world_title, area_title, area_description = current_world_titles(state)
    title = f"{world_title} / {area_title}" if world_title else area_title
    sections, _ = draw_table_shell(
        font,
        rect,
        title=title,
        subtitle=area_description,
    )
    draw_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 48), snapshot.global_clock_ids, state)
    draw_world_objects(font, state, rng, sections.content, present_world_objects(state))


def _draw_location_table(font: Font | None, state: GameState, rng, *, depth: int = 0, location_id: str | None = None) -> None:
    lid = location_id if location_id is not None else state.modal.primary_id
    if lid is None:
        return
    snapshot = current_world_snapshot(state)
    if lid not in snapshot.locations_by_id:
        if location_id is None:
            close_modal(state)
        return
    location = snapshot.locations_by_id[lid]
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
        title=location.title,
        subtitle=location.description,
        close_label="关闭" if is_top else None,
    )
    if closed and not resolving and is_top:
        close_modal(state)
        return
    if not is_top:
        return
    location_clock_ids = present_location_clock_ids(state, lid)
    if location_clock_ids:
        draw_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 48), location_clock_ids, state)
    child_ids = tuple(child.id for child in location.children if location_is_visible(child.id, state))
    draw_location_contents(
        font,
        state,
        rng,
        sections.content,
        present_child_location_cards(state, child_ids),
        present_action_cards(state, location),
    )
