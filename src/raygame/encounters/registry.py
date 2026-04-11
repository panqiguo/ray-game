from __future__ import annotations

from dataclasses import replace

from raygame.content.builders import condition
from raygame.model.defs import ActionDef, Condition, Effect, LocationNode, ProgressClockSpec
from raygame.model.enums import ScreenName

from .defs import CompiledEncounter, EncounterActDef, EncounterDef, EncounterStateDef
from .thug import ENCOUNTER as THUG_ENCOUNTER


def _infer_linked_clock_ids(action: ActionDef) -> tuple[str, ...]:
    clock_ids: list[str] = list(action.linked_clock_ids)
    for effect in _iter_action_effects(action):
        if effect.kind not in {"advance_encounter_clock", "damage_encounter_clock"}:
            continue
        assert isinstance(effect.value, str)
        clock_id, _ = effect.value.split(":")
        if clock_id not in clock_ids:
            clock_ids.append(clock_id)
    return tuple(clock_ids)


def _scope_node(node: LocationNode, act_id: str, state: EncounterStateDef) -> LocationNode:
    scoped_conditions = node.conditions + (
        condition("in_encounter_act", act_id),
        condition("in_encounter_state", state.id),
    )
    scoped_actions = tuple(_scope_action(action, act_id, state.id) for action in node.actions)
    scoped_children = tuple(_scope_node(child, act_id, state) for child in node.children)
    return replace(
        node,
        title=node.title or state.title,
        description=node.description or state.description,
        actions=scoped_actions,
        children=scoped_children,
        conditions=scoped_conditions,
    )


def _scope_action(action: ActionDef, act_id: str, state_id: str) -> ActionDef:
    return replace(
        action,
        screen=ScreenName.ENCOUNTER,
        linked_clock_ids=_infer_linked_clock_ids(action),
        conditions=action.conditions
        + (
            condition("in_encounter_act", act_id),
            condition("in_encounter_state", state_id),
        ),
    )


def _iter_action_effects(action: ActionDef) -> tuple[Effect, ...]:
    effects = list(action.effects)
    if action.check is not None:
        effects.extend(action.check.success.effects)
        effects.extend(action.check.cost.effects)
        effects.extend(action.check.fail.effects)
    return tuple(effects)


def _validate_condition_bundle(
    conditions: tuple[Condition, ...],
    *,
    acts_by_id: dict[str, EncounterActDef],
    clocks_by_id: dict[str, ProgressClockSpec],
) -> None:
    state_ids = {state.id for act in acts_by_id.values() for state in act.states}
    for item in conditions:
        if item.kind == "in_encounter_act":
            assert isinstance(item.value, str) and item.value in acts_by_id, f"Unknown encounter act condition target: {item.value}"
        elif item.kind == "in_encounter_state":
            assert isinstance(item.value, str) and item.value in state_ids, f"Unknown encounter state condition target: {item.value}"
        elif item.kind == "encounter_clock_at_least":
            assert isinstance(item.value, str)
            clock_id, _ = item.value.split(":")
            assert clock_id in clocks_by_id, f"Unknown encounter clock condition target: {clock_id}"
        elif item.kind == "encounter_flag":
            assert isinstance(item.value, str) and item.value, "Encounter flag condition must be a non-empty string"


def _validate_effect_bundle(
    effects: tuple[Effect, ...],
    *,
    acts_by_id: dict[str, EncounterActDef],
    clocks_by_id: dict[str, ProgressClockSpec],
    location_ids: set[str],
    action_ids: set[str],
    current_act_id: str,
) -> None:
    active_act_id = current_act_id
    for effect in effects:
        if effect.kind == "set_encounter_act":
            assert isinstance(effect.value, str) and effect.value in acts_by_id, f"Unknown encounter act target: {effect.value}"
            active_act_id = effect.value
        elif effect.kind == "set_encounter_state":
            assert isinstance(effect.value, str)
            target_states = {state.id for state in acts_by_id[active_act_id].states}
            assert effect.value in target_states, f"Unknown encounter state target for act {active_act_id}: {effect.value}"
        elif effect.kind == "finish_encounter":
            assert effect.value in {"success", "fail", "abort"}, f"Unsupported finish_encounter outcome: {effect.value}"
        elif effect.kind in {"advance_encounter_clock", "damage_encounter_clock"}:
            assert isinstance(effect.value, str)
            clock_id, _ = effect.value.split(":")
            assert clock_id in clocks_by_id, f"Unknown encounter clock target: {clock_id}"
        elif effect.kind == "set_encounter_flag":
            assert isinstance(effect.value, str) and effect.value, "Encounter flag must be a non-empty string"
        elif effect.kind in {"hide_location", "reveal_location"}:
            assert isinstance(effect.value, str)
            assert effect.value in location_ids, f"Unknown encounter location target: {effect.value}"
        elif effect.kind == "hide_action":
            assert isinstance(effect.value, str)
            assert effect.value in action_ids, f"Unknown encounter action target: {effect.value}"


def _walk_locations(root: LocationNode) -> tuple[LocationNode, ...]:
    items = [root]
    for child in root.children:
        items.extend(_walk_locations(child))
    return tuple(items)


