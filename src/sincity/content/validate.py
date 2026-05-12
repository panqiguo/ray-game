from __future__ import annotations

from sincity.dialogues import DIALOGUES_BY_ID
from sincity.content.runtime import render_world
from sincity.encounters import ENCOUNTERS_BY_ID, initial_store, render_encounter, validate_encounter_program
from sincity.content.cards import CARD_DEFS
from sincity.content.growth import GROWTH_DEFS
from sincity.content.city_1 import SCENARIO
from sincity.model.defs import ActionDef, Condition, Effect, InputRequirement, LocationNode, ProgressClockSpec


VALID_CONDITIONS = {
    "has_item",
    "field_at_least",
    "field_truthy",
    "inventory_below",
    "clock_at_least",
    "clock_hidden",
    "in_encounter_act",
    "in_encounter_state",
    "encounter_flag",
    "encounter_clock_at_least",
}

WORLD_EFFECTS = {
    "set_field",
    "add_field",
    "shift_clock",
    "reset_hand",
    "upgrade_spirit_value",
    "add_spirit_slot",
    "advance_day",
    "end_game",
    "start_encounter",
    "start_dialogue",
    "start_quick_dialogue",
}

ENCOUNTER_EFFECTS = {
    "set_field",
    "add_field",
    "shift_clock",
    "reset_hand",
    "start_dialogue",
    "start_quick_dialogue",
    "end_encounter",
}

ENCOUNTER_COMPLETION_EFFECTS = {
    "set_field",
    "add_field",
    "shift_clock",
    "reset_hand",
    "upgrade_spirit_value",
    "add_spirit_slot",
    "advance_day",
    "end_game",
    "start_encounter",
    "start_dialogue",
    "start_quick_dialogue",
}

LEGACY_EFFECTS = {
    "change_health",
    "change_energy",
    "change_stress",
    "advance_clock",
    "set_encounter_store",
    "advance_encounter_clock",
    "damage_encounter_clock",
}


def _validate_condition(item: Condition) -> None:
    assert item.kind in VALID_CONDITIONS, f"Unknown condition kind: {item.kind}"


def _validate_effect(item: Effect, *, context: str) -> None:
    allowed = {
        "world": WORLD_EFFECTS,
        "encounter": ENCOUNTER_EFFECTS,
        "encounter_completion": ENCOUNTER_COMPLETION_EFFECTS,
        "legacy": LEGACY_EFFECTS,
    }[context]
    assert item.kind in allowed, f"Effect `{item.kind}` is not allowed in {context} context"
    if item.kind == "start_dialogue":
        assert isinstance(item.value, str) and item.value in DIALOGUES_BY_ID, f"Unknown dialogue id: {item.value}"
    if item.kind == "start_quick_dialogue":
        assert isinstance(item.value, str) and item.value.strip(), "Quick dialogue text cannot be empty"
    if item.kind == "start_encounter":
        assert isinstance(item.value, str) and item.value in ENCOUNTERS_BY_ID, f"Unknown encounter id: {item.value}"
    if item.kind == "end_game":
        assert item.value is True or (
            isinstance(item.value, tuple)
            and len(item.value) == 2
            and all(isinstance(part, str) and part.strip() for part in item.value)
        ), "end_game should be true or carry title/body text"


def _validate_input(item: InputRequirement) -> None:
    assert item.kind in {"card", "item"}, f"Unknown input kind: {item.kind}"
    assert item.amount >= 1, f"Input amount must be >= 1: {item}"


def _validate_action(action: ActionDef, *, context: str) -> None:
    for condition in action.conditions:
        _validate_condition(condition)
    for item in action.inputs:
        _validate_input(item)
    for effect in action.effects:
        _validate_effect(effect, context=context)
    if action.check is not None:
        for outcome in (action.check.success, action.check.cost, action.check.fail):
            for effect in outcome.effects:
                _validate_effect(effect, context=context)


def _validate_clock(spec: ProgressClockSpec) -> None:
    assert spec.segments >= 1, f"Clock segments must be >= 1: {spec.id}"
    last = 0
    for threshold in spec.thresholds:
        assert 1 <= threshold.at <= spec.segments, f"Threshold out of range: {spec.id}"
        assert threshold.at > last, f"Thresholds must be increasing: {spec.id}"
        last = threshold.at
        for effect in threshold.effects:
            _validate_effect(effect, context="legacy")


def validate_content() -> None:
    for card_id, card in CARD_DEFS.items():
        assert card.id == card_id
    for growth_id, growth in GROWTH_DEFS.items():
        assert growth.id == growth_id
        for condition in growth.conditions:
            _validate_condition(condition)
        for effect in growth.effects:
            _validate_effect(effect, context="encounter_completion")
    snapshot = render_world(SCENARIO, _validation_state())
    for location_id, location in snapshot.locations_by_id.items():
        assert location.id == location_id
        _validate_location(location)
    for action_id, action in snapshot.actions_by_id.items():
        assert action.id == action_id
        _validate_action(action, context="world")
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
            _validate_action(action, context="encounter")
        for clock_id, spec in encounter.clocks_by_id.items():
            assert spec.id == clock_id
            _validate_clock(spec)
        for effect in encounter.rewards:
            _validate_effect(effect, context="encounter_completion")
        for effect in encounter.fail_effects:
            _validate_effect(effect, context="encounter_completion")


def _validate_location(location: LocationNode) -> None:
    for condition in location.conditions:
        _validate_condition(condition)


def _validation_state():
    from sincity.model.state import AttributeState, DeckState, GameState, WorldState, ProgressClockState
    return GameState(
        deck=DeckState(),
        attributes=AttributeState(health=SCENARIO.initial_health, stress=SCENARIO.initial_stress),
        world=WorldState(
            progress_clocks={clock_id: ProgressClockState(value=0, visible=True) for clock_id in SCENARIO.clocks_by_id},
            inventory={
                **dict(SCENARIO.initial_inventory),
                "money": SCENARIO.initial_money,
                "cigarettes": SCENARIO.initial_cigarettes,
            },
            values=dict(SCENARIO.initial_values),
        ),
    )
