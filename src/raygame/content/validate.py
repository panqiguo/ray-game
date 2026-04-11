from __future__ import annotations

from raygame.encounters import ENCOUNTERS_BY_ID, initial_store, render_encounter, validate_encounter_program
from raygame.content.cards import CARD_DEFS
from raygame.content.growth import GROWTH_DEFS
from raygame.content.scenario_escape import SCENARIO
from raygame.model.defs import ActionDef, Condition, Effect, InputRequirement, LocationNode, ProgressClockSpec


VALID_CONDITIONS = {
    "has_item",
    "inventory_below",
    "clock_at_least",
    "clock_hidden",
    "location_visible",
    "in_encounter_act",
    "in_encounter_state",
    "encounter_flag",
    "encounter_clock_at_least",
}

VALID_EFFECTS = {
    "change_health",
    "change_stress",
    "change_resource",
    "give_item",
    "remove_item",
    "advance_clock",
    "reveal_location",
    "hide_location",
    "hide_action",
    "show_clock",
    "hide_clock",
    "reset_hand",
    "advance_day",
    "end_run",
    "start_encounter",
    "set_encounter_store",
    "advance_encounter_clock",
    "damage_encounter_clock",
    "finish_encounter",
}


def _validate_condition(item: Condition) -> None:
    assert item.kind in VALID_CONDITIONS, f"Unknown condition kind: {item.kind}"


def _validate_effect(item: Effect) -> None:
    assert item.kind in VALID_EFFECTS, f"Unknown effect kind: {item.kind}"


def _validate_input(item: InputRequirement) -> None:
    assert item.kind in {"card", "resource", "item"}, f"Unknown input kind: {item.kind}"
    assert item.amount >= 1, f"Input amount must be >= 1: {item}"


def _validate_action(action: ActionDef) -> None:
    for condition in action.conditions:
        _validate_condition(condition)
    for item in action.inputs:
        _validate_input(item)
    for effect in action.effects:
        _validate_effect(effect)
    if action.check is not None:
        for outcome in (action.check.success, action.check.cost, action.check.fail):
            for effect in outcome.effects:
                _validate_effect(effect)


def _validate_clock(spec: ProgressClockSpec) -> None:
    assert spec.segments >= 1, f"Clock segments must be >= 1: {spec.id}"
    last = 0
    for threshold in spec.thresholds:
        assert 1 <= threshold.at <= spec.segments, f"Threshold out of range: {spec.id}"
        assert threshold.at > last, f"Thresholds must be increasing: {spec.id}"
        last = threshold.at
        for effect in threshold.effects:
            _validate_effect(effect)


def validate_content() -> None:
    for card_id, card in CARD_DEFS.items():
        assert card.id == card_id
    for growth_id, growth in GROWTH_DEFS.items():
        assert growth.id == growth_id
    for location_id, location in SCENARIO.locations_by_id.items():
        assert location.id == location_id
        _validate_location(location)
    for action_id, action in SCENARIO.actions_by_id.items():
        assert action.id == action_id
        _validate_action(action)
    for clock_id, spec in SCENARIO.clocks_by_id.items():
        assert spec.id == clock_id
        _validate_clock(spec)
    for encounter_id, encounter in ENCOUNTERS_BY_ID.items():
        assert encounter.id == encounter_id
        validate_encounter_program(encounter)
        snapshot = render_encounter(encounter, initial_store(encounter))
        for location_id, location in snapshot.locations_by_id.items():
            assert location.id == location_id
            _validate_location(location)
        for action_id, action in snapshot.actions_by_id.items():
            assert action.id == action_id
            _validate_action(action)
        for clock_id, spec in encounter.clocks_by_id.items():
            assert spec.id == clock_id
            _validate_clock(spec)


def _validate_location(location: LocationNode) -> None:
    for condition in location.conditions:
        _validate_condition(condition)
