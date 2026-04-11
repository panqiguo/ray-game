from __future__ import annotations

from raygame.encounters import get_encounter
from raygame.model.defs import LocationNode
from raygame.model.state import GameState

from .table_presenters import PresentedActionCard, PresentedLocationCard, present_action_cards_for_location, present_location_cards


def current_encounter_root(state: GameState) -> LocationNode:
    assert state.active_encounter is not None
    encounter = get_encounter(state.active_encounter.encounter_id)
    root_id = encounter.root_by_state[(state.active_encounter.current_act_id, state.active_encounter.current_state_id)]
    return encounter.locations_by_id[root_id]


def present_encounter_child_location_cards(state: GameState, location_ids: tuple[str, ...]) -> tuple[PresentedLocationCard, ...]:
    assert state.active_encounter is not None
    encounter = get_encounter(state.active_encounter.encounter_id)
    return present_location_cards(state, encounter, location_ids)


def present_encounter_action_cards(state: GameState, location: LocationNode) -> tuple[PresentedActionCard, ...]:
    assert state.active_encounter is not None
    encounter = get_encounter(state.active_encounter.encounter_id)
    return present_action_cards_for_location(state, encounter, location)


def current_encounter_clock_ids(state: GameState) -> tuple[str, ...]:
    assert state.active_encounter is not None
    encounter = get_encounter(state.active_encounter.encounter_id)
    act = encounter.acts_by_id[state.active_encounter.current_act_id]
    return (act.objective_clock.id,)


def current_encounter_titles(state: GameState) -> tuple[str, str, str]:
    assert state.active_encounter is not None
    encounter = get_encounter(state.active_encounter.encounter_id)
    act = encounter.acts_by_id[state.active_encounter.current_act_id]
    scene_state = encounter.states_by_key[(state.active_encounter.current_act_id, state.active_encounter.current_state_id)]
    return encounter.title, act.title, scene_state.description
