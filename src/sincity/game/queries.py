from __future__ import annotations

from sincity.content import SCENARIO
from sincity.content.runtime import render_world
from sincity.encounters import get_encounter, render_encounter, evaluate_reaction_die
from sincity.model.defs import ActionDef, ProgressClockSpec
from sincity.model.enums import ScreenName
from sincity.model.state import GameState, ProgressClockState


def _current_content(state: GameState):
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        return current_encounter_snapshot(state)
    return current_world_snapshot(state)


def get_action(action_id: str) -> ActionDef:
    from sincity.game.session import start_new_run
    state, _ = start_new_run(0)
    return current_world_snapshot(state).actions_by_id[action_id]


def get_action_for_state(state: GameState, action_id: str) -> ActionDef | None:
    return _current_content(state).actions_by_id.get(action_id)


def current_world_snapshot(state: GameState):
    cache = state.render_cache
    if cache.world_revision == cache.revision and cache.world_snapshot is not None:
        return cache.world_snapshot
    snapshot = render_world(SCENARIO, state)
    cache.world_snapshot = snapshot
    cache.world_revision = cache.revision
    return snapshot


def current_encounter_snapshot(state: GameState):
    assert state.active_encounter is not None
    cache = state.render_cache
    encounter_id = state.active_encounter.encounter_id
    if cache.encounter_revision == cache.revision and cache.encounter_id == encounter_id and cache.encounter_snapshot is not None:
        return cache.encounter_snapshot
    encounter = get_encounter(state.active_encounter.encounter_id)
    snapshot = render_encounter(encounter, state.active_encounter.store)
    cache.encounter_snapshot = snapshot
    cache.encounter_revision = cache.revision
    cache.encounter_id = encounter_id
    return snapshot


def current_encounter_reaction_table(state: GameState):
    if state.screen != ScreenName.ENCOUNTER or state.active_encounter is None:
        return None
    encounter = get_encounter(state.active_encounter.encounter_id)
    return evaluate_reaction_die(encounter, state.active_encounter.store)


def get_clock_value(state: GameState, clock_id: str) -> int:
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        nested = current_encounter_snapshot(state).nested_clocks_by_id.get(clock_id)
        if nested is not None:
            return nested.value
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None and clock_id in get_encounter(state.active_encounter.encounter_id).clocks_by_id:
        raw = state.active_encounter.store[clock_id]
        assert isinstance(raw, int)
        return raw
    clock_state = state.world.progress_clocks.get(clock_id)
    assert clock_state is not None, f"Missing world progress clock: {clock_id}"
    return clock_state.value


def get_clock_spec_for_state(state: GameState, clock_id: str):
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        nested = current_encounter_snapshot(state).nested_clocks_by_id.get(clock_id)
        if nested is not None:
            return ProgressClockSpec(id=clock_id, title=nested.title, description=nested.description, segments=nested.maximum)
        encounter = get_encounter(state.active_encounter.encounter_id)
        if clock_id in encounter.clocks_by_id:
            return encounter.clocks_by_id[clock_id]
    return SCENARIO.clocks_by_id[clock_id]


def sync_world_progress_clocks(state: GameState) -> None:
    for clock_id, spec in SCENARIO.clocks_by_id.items():
        state.world.progress_clocks.setdefault(clock_id, ProgressClockState(value=spec.initial, visible=True))


def location_for_action(action_id: str, state: GameState) -> str | None:
    content = _current_content(state)
    for location_id, action_ids in content.actions_by_location.items():
        if action_id in action_ids:
            return location_id
    raise AssertionError(f"Unknown action owner: {action_id}")
