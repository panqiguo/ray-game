from __future__ import annotations

from pyray import *  # type: ignore

from raygame.content import GROWTH_DEFS, SCENARIO
from raygame.content.runtime import render_world
from raygame.model.state import GameState
from raygame.rules import close_modal, current_action, dismiss_pending_resolution, location_is_visible
from raygame.screens.city_presenters import (
    present_action_cards,
    present_child_location_cards,
    present_location_clock_ids,
    present_world_objects,
)
from raygame.screens.table_views import (
    draw_location_contents,
    draw_world_objects,
    floating_table_rect,
    split_desktop_area,
)
from raygame.screens.widgets import (
    begin_layer,
    any_input_pressed,
    draw_card_pile_modal,
    draw_clock_row,
    draw_dialogue_modal,
    draw_hand,
    draw_message_feed,
    draw_profile_modal,
    draw_scrim,
    draw_table_shell,
    end_layer,
    layout,
)


def draw_city_screen(font: Font | None, state: GameState, rng) -> None:
    if state.pending_resolution is not None and state.pending_resolution.settled and any_input_pressed():
        dismiss_pending_resolution(state)
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    if is_key_pressed(KEY_ESCAPE) and not resolving:
        close_modal(state)
    page = layout()
    table_rect, message_rect = split_desktop_area(page.stage)
    begin_layer("world", interactive=state.modal.kind == "")
    _draw_world_table(font, state, table_rect, rng)
    end_layer("world")
    draw_card_pile_modal(font, state)
    begin_layer("hand", interactive=state.modal.kind in {"", "location"} and not resolving)
    draw_hand(font, state, current_action(state))
    end_layer("hand")
    draw_message_feed(font, message_rect, state)
    if state.modal.kind == "location" and state.modal.primary_id is not None:
        begin_layer("location_table", interactive=True)
        _draw_location_table(font, state, rng)
        end_layer("location_table")
    draw_profile_modal(font, state, GROWTH_DEFS)
    draw_dialogue_modal(font, state)


def _draw_world_table(font: Font | None, state: GameState, rect: Rectangle, rng) -> None:
    snapshot = render_world(SCENARIO, state)
    sections, _ = draw_table_shell(
        font,
        rect,
        title=snapshot.title,
        subtitle="",
    )
    draw_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 48), snapshot.global_clock_ids, state)
    draw_world_objects(font, state, rng, sections.content, present_world_objects(state))


def _draw_location_table(font: Font | None, state: GameState, rng) -> None:
    assert state.modal.primary_id is not None
    snapshot = render_world(SCENARIO, state)
    location = snapshot.locations_by_id[state.modal.primary_id]
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    rect = floating_table_rect()
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
    location_clock_ids = present_location_clock_ids(state, location.id)
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
