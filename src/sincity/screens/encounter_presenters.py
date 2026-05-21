from __future__ import annotations

from sincity.model.defs import LocationNode
from sincity.model.state import GameState
from sincity.rules import current_encounter_snapshot

from .table_presenters import PresentedActionCard, PresentedLocationCard, present_action_cards_for_location, present_location_cards


def _snapshot(state: GameState):
    return current_encounter_snapshot(state)


def current_encounter_root(state: GameState) -> LocationNode:
    return _snapshot(state).root_location


def present_encounter_child_location_cards(state: GameState, location_ids: tuple[str, ...]) -> tuple[PresentedLocationCard, ...]:
    return present_location_cards(state, _snapshot(state), location_ids)


def present_encounter_action_cards(state: GameState, location: LocationNode) -> tuple[PresentedActionCard, ...]:
    return present_action_cards_for_location(state, _snapshot(state), location)


def current_encounter_clock_ids(state: GameState) -> tuple[str, ...]:
    snapshot = _snapshot(state)
    return snapshot.shown_clock_ids_by_scene.get(snapshot.root_location_id, ())


def current_encounter_clocks(state: GameState):
    snapshot = _snapshot(state)
    return snapshot.shown_clocks_by_scene.get(snapshot.root_location_id, ())


def present_encounter_location_clock_ids(state: GameState, location_id: str) -> tuple[str, ...]:
    snapshot = _snapshot(state)
    return snapshot.shown_clock_ids_by_scene.get(location_id, ())


def present_encounter_location_clocks(state: GameState, location_id: str):
    snapshot = _snapshot(state)
    return snapshot.shown_clocks_by_scene.get(location_id, ())


def current_encounter_titles(state: GameState) -> tuple[str, str, str]:
    snapshot = _snapshot(state)
    return snapshot.title, snapshot.root_location.title, snapshot.root_location.description