def compile_encounter(encounter: EncounterDef) -> CompiledEncounter:
    assert encounter.acts, f"Encounter has no acts: {encounter.id}"
    acts_by_id: dict[str, EncounterActDef] = {}
    states_by_key: dict[tuple[str, str], EncounterStateDef] = {}
    root_by_state: dict[tuple[str, str], str] = {}
    locations_by_id: dict[str, LocationNode] = {}
    parent_by_id: dict[str, str | None] = {}
    actions_by_id: dict[str, ActionDef] = {}
    actions_by_location: dict[str, tuple[str, ...]] = {}
    clocks_by_id: dict[str, ProgressClockSpec] = {}
    transitions_by_act: dict[str, tuple] = {}

    def walk(node: LocationNode, parent_id: str | None, depth: int) -> None:
        assert depth <= 2, f"Encounter location nesting exceeds 2: {node.id}"
        assert node.id not in locations_by_id, f"Duplicate encounter location id: {node.id}"
        locations_by_id[node.id] = node
        parent_by_id[node.id] = parent_id
        actions_by_location[node.id] = tuple(action.id for action in node.actions)
        for action in node.actions:
            assert action.id not in actions_by_id, f"Duplicate encounter action id: {action.id}"
            actions_by_id[action.id] = action
        for child in node.children:
            walk(child, node.id, depth + 1)

    for act in encounter.acts:
        assert act.id not in acts_by_id, f"Duplicate encounter act id: {act.id}"
        acts_by_id[act.id] = act
        transitions_by_act[act.id] = act.transitions
        assert act.objective_clock.id not in clocks_by_id, f"Duplicate encounter clock id: {act.objective_clock.id}"
        clocks_by_id[act.objective_clock.id] = act.objective_clock
        for spec in act.clocks:
            assert spec.id not in clocks_by_id, f"Duplicate encounter clock id: {spec.id}"
            clocks_by_id[spec.id] = spec
        state_ids = {state.id for state in act.states}
        assert act.initial_state_id in state_ids, f"Missing initial state {act.initial_state_id} for act {act.id}"
        for state in act.states:
            state_key = (act.id, state.id)
            assert state_key not in states_by_key, f"Duplicate encounter state key: {state_key}"
            scoped_root = _scope_node(state.root, act.id, state)
            scoped_state = replace(state, root=scoped_root)
            states_by_key[state_key] = scoped_state
            root_by_state[state_key] = scoped_root.id
            walk(scoped_root, None, 0)

    assert encounter.initial_act_id in acts_by_id, f"Missing initial act {encounter.initial_act_id} for encounter {encounter.id}"

    all_location_ids = set(locations_by_id)
    all_action_ids = set(actions_by_id)

    for act in encounter.acts:
        for transition in act.transitions:
            if transition.kind in {"clock_full", "clock_empty"}:
                assert transition.source in clocks_by_id, f"Unknown encounter clock source: {transition.source}"
            else:
                raise AssertionError(f"Unsupported encounter transition kind: {transition.kind}")
            _validate_effect_bundle(
                transition.effects,
                acts_by_id=acts_by_id,
                clocks_by_id=clocks_by_id,
                location_ids=all_location_ids,
                action_ids=all_action_ids,
                current_act_id=act.id,
            )

    for act in encounter.acts:
        for state in act.states:
            for node in _walk_locations(state.root):
                _validate_condition_bundle(node.conditions, acts_by_id=acts_by_id, clocks_by_id=clocks_by_id)
                for action in node.actions:
                    _validate_condition_bundle(action.conditions, acts_by_id=acts_by_id, clocks_by_id=clocks_by_id)
                    _validate_effect_bundle(
                        _iter_action_effects(action),
                        acts_by_id=acts_by_id,
                        clocks_by_id=clocks_by_id,
                        location_ids=all_location_ids,
                        action_ids=all_action_ids,
                        current_act_id=act.id,
                    )

    _validate_effect_bundle(
        encounter.rewards,
        acts_by_id=acts_by_id,
        clocks_by_id=clocks_by_id,
        location_ids=all_location_ids,
        action_ids=all_action_ids,
        current_act_id=encounter.initial_act_id,
    )
    _validate_effect_bundle(
        encounter.fail_effects,
        acts_by_id=acts_by_id,
        clocks_by_id=clocks_by_id,
        location_ids=all_location_ids,
        action_ids=all_action_ids,
        current_act_id=encounter.initial_act_id,
    )

    return CompiledEncounter(
        id=encounter.id,
        title=encounter.title,
        description=encounter.description,
        initial_act_id=encounter.initial_act_id,
        acts_by_id=acts_by_id,
        root_by_state=root_by_state,
        states_by_key=states_by_key,
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        clocks_by_id=clocks_by_id,
        transitions_by_act=transitions_by_act,
        rewards=encounter.rewards,
        fail_effects=encounter.fail_effects,
    )


RAW_ENCOUNTERS = (THUG_ENCOUNTER,)
ENCOUNTERS_BY_ID = {encounter.id: compile_encounter(encounter) for encounter in RAW_ENCOUNTERS}


def get_encounter(encounter_id: str) -> CompiledEncounter:
    return ENCOUNTERS_BY_ID[encounter_id]
