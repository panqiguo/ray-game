from __future__ import annotations

from sincity.encounters import get_encounter
from sincity.model.defs import ActionDef, InputRequirement
from sincity.model.enums import ScreenName
from sincity.model.state import GameState
from sincity.game.fields import field_value
from sincity.game.queries import current_encounter_snapshot, current_world_snapshot, get_clock_value, location_for_action


def _current_content(state: GameState):
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        return current_encounter_snapshot(state)
    return current_world_snapshot(state)


def all_met(conditions, state: GameState) -> bool:
    return all(evaluate_condition(condition, state) for condition in conditions)


def evaluate_condition(item, state: GameState) -> bool:
    value = item.value
    if item.kind == "has_item":
        assert isinstance(value, str)
        key, _, raw = value.partition(":")
        amount = int(raw) if raw else 1
        return int(field_value(state, key)) >= amount
    if item.kind == "field_at_least":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        return int(field_value(state, key)) >= int(raw)
    if item.kind == "field_below":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        return int(field_value(state, key)) < int(raw)
    if item.kind == "field_equals":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        expected: int | bool | str
        if raw == "true":
            expected = True
        elif raw == "false":
            expected = False
        elif raw == "nil":
            expected = ""
        else:
            try:
                expected = int(raw)
            except ValueError:
                expected = raw
        return field_value(state, key) == expected
    if item.kind == "field_truthy":
        assert isinstance(value, str)
        return bool(field_value(state, value))
    if item.kind == "inventory_below":
        assert isinstance(value, str)
        item_id, raw = value.split(":")
        return state.world.inventory.get(item_id, 0) < int(raw)
    if item.kind == "clock_at_least":
        assert isinstance(value, str)
        clock_id, raw = value.split(":")
        return get_clock_value(state, clock_id) >= int(raw)
    if item.kind == "clock_hidden":
        assert isinstance(value, str)
        if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None and value in get_encounter(state.active_encounter.encounter_id).clocks_by_id:
            return value not in state.active_encounter.clocks
        return not state.world.progress_clocks[value].visible
    if item.kind == "in_encounter_act":
        return False
    if item.kind == "in_encounter_state":
        return False
    if item.kind == "encounter_flag":
        assert isinstance(value, str)
        return state.active_encounter is not None and bool(state.active_encounter.store.get(value, False))
    if item.kind == "encounter_clock_at_least":
        assert isinstance(value, str)
        clock_id, raw = value.split(":")
        return state.active_encounter is not None and int(state.active_encounter.store.get(clock_id, 0)) >= int(raw)
    raise AssertionError(f"Unsupported condition kind: {item.kind}")


def action_is_visible(action: ActionDef, state: GameState) -> bool:
    content = _current_content(state)
    if action.id not in content.actions_by_id:
        return False
    location_id = location_for_action(action.id, state)
    if location_id is not None and not location_is_visible(location_id, state):
        return False
    return True


def location_is_visible(location_id: str, state: GameState) -> bool:
    content = _current_content(state)
    if location_id not in content.locations_by_id:
        return False
    if location_id == content.root_location_id:
        return True
    parent_id = content.parent_by_id[location_id]
    if parent_id is not None and not location_is_visible(parent_id, state):
        return False
    return True


def location_is_available(location_id: str, state: GameState) -> bool:
    if not location_is_visible(location_id, state):
        return False
    content = _current_content(state)
    location = content.locations_by_id[location_id]
    return all_met(location.conditions, state)


# ── Action availability (部分依赖 deck/slot 模块) ───────────────────

def action_is_available(action: ActionDef, state: GameState) -> bool:
    from sincity.game.encounters import _sync_encounter_action_cycle
    _sync_encounter_action_cycle(state)
    return action_is_visible(action, state) and all_met(action.conditions, state) and requirements_affordable(action.inputs, state)


def requirements_affordable(inputs: tuple[InputRequirement, ...], state: GameState) -> bool:
    from sincity.game.actions import _all_spirit_slots, slot_is_available
    for requirement in inputs:
        if requirement.kind == "card":
            if requirement.key == "any" and not any(slot_is_available(state, slot_id) for slot_id in _all_spirit_slots(state)):
                return False
            if requirement.key == "negative":
                return False
        elif requirement.kind == "item":
            from sincity.game.fields import field_value
            if int(field_value(state, requirement.key)) < requirement.amount:
                return False
        else:
            raise AssertionError(f"Unsupported input kind: {requirement.kind}")
    return True
