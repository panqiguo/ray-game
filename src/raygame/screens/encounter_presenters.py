from __future__ import annotations

from raygame.encounters import get_encounter, render_encounter
from raygame.model.defs import LocationNode
from raygame.model.state import GameState

from .table_presenters import PresentedActionCard, PresentedLocationCard, present_action_cards_for_location, present_location_cards


def _snapshot(state: GameState):
    assert state.active_encounter is not None
    encounter = get_encounter(state.active_encounter.encounter_id)
    return render_encounter(encounter, state.active_encounter.store)


def current_encounter_root(state: GameState) -> LocationNode:
    return _snapshot(state).root.root


def present_encounter_child_location_cards(state: GameState, location_ids: tuple[str, ...]) -> tuple[PresentedLocationCard, ...]:
    return present_location_cards(state, _snapshot(state), location_ids)


def present_encounter_action_cards(state: GameState, location: LocationNode) -> tuple[PresentedActionCard, ...]:
    return present_action_cards_for_location(state, _snapshot(state), location)


def current_encounter_clock_ids(state: GameState) -> tuple[str, ...]:
    snapshot = _snapshot(state)
    return snapshot.shown_clock_ids_by_scene.get(snapshot.root.root.id, ())


def current_encounter_titles(state: GameState) -> tuple[str, str, str]:
    snapshot = _snapshot(state)
    return snapshot.title, snapshot.root.root.title, snapshot.root.root.description
