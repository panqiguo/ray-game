from __future__ import annotations

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rules import close_modal, current_action, dismiss_pending_resolution, location_is_visible
from raygame.screens.encounter_presenters import (
    current_encounter_clock_ids,
    current_encounter_root,
    current_encounter_titles,
    present_encounter_action_cards,
    present_encounter_child_location_cards,
    present_encounter_location_clock_ids,
)
from raygame.screens.table_views import draw_location_contents, floating_table_rect, split_desktop_area
from raygame.screens.widgets import (
    begin_layer,
    click_pressed,
    consume_click,
    draw_card_pile_modal,
    draw_clock_row,
    draw_hand,
    draw_message_feed,
    draw_profile_modal,
    draw_scrim,
    draw_table_shell,
    end_layer,
    layout,
)


def draw_encounter_screen(font: Font | None, state: GameState, rng) -> None:
    if state.pending_resolution is not None and state.pending_resolution.settled and click_pressed():
        dismiss_pending_resolution(state)
        consume_click()
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    if is_key_pressed(KEY_ESCAPE) and not resolving:
        close_modal(state)
    page = layout()
    table_rect, message_rect = split_desktop_area(page.stage)
    begin_layer("encounter_root", interactive=state.modal.kind == "")
    _draw_encounter_table(font, state, rng, table_rect)
    end_layer("encounter_root")
    draw_card_pile_modal(font, state)
    begin_layer("hand", interactive=state.modal.kind in {"", "location"} and not resolving)
    draw_hand(font, state, current_action(state))
    end_layer("hand")
    draw_message_feed(font, message_rect, state)
    if state.modal.kind == "location" and state.modal.primary_id is not None:
        begin_layer("encounter_location_table", interactive=True)
        _draw_encounter_location_table(font, state, rng)
        end_layer("encounter_location_table")
    draw_profile_modal(font, state)


def _draw_encounter_table(font: Font | None, state: GameState, rng, rect: Rectangle) -> None:
    encounter_title, act_title, state_description = current_encounter_titles(state)
    root = current_encounter_root(state)
    sections, _ = draw_table_shell(
        font,
        rect,
        title=f"{encounter_title} / {act_title}",
        subtitle=state_description or root.description,
    )
    draw_clock_row(
        font,
        Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 26),
        current_encounter_clock_ids(state),
        state,
    )
    _draw_location_contents(font, state, rng, root, sections.content, nested_locations=False)


def _draw_encounter_location_table(font: Font | None, state: GameState, rng) -> None:
    root = current_encounter_root(state)
    assert state.modal.primary_id is not None
    location_id = state.modal.primary_id
    target = next((child for child in _all_locations(root) if child.id == location_id), None)
    if target is None:
        close_modal(state)
        return
    resolving = state.pending_resolution is not None and not state.pending_resolution.settled
    rect = floating_table_rect()
    draw_scrim(layout().stage)
    sections, closed = draw_table_shell(
        font,
        rect,
        title=target.title,
        subtitle=target.description,
        close_label="关闭",
    )
    if closed and not resolving:
        close_modal(state)
        return
    location_clock_ids = present_encounter_location_clock_ids(state, target.id)
    if location_clock_ids:
        draw_clock_row(font, Rectangle(sections.header.x + 18, sections.header.y + 84, sections.header.width - 36, 26), location_clock_ids, state)
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
