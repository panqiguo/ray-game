from __future__ import annotations

import time
from dataclasses import dataclass

from sincity.constants import HAND_SIZE, MAX_LOG_LINES
from sincity.content import DEBUG_COMPANION_ORDER, GROWTH_DEFS, PLAYER_ACTOR_ID, SCENARIO, build_initial_party
from sincity.content.runtime import next_react_rule as next_world_react_rule
from sincity.content.runtime import react_rule_matches as world_react_rule_matches
from sincity.content.runtime import evaluate_world_expr, evaluate_world_react_effects, render_tasks, render_world
from sincity.dialogues import choose_dialogue_option as choose_runtime_dialogue_option
from sincity.dialogues import continue_dialogue_session, create_dialogue_session, create_quick_dialogue_session, get_dialogue
from sincity.encounters import MAX_REACT_STEPS, evaluate_cycle_effects, evaluate_effect_expr, evaluate_fail_effects, evaluate_react_rules, evaluate_reaction_die, evaluate_success_effects, get_encounter, initial_store, next_react_rule, react_rule_matches, render_encounter
from sincity.encounters.defs import CompiledEncounterProgram
from sincity.model.defs import ActionDef, AddFieldPayload, DynamicValue, Effect, FieldRef, InputRequirement, ProgressClockSpec, SetFieldPayload, ShiftClockPayload
from sincity.model.enums import ResultType, ScreenName
from sincity.model.state import (
    ActiveEncounterState,
    ActionAssemblyState,
    ActionResolution,
    AttributeState,
    CardHintFlashState,
    DeckState,
    GameState,
    PendingResolutionState,
    ProgressClockState,
    ModalState,
    SelectedInputState,
    WorldState,
)
from sincity.rules.deck import list_spirit_slots, make_starting_deck, refresh_spirit_slots, start_city_day
from sincity.rules.judgment import compute_action_value, roll_result
from sincity.rules.notifications import push_notification
from sincity.rules.rng import RandomSource
from sincity.model.enums import Suit


@dataclass(frozen=True)
class CheckValuePart:
    label: str
    value: int
    source: str = "environment"
    actor_id: str | None = None


@dataclass(frozen=True)
class CheckValueBreakdown:
    base: int
    actor_part: CheckValuePart | None
    environment_parts: tuple[CheckValuePart, ...]
    total: int


def _push_log(state: GameState, text: str) -> None:
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def start_new_run(seed: int) -> tuple[GameState, RandomSource]:
    rng = RandomSource(seed)
    deck = make_starting_deck(rng)
    world = WorldState(
        progress_clocks={
            clock_id: ProgressClockState(
                value=0,
                visible=True,
            )
            for clock_id in SCENARIO.clocks_by_id
        },
        inventory={
            **dict(SCENARIO.initial_inventory),
            "money": SCENARIO.initial_money,
            "cigarettes": SCENARIO.initial_cigarettes,
        },
        values=dict(SCENARIO.initial_values),
    )
    state = GameState(
        deck=deck,
        attributes=AttributeState(
            health=SCENARIO.initial_health,
            max_health=10,
            stress=SCENARIO.initial_stress,
            max_stress=5,
        ),
        world=world,
        screen=ScreenName.CITY,
        pending_growth_choices=list(SCENARIO.initial_growth_choices),
        growth_points=0,
        seed=seed,
    )
    state.player_actor_id = PLAYER_ACTOR_ID
    state.party = build_initial_party(player_health=state.attributes.health, player_energy=state.attributes.stress)
    state.companion_actor_ids = []
    sync_trauma_cards_with_health(state)
    start_city_day(state.deck, rng, HAND_SIZE, actors=_active_card_actors(state))
    _reset_action_cycle_from_deck(state)
    sync_world_progress_clocks(state)
    _resolve_world_reacts(state, rng, [])
    return state, rng


def get_action(action_id: str) -> ActionDef:
    return current_world_snapshot(_runtime_projection_state()).actions_by_id[action_id]


def get_action_for_state(state: GameState, action_id: str) -> ActionDef | None:
    return _current_content(state).actions_by_id.get(action_id)


def _current_content(state: GameState | None = None):
    if state is not None and state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        return current_encounter_snapshot(state)
    assert state is not None
    return current_world_snapshot(state)


def _runtime_projection_state() -> GameState:
    state, _ = start_new_run(0)
    return state


def _encounter(state: GameState):
    assert state.active_encounter is not None
    return get_encounter(state.active_encounter.encounter_id)


def _encounter_snapshot(state: GameState):
    assert state.active_encounter is not None
    return current_encounter_snapshot(state)


def _current_encounter_root_id(state: GameState) -> str:
    return _encounter_snapshot(state).root_location_id


def _reset_action_cycle_from_deck(state: GameState) -> None:
    state.encounter_pressure_used = False
    state.deck.action_card_bonuses.clear()


def _reset_encounter_action_cycle(state: GameState) -> None:
    _reset_action_cycle_from_deck(state)


def _sync_encounter_action_cycle(state: GameState) -> None:
    if state.screen != ScreenName.ENCOUNTER or state.active_encounter is None:
        return
    root_id = _current_encounter_root_id(state)
    if state.encounter_resource_root_id != root_id:
        state.encounter_resource_root_id = root_id


def encounter_action_cards(state: GameState) -> tuple[int, int] | None:
    if state.screen != ScreenName.ENCOUNTER or state.active_encounter is None:
        return None
    _sync_encounter_action_cycle(state)
    return (len(state.deck.available_slots), len(state.deck.available_slots) + len(state.deck.exhausted_slots))


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
    snapshot = render_encounter(_encounter(state), state.active_encounter.store)
    cache.encounter_snapshot = snapshot
    cache.encounter_revision = cache.revision
    cache.encounter_id = encounter_id
    return snapshot


def current_encounter_reaction_table(state: GameState):
    if state.screen != ScreenName.ENCOUNTER or state.active_encounter is None:
        return None
    return evaluate_reaction_die(_encounter(state), state.active_encounter.store)


def _mark_content_dirty(state: GameState) -> None:
    state.render_cache.revision += 1


def get_clock_value(state: GameState, clock_id: str) -> int:
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        nested = current_encounter_snapshot(state).nested_clocks_by_id.get(clock_id)
        if nested is not None:
            return nested.value
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None and clock_id in _encounter(state).clocks_by_id:
        raw = state.active_encounter.store[clock_id]
        assert isinstance(raw, int)
        return raw
    clock_state = state.world.progress_clocks.get(clock_id)
    assert clock_state is not None, f"Missing world progress clock: {clock_id}"
    return clock_state.value


def sync_world_progress_clocks(state: GameState) -> None:
    for clock_id in SCENARIO.clocks_by_id:
        state.world.progress_clocks.setdefault(clock_id, ProgressClockState(value=0, visible=True))


def get_clock_spec_for_state(state: GameState, clock_id: str):
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        nested = current_encounter_snapshot(state).nested_clocks_by_id.get(clock_id)
        if nested is not None:
            return ProgressClockSpec(id=clock_id, title=nested.title, description=nested.description, segments=nested.maximum)
        encounter = _encounter(state)
        if clock_id in encounter.clocks_by_id:
            return encounter.clocks_by_id[clock_id]
    return SCENARIO.clocks_by_id[clock_id]


def _field_value(state: GameState, key: str) -> int | bool | str:
    if key == "day":
        return state.day
    if state.active_encounter is not None and key in state.active_encounter.store:
        spec = _encounter(state).store_specs[key]
        if spec.persist == "encounter":
            return state.active_encounter.store[key]
        if spec.persist == "world_attr":
            return _world_attr_value(state, key)
        if spec.persist == "world_value":
            return state.world.values.get(key, spec.initial)
        if spec.persist == "world_inventory":
            return state.world.inventory.get(key, int(spec.initial))
    if key in {"energy", "stress", "health", "logic", "perception", "willpower"}:
        return _world_attr_value(state, key)
    if key in state.world.values:
        return state.world.values[key]
    return state.world.inventory.get(key, 0)


def _set_field(state: GameState, key: str, value: int | bool | str, extra_lines: list[str] | None = None) -> None:
    if state.active_encounter is not None and key in state.active_encounter.store:
        spec = _encounter(state).store_specs[key]
        if spec.persist == "encounter":
            current = state.active_encounter.store[key]
            state.active_encounter.store[key] = _coerce_like(current, value)
            _mark_content_dirty(state)
            return
        if spec.persist == "world_attr":
            _set_world_attr(state, key, int(value))
            state.active_encounter.store[key] = _field_value(state, key)
            _mark_content_dirty(state)
            return
        if spec.persist == "world_value":
            current = state.world.values.get(key, spec.initial)
            parsed = _coerce_like(current, value)
            state.world.values[key] = parsed
            state.active_encounter.store[key] = parsed
            _mark_content_dirty(state)
            return
        if spec.persist == "world_inventory":
            count = int(value)
            if count <= 0:
                state.world.inventory.pop(key, None)
            else:
                state.world.inventory[key] = count
            state.active_encounter.store[key] = state.world.inventory.get(key, 0)
            _mark_content_dirty(state)
            return
    if key == "energy":
        _set_world_attr(state, key, int(value))
        _mark_content_dirty(state)
        return
    if hasattr(state.attributes, key):
        if key == "health":
            _set_world_attr(state, key, int(value))
        else:
            setattr(state.attributes, key, int(value))
        _mark_content_dirty(state)
        return
    if key in {"gang_relation", "finance_relation", "police_relation"}:
        state.world.values[key] = max(-3, min(3, int(value)))
        _mark_content_dirty(state)
        return
    if isinstance(value, bool) or key in state.world.values:
        state.world.values[key] = value
        _mark_content_dirty(state)
        return
    count = int(value)
    if count <= 0:
        state.world.inventory.pop(key, None)
    else:
        state.world.inventory[key] = count
    _mark_content_dirty(state)


def _world_attr_value(state: GameState, key: str) -> int:
    actor = _player_actor(state)
    if key == "energy":
        return actor.energy
    if key == "stress":
        return actor.energy
    if key == "health":
        return actor.health
    if key == "logic":
        return actor.logic
    if key == "perception":
        return actor.perception
    if key == "willpower":
        return actor.willpower
    raise AssertionError(f"Unknown world attr: {key}")


def _set_world_attr(state: GameState, key: str, value: int) -> None:
    actor = _player_actor(state)
    if key in {"energy", "stress"}:
        actor.energy = max(0, min(actor.max_energy, value))
        state.attributes.stress = actor.energy
        return
    if key == "health":
        actor.health = max(0, min(actor.max_health, value))
        state.attributes.health = actor.health
        sync_trauma_cards_with_health(state)
        return
    assert key in {"logic", "perception", "willpower"}, f"Unknown world attr: {key}"
    setattr(actor, key, value)


def _add_field(state: GameState, key: str, amount: int, extra_lines: list[str] | None = None) -> None:
    if state.active_encounter is not None and key in state.active_encounter.store:
        current = _field_value(state, key)
        assert isinstance(current, int), f"Cannot add to non-number field `{key}`"
        _set_field(state, key, current + amount, extra_lines)
        return
    if key == "health":
        change_health(state, amount, extra_lines)
        return
    if key == "energy":
        change_energy(state, amount, extra_lines)
        return
    if key == "stress":
        change_energy(state, -amount, extra_lines)
        return
    current = _field_value(state, key)
    _set_field(state, key, int(current) + amount, extra_lines)


def _slot_spirit(slot_id: str) -> str:
    return slot_owner(slot_id)


def slot_owner(slot_id: str) -> str:
    owner, _, _slot_index = slot_id.partition(":")
    assert owner, f"Unknown action card: {slot_id}"
    return owner


def _player_actor(state: GameState):
    actor = state.party.get(state.player_actor_id)
    assert actor is not None, f"Missing player actor: {state.player_actor_id}"
    return actor


def party_actor(state: GameState, actor_id: str):
    actor = state.party.get(actor_id)
    assert actor is not None, f"Unknown party actor: {actor_id}"
    return actor


def actor_name(state: GameState, actor_id: str) -> str:
    return party_actor(state, actor_id).name


def add_next_companion_for_debug(state: GameState, rng: RandomSource | None = None) -> str | None:
    for actor_id in DEBUG_COMPANION_ORDER:
        if actor_id not in state.companion_actor_ids:
            state.companion_actor_ids.append(actor_id)
            _refresh_cards_after_party_change(state, rng)
            _mark_content_dirty(state)
            return actor_name(state, actor_id)
    return None


def remove_companions_for_debug(state: GameState, rng: RandomSource | None = None) -> tuple[str, ...]:
    removed = tuple(actor_name(state, actor_id) for actor_id in state.companion_actor_ids)
    state.companion_actor_ids.clear()
    _refresh_cards_after_party_change(state, rng)
    _mark_content_dirty(state)
    return removed


def _refresh_cards_after_party_change(state: GameState, rng: RandomSource | None = None) -> None:
    if rng is None:
        rng = RandomSource(state.seed)
    clear_assembly(state)
    clear_selected_input(state)
    reset_hand(state, rng)


def _active_card_actors(state: GameState) -> tuple:
    ids = [state.player_actor_id] if state.screen != ScreenName.ENCOUNTER else [state.player_actor_id, *state.companion_actor_ids]
    return tuple(actor for actor_id in ids if (actor := state.party.get(actor_id)) is not None and actor.can_act)


def _all_spirit_slots(state: GameState) -> list[str]:
    return list_spirit_slots(state.deck)


def slot_trauma_count(state: GameState, slot_id: str) -> int:
    return max(0, slot_base_raw_value(state, slot_id) - slot_base_value(state, slot_id))


def slot_base_raw_value(state: GameState, slot_id: str) -> int:
    return state.deck.action_card_values.get(slot_id, 0)


def slot_base_value(state: GameState, slot_id: str) -> int:
    return state.deck.action_card_values.get(slot_id, 0)


def slot_current_value(state: GameState, slot_id: str) -> int:
    return slot_base_value(state, slot_id) + state.deck.action_card_bonuses.get(slot_id, 0)


def slot_is_available(state: GameState, slot_id: str) -> bool:
    if slot_id not in state.deck.available_slots:
        return False
    return True


def slot_is_exhausted(state: GameState, slot_id: str) -> bool:
    return slot_id in state.deck.exhausted_slots


def slot_is_locked(state: GameState, slot_id: str) -> bool:
    return slot_id in state.deck.locked_slots


def slot_is_preferred_for_check(slot_id: str, check) -> bool | None:
    del slot_id, check
    return None


def _actor_attribute_value(state: GameState, owner_id: str, suit: Suit) -> int:
    actor = party_actor(state, owner_id)
    if suit == Suit.LOGIC:
        return actor.logic
    if suit == Suit.PERCEPTION:
        return actor.perception
    if suit == Suit.WILLPOWER:
        return actor.willpower
    return 0


def slot_effective_value(state: GameState, slot_id: str, check) -> int:
    return slot_value_breakdown(state, slot_id, check).total


def slot_value_breakdown(state: GameState, slot_id: str, check) -> CheckValueBreakdown:
    base_value = slot_current_value(state, slot_id)
    owner_id = state.deck.action_card_owners.get(slot_id, slot_owner(slot_id))
    attribute_parts = tuple(
        CheckValuePart(label=f"{actor_name(state, owner_id)} {_suit_label(suit)}", value=_actor_attribute_value(state, owner_id, suit), source="actor", actor_id=owner_id)
        for suit in check.suits
    )
    active_attribute = max(attribute_parts, key=lambda item: item.value, default=None)
    actor_part = active_attribute if active_attribute is not None else None
    environment_parts = tuple(
        CheckValuePart(label=item.label, value=item.value, source="environment")
        for item in getattr(check, "factors", ())
        if item.active and item.value != 0
    )
    raw_total = base_value + (actor_part.value if actor_part is not None else 0) + sum(item.value for item in environment_parts)
    return CheckValueBreakdown(
        base=base_value,
        actor_part=actor_part,
        environment_parts=environment_parts,
        total=compute_action_value(raw_total, check, preferred=None),
    )


def _suit_label(suit: Suit) -> str:
    if suit == Suit.LOGIC:
        return "逻辑"
    if suit == Suit.PERCEPTION:
        return "感知"
    if suit == Suit.WILLPOWER:
        return "意志"
    if suit == Suit.WOUND:
        return "流血"
    if suit == Suit.SHOCK:
        return "惊悸"
    return str(suit)


def _slot_can_execute_check(state: GameState, slot_id: str, check) -> bool:
    _sync_encounter_action_cycle(state)
    if not _slot_can_spend_energy(state, slot_id):
        return False
    return slot_effective_value(state, slot_id, check) > 0


def _slot_can_spend_energy(state: GameState, slot_id: str) -> bool:
    _sync_encounter_action_cycle(state)
    if not slot_is_available(state, slot_id):
        return False
    return True


def _coerce_like(current: int | bool | str, value: int | bool | str) -> int | bool | str:
    if isinstance(current, bool):
        return bool(value)
    if isinstance(current, int):
        return int(value)
    return str(value)


def action_is_visible(action: ActionDef, state: GameState) -> bool:
    content = _current_content(state)
    if action.id not in content.actions_by_id:
        return False
    location_id = location_for_action(action.id, state)
    if location_id is not None and not location_is_visible(location_id, state):
        return False
    return True


def action_is_available(action: ActionDef, state: GameState) -> bool:
    _sync_encounter_action_cycle(state)
    return action_is_visible(action, state) and all_met(action.conditions, state) and requirements_affordable(action.inputs, state)


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


def all_met(conditions, state: GameState) -> bool:
    return all(evaluate_condition(condition, state) for condition in conditions)


def evaluate_condition(item, state: GameState) -> bool:
    value = item.value
    if item.kind == "has_item":
        assert isinstance(value, str)
        key, _, raw = value.partition(":")
        amount = int(raw) if raw else 1
        return int(_field_value(state, key)) >= amount
    if item.kind == "field_at_least":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        return int(_field_value(state, key)) >= int(raw)
    if item.kind == "field_below":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        return int(_field_value(state, key)) < int(raw)
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
        return _field_value(state, key) == expected
    if item.kind == "field_truthy":
        assert isinstance(value, str)
        return bool(_field_value(state, value))
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
        if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None and value in _encounter(state).clocks_by_id:
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


def requirements_affordable(inputs: tuple[InputRequirement, ...], state: GameState) -> bool:
    for requirement in inputs:
        if requirement.kind == "card":
            if requirement.key == "any" and not any(slot_is_available(state, slot_id) for slot_id in _all_spirit_slots(state)):
                return False
            if requirement.key == "negative":
                return False
        elif requirement.kind == "item":
            if int(_field_value(state, requirement.key)) < requirement.amount:
                return False
        else:
            raise AssertionError(f"Unsupported input kind: {requirement.kind}")
    return True


def open_action(state: GameState, action_id: str, modal_kind: str = "action") -> None:
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    state.assembly = ActionAssemblyState(action_id=action_id)
    state.selected_input = SelectedInputState()
    state.modal.kind = modal_kind
    state.modal.primary_id = action_id


def open_modal(state: GameState, kind: str, primary_id: str | None = None) -> None:
    dismiss_pending_resolution(state)
    state.modal.kind = kind
    state.modal.primary_id = primary_id
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    if kind == "location" and primary_id is not None and state.screen == ScreenName.CITY:
        state.world.fresh_locations.discard(primary_id)
    if kind != "action":
        clear_assembly(state)
        clear_selected_input(state)


def open_overlay(state: GameState, kind: str, primary_id: str | None = None) -> None:
    dismiss_pending_resolution(state)
    assert state.modal.kind, "overlay requires an active base modal"
    state.modal.return_kind = state.modal.kind
    state.modal.return_primary_id = state.modal.primary_id
    state.modal.kind = kind
    state.modal.primary_id = primary_id


def clear_assembly(state: GameState) -> None:
    state.assembly = ActionAssemblyState()


def clear_selected_input(state: GameState) -> None:
    state.selected_input = SelectedInputState()


def trigger_card_hint_flash(state: GameState, action: ActionDef, *, duration: float = 0.75) -> None:
    if action.check is None:
        return
    state.card_hint_flash = CardHintFlashState(
        action_id=action.id,
        until_monotonic=time.monotonic() + duration,
    )


def card_hint_flash_active(state: GameState, action: ActionDef | None = None) -> bool:
    flash = state.card_hint_flash
    if flash.until_monotonic <= time.monotonic():
        if flash.action_id or flash.until_monotonic:
            state.card_hint_flash = CardHintFlashState()
        return False
    if action is None:
        return bool(flash.action_id)
    return flash.action_id == action.id


def card_matches_action_check(action: ActionDef | None, card_id: str) -> bool:
    del card_id
    if action is None or action.check is None:
        return False
    return True


def close_modal(state: GameState) -> None:
    dismiss_pending_resolution(state)
    if state.modal.kind == "dialogue":
        _clear_dialogue_modal(state)
        return
    if state.modal.return_kind:
        state.modal.kind = state.modal.return_kind
        state.modal.primary_id = state.modal.return_primary_id
        state.modal.return_kind = ""
        state.modal.return_primary_id = None
        return
    state.modal.kind = ""
    state.modal.primary_id = None
    clear_assembly(state)
    clear_selected_input(state)


def select_card_input(state: GameState, card_id: str, card_index: int | None = None) -> None:
    if state.selected_input.kind == "card" and state.selected_input.key == card_id and state.selected_input.index == card_index:
        clear_selected_input(state)
        return
    state.selected_input = SelectedInputState(kind="card", key=card_id, index=card_index)


def select_item_input(state: GameState, key: str) -> None:
    if state.selected_input.kind == "item" and state.selected_input.key == key:
        clear_selected_input(state)
        return
    state.selected_input = SelectedInputState(kind="item", key=key)


def start_dialogue(state: GameState, dialogue_id: str) -> None:
    asset = get_dialogue(dialogue_id)
    _open_dialogue_session(state, create_dialogue_session(asset, state), primary_id=dialogue_id)
    _push_log(state, f"进入对话：{asset.title}")


def start_quick_dialogue(state: GameState, raw_text: str) -> None:
    session = create_quick_dialogue_session(raw_text)
    _open_dialogue_session(state, session, primary_id="__quick__")
    _push_log(state, f"进入对话：{session.title}")


def _open_dialogue_session(state: GameState, session, *, primary_id: str) -> None:
    state.active_dialogue = session
    if state.modal.kind:
        state.modal.return_kind = state.modal.kind
        state.modal.return_primary_id = state.modal.primary_id
    else:
        state.modal.return_kind = ""
        state.modal.return_primary_id = None
    state.modal.kind = "dialogue"
    state.modal.primary_id = primary_id
    clear_assembly(state)
    clear_selected_input(state)


def continue_dialogue(state: GameState) -> None:
    if state.active_dialogue is None:
        return
    keep_pinned = state.active_dialogue.history_scroll == 0
    continue_dialogue_session(state.active_dialogue)
    if keep_pinned and state.active_dialogue is not None:
        state.active_dialogue.history_scroll = 0
    if state.active_dialogue.finished and state.active_dialogue.auto_close_on_finish:
        finish_dialogue(state)


def fast_forward_dialogue(state: GameState) -> bool:
    if state.active_dialogue is None:
        return False
    while state.active_dialogue is not None and state.active_dialogue.can_continue and not state.active_dialogue.choices:
        continue_dialogue(state)
    if state.active_dialogue is None:
        return True
    if state.active_dialogue.choices:
        return True
    if state.active_dialogue.finished:
        finish_dialogue(state)
        return True
    raise AssertionError(f"Dialogue cannot be advanced or finished: {state.active_dialogue.dialogue_id}")


def choose_dialogue_option(state: GameState, index: int) -> None:
    if state.active_dialogue is None:
        return
    keep_pinned = state.active_dialogue.history_scroll == 0
    choose_runtime_dialogue_option(state.active_dialogue, index)
    if state.active_dialogue is None:
        return
    if keep_pinned and state.active_dialogue is not None:
        state.active_dialogue.history_scroll = 0
    if state.active_dialogue.finished and state.active_dialogue.auto_close_on_finish:
        finish_dialogue(state)


def finish_dialogue(state: GameState) -> None:
    if state.active_dialogue is None:
        return
    _clear_dialogue_modal(state)
    if state.pending_game_over:
        _apply_game_over(
            state,
            title=state.pending_game_over_title,
            body=state.pending_game_over_body,
        )


def _clear_dialogue_modal(state: GameState) -> None:
    state.active_dialogue = None
    state.modal = ModalState()
    clear_assembly(state)
    clear_selected_input(state)


def _apply_game_over(state: GameState, *, title: str, body: str) -> None:
    state.pending_game_over = False
    state.pending_game_over_title = ""
    state.pending_game_over_body = ""
    state.ending_id = "game_over"
    state.ending_title = title
    state.ending_body = body
    state.screen = ScreenName.ENDING
    state.active_encounter = None
    state.active_dialogue = None
    state.pending_resolution = None
    state.modal = ModalState()
    clear_assembly(state)
    clear_selected_input(state)
    _mark_content_dirty(state)


def end_game(state: GameState, *, title: str = "游戏结束", body: str = "") -> None:
    if state.active_dialogue is not None:
        state.pending_game_over = True
        state.pending_game_over_title = title
        state.pending_game_over_body = body
        return
    _apply_game_over(state, title=title, body=body)


def focus_action(state: GameState, action_id: str) -> None:
    if state.assembly.action_id == action_id:
        return
    state.assembly = ActionAssemblyState(action_id=action_id)


def action_slot_ready(state: GameState, action: ActionDef, requirement: InputRequirement | None = None, *, energy_slot: bool = False) -> bool:
    if state.assembly.action_id != action.id:
        return False
    if energy_slot:
        return state.assembly.slotted_card_id is not None
    assert requirement is not None
    return requirement_is_slotted(state, requirement)


def action_can_accept_selected_input(state: GameState, action: ActionDef, requirement: InputRequirement | None = None, *, energy_slot: bool = False) -> bool:
    selected = state.selected_input
    if not selected.kind:
        return False
    if energy_slot:
        card_id = _selected_card_id(state)
        if card_id is None:
            return False
        if action.check is not None:
            return _slot_can_execute_check(state, card_id, action.check)
        if action_requires_energy_slot(action):
            return _slot_can_spend_energy(state, card_id)
        return False
    assert requirement is not None
    if requirement.kind == "item":
        return selected.kind == "item" and selected.key == requirement.key and int(_field_value(state, requirement.key)) >= requirement.amount
    if requirement.kind == "card":
        card_id = _selected_card_id(state)
        if selected.kind != "card" or card_id is None:
            return False
        return requirement.key == "any" and slot_is_available(state, card_id)
    return False


def first_usable_energy_slot(state: GameState, action: ActionDef) -> tuple[str, int] | None:
    if not action_requires_energy_slot(action):
        return None
    best: tuple[str, int] | None = None
    best_value = -1
    for index, slot_id in enumerate(list_spirit_slots(state.deck)):
        if action.check is not None and _slot_can_execute_check(state, slot_id, action.check):
            value = slot_effective_value(state, slot_id, action.check)
            if value > best_value:
                best_value = value
                best = (slot_id, index)
        elif action.check is None and _slot_can_spend_energy(state, slot_id):
            value = slot_current_value(state, slot_id)
            if value > best_value:
                best_value = value
                best = (slot_id, index)
    return best


def toggle_action_energy_slot(state: GameState, action: ActionDef) -> None:
    if state.assembly.action_id == action.id and state.assembly.slotted_card_id is not None:
        state.assembly.slotted_card_id = None
        state.assembly.slotted_card_index = None
        if not state.assembly.slotted_items:
            state.assembly.action_id = None
        return
    selected_card_id = _selected_card_id(state)
    if selected_card_id is not None and action_can_accept_selected_input(state, action, energy_slot=True):
        focus_action(state, action.id)
        state.assembly.slotted_card_id = selected_card_id
        state.assembly.slotted_card_index = state.selected_input.index
        clear_selected_input(state)
        return
    slot = first_usable_energy_slot(state, action)
    if slot is None:
        focus_action(state, action.id)
        trigger_card_hint_flash(state, action)
        return
    focus_action(state, action.id)
    state.assembly.slotted_card_id = slot[0]
    state.assembly.slotted_card_index = slot[1]
    clear_selected_input(state)


def toggle_action_requirement_slot(state: GameState, action: ActionDef, requirement: InputRequirement) -> None:
    if state.assembly.action_id == action.id and requirement_is_slotted(state, requirement):
        if requirement.kind == "item":
            state.assembly.slotted_items.pop(requirement.key, None)
        elif requirement.kind == "card":
            state.assembly.slotted_card_id = None
            state.assembly.slotted_card_index = None
        if not state.assembly.slotted_items and state.assembly.slotted_card_id is None:
            state.assembly.action_id = None
        return
    if action_can_accept_selected_input(state, action, requirement):
        focus_action(state, action.id)
        if requirement.kind == "item":
            state.assembly.slotted_items[requirement.key] = requirement.amount
        elif requirement.kind == "card":
            card_id = _selected_card_id(state)
            assert card_id is not None
            state.assembly.slotted_card_id = card_id
            state.assembly.slotted_card_index = state.selected_input.index
        clear_selected_input(state)
        return
    if requirement.kind == "item":
        amount = _field_value(state, requirement.key)
        if isinstance(amount, int) and amount >= requirement.amount:
            focus_action(state, action.id)
            state.assembly.slotted_items[requirement.key] = requirement.amount
            clear_selected_input(state)
            return


def slot_card(state: GameState, card_id: str) -> None:
    action = current_action(state)
    if action is None:
        return
    requirement = next((item for item in action.inputs if item.kind == "card"), None)
    if requirement is None and action.check is None:
        return
    if requirement is not None and requirement.key == "negative":
        return
    if action.check is not None and not _slot_can_execute_check(state, card_id, action.check):
        return
    if state.assembly.slotted_card_id == card_id and state.assembly.slotted_card_index is not None:
        state.assembly.slotted_card_id = None
        state.assembly.slotted_card_index = None
        return
    if card_id in state.deck.available_slots:
        state.assembly.slotted_card_id = card_id
        state.assembly.slotted_card_index = state.deck.available_slots.index(card_id)


def toggle_requirement_input(state: GameState, requirement: InputRequirement) -> None:
    action = current_action(state)
    if action is None:
        return
    if requirement.kind == "item":
        if state.assembly.slotted_items.get(requirement.key, 0) >= requirement.amount:
            state.assembly.slotted_items.pop(requirement.key, None)
        elif int(_field_value(state, requirement.key)) >= requirement.amount:
            state.assembly.slotted_items[requirement.key] = requirement.amount


def requirement_is_slotted(state: GameState, requirement: InputRequirement) -> bool:
    if requirement.kind == "card":
        if requirement.key == "negative":
            return False
        card_id = _slotted_card_id(state)
        return card_id is not None and slot_is_available(state, card_id)
    if requirement.kind == "item":
        return state.assembly.slotted_items.get(requirement.key, 0) >= requirement.amount
    raise AssertionError(f"Unsupported requirement kind: {requirement.kind}")


def action_ready_to_execute(action: ActionDef, state: GameState) -> bool:
    if not action_is_available(action, state):
        return False
    if action.check is None and not action.effects:
        return False
    for requirement in action.inputs:
        if not requirement_is_slotted(state, requirement):
            return False
    if action.check is not None:
        card_id = _slotted_card_id(state)
        if card_id is None or not _slot_can_execute_check(state, card_id, action.check):
            return False
    elif action_requires_energy_slot(action):
        card_id = _slotted_card_id(state)
        if card_id is None or not _slot_can_spend_energy(state, card_id):
            return False
    return True


def action_requires_energy_slot(action: ActionDef) -> bool:
    return action.check is not None


def current_action(state: GameState) -> ActionDef | None:
    if not state.assembly.action_id:
        return None
    action = get_action_for_state(state, state.assembly.action_id)
    if action is not None:
        return action
    clear_assembly(state)
    clear_selected_input(state)
    if state.modal.kind == "action":
        state.modal.kind = ""
        state.modal.primary_id = None
    return None


def perform_current_action(state: GameState, rng: RandomSource) -> None:
    action = current_action(state)
    assert action is not None
    assert action_ready_to_execute(action, state), f"Action not ready: {action.id}"
    location_id = location_for_action(action.id, state)
    _consume_inputs(state, action)
    if action.check is None:
        if action_requires_energy_slot(action):
            slot_id = _slotted_card_id(state)
            assert slot_id is not None, "energy slot must be slotted before spending energy"
            _consume_energy_from_slot(state, slot_id)
        resolution = ActionResolution(
            action_id=action.id,
            card_id=_slotted_card_id(state),
            result=None,
            die_roll=None,
            value=None,
            text=action.description,
            effect_lines=_describe_effects(action.effects, action.id, state),
        )
        state.pending_resolution = PendingResolutionState(
            resolution=resolution,
            effects=action.effects,
            log_text=f"{action.title}: {action.description}",
            location_id=location_id or "",
        )
    else:
        card_id = _slotted_card_id(state)
        assert card_id is not None
        value = slot_effective_value(state, card_id, action.check)
        _consume_check_resource(state, card_id)
        die_roll = rng.d6()
        result = roll_result(value, die_roll)
        if result == ResultType.SUCCESS:
            outcome = action.check.success
        elif result == ResultType.COST:
            outcome = action.check.cost
        else:
            outcome = action.check.fail
        resolved_effects = action.effects + outcome.effects
        effect_lines = _describe_effects(resolved_effects, action.id, state)
        resolution_text = _compose_resolution_text(result, effect_lines, outcome.text)
        resolution = ActionResolution(
            action_id=action.id,
            card_id=card_id,
            result=result,
            die_roll=die_roll,
            value=value,
            text=resolution_text,
            effect_lines=effect_lines,
        )
        log_text = resolution_text or "，".join(effect_lines[:2])
        state.pending_resolution = PendingResolutionState(
            resolution=resolution,
            effects=resolved_effects,
            log_text=f"{action.title}: {log_text}",
            location_id=location_id or "",
        )
    clear_selected_input(state)


def advance_pending_resolution(state: GameState, rng: RandomSource, dt: float) -> None:
    pending = state.pending_resolution
    if pending is None:
        return
    if not pending.settled:
        previous_screen = state.screen
        previous_encounter_root_id = (
            _current_encounter_root_id(state)
            if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None
            else None
        )
        pending.progress = min(1.0, pending.progress + dt / 0.7)
        if pending.progress >= 1.0:
            _push_log(state, pending.log_text)
            extra_lines = _apply_effects(pending.effects, state, rng)
            if extra_lines:
                merged = list(pending.resolution.effect_lines)
                for line in extra_lines:
                    if line not in merged:
                        merged.append(line)
                pending.resolution.effect_lines = tuple(merged[:6])
            state.last_resolution = pending.resolution
            _check_endings(state)
            if state.modal.kind == "location" and state.modal.primary_id is not None and not location_is_visible(state.modal.primary_id, state):
                close_modal(state)
            pending.settled = True
            if _should_auto_dismiss_pending_resolution(
                state,
                pending,
                previous_screen=previous_screen,
                previous_encounter_root_id=previous_encounter_root_id,
            ):
                dismiss_pending_resolution(state)
        return


def dismiss_pending_resolution(state: GameState) -> None:
    pending = state.pending_resolution
    if pending is None:
        return
    if pending.settled and state.assembly.action_id == pending.resolution.action_id:
        clear_assembly(state)
    state.pending_resolution = None


def _should_auto_dismiss_pending_resolution(
    state: GameState,
    pending: PendingResolutionState,
    *,
    previous_screen: ScreenName,
    previous_encounter_root_id: str | None,
) -> bool:
    if state.screen != previous_screen:
        return True
    if previous_screen == ScreenName.ENCOUNTER:
        if state.active_encounter is None:
            return True
        if get_action_for_state(state, pending.resolution.action_id) is None:
            return True
        if previous_encounter_root_id is not None and _current_encounter_root_id(state) != previous_encounter_root_id:
            return True
        if pending.location_id and not location_is_visible(pending.location_id, state):
            return True
    return False


def _consume_inputs(state: GameState, action: ActionDef) -> None:
    for requirement in action.inputs:
        assert requirement_is_slotted(state, requirement), f"Requirement not slotted: {requirement}"
        if requirement.kind == "item" and requirement.consume:
            _add_field(state, requirement.key, -requirement.amount)
        if requirement.kind == "card" and action.check is None:
            _consume_slotted_card(state)


def _consume_slotted_card(state: GameState) -> None:
    slot_id = state.assembly.slotted_card_id
    if slot_id is None:
        return
    state.deck.action_card_bonuses.pop(slot_id, None)
    if slot_id in state.deck.available_slots:
        state.deck.available_slots.remove(slot_id)
    if slot_id not in state.deck.exhausted_slots:
        state.deck.exhausted_slots.append(slot_id)


def _consume_check_resource(state: GameState, slot_id: str) -> None:
    _consume_energy_from_slot(state, slot_id)


def _consume_energy_from_slot(state: GameState, slot_id: str) -> None:
    assert _slot_can_spend_energy(state, slot_id), f"energy slot cannot spend energy: {slot_id}"
    _sync_encounter_action_cycle(state)
    _consume_slotted_card(state)
    _mark_content_dirty(state)


def _selected_card_id(state: GameState) -> str | None:
    selected = state.selected_input
    if selected.kind != "card":
        return None
    slots = _all_spirit_slots(state)
    if selected.index is not None and 0 <= selected.index < len(slots):
        card_id = slots[selected.index]
        if card_id == selected.key:
            return card_id
    if selected.key in slots:
        return selected.key
    return None


def _slotted_card_id(state: GameState) -> str | None:
    slot_id = state.assembly.slotted_card_id
    if slot_id is None:
        return None
    slots = _all_spirit_slots(state)
    if state.assembly.slotted_card_index is not None and 0 <= state.assembly.slotted_card_index < len(slots):
        if slots[state.assembly.slotted_card_index] == slot_id:
            return slot_id
    if slot_id in slots:
        return slot_id
    return None


def _apply_effects(
    effects: tuple[Effect, ...],
    state: GameState,
    rng: RandomSource,
    extra_lines: list[str] | None = None,
    *,
    resolve_encounter_reacts: bool = True,
) -> tuple[str, ...]:
    derived: list[str] = [] if extra_lines is None else extra_lines
    for item in effects:
        _apply_effect(item, state, rng, derived)
    if resolve_encounter_reacts:
        if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
            _resolve_encounter_reacts(state, rng, derived)
        elif state.screen == ScreenName.CITY:
            _resolve_world_reacts(state, rng, derived)
    _award_completed_tasks(state)
    return tuple(derived)


def _parse_legacy_scalar(raw: str) -> int | bool | str:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "nil":
        return ""
    try:
        return int(raw)
    except ValueError:
        return raw


def _resolve_set_field_payload(value: object, state: GameState) -> tuple[str, int | bool | str]:
    if isinstance(value, SetFieldPayload):
        raw = value.value
        if isinstance(raw, FieldRef):
            return value.target, _field_value(state, raw.name)
        if isinstance(raw, DynamicValue):
            evaluated = _evaluate_dynamic_value(state, raw)
            if isinstance(evaluated, FieldRef):
                return value.target, _field_value(state, evaluated.name)
            if evaluated is None:
                return value.target, ""
            assert isinstance(evaluated, (int, bool, str)), f"Unsupported dynamic set_field value: {evaluated!r}"
            return value.target, evaluated
        if raw is None:
            return value.target, ""
        assert isinstance(raw, (int, bool, str)), f"Unsupported set_field value: {raw!r}"
        return value.target, raw
    assert isinstance(value, str), f"Invalid set_field payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, _parse_legacy_scalar(raw)


def _resolve_add_field_payload(value: object) -> tuple[str, int]:
    if isinstance(value, AddFieldPayload):
        return value.target, value.amount
    assert isinstance(value, str), f"Invalid add_field payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, int(raw)


def _resolve_shift_clock_payload(value: object) -> tuple[str, int]:
    if isinstance(value, ShiftClockPayload):
        return value.target, value.amount
    assert isinstance(value, str), f"Invalid shift_clock payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, int(raw)


def _describe_set_field_payload(value: object, state: GameState) -> tuple[str, str]:
    if isinstance(value, SetFieldPayload):
        raw = value.value
        if isinstance(raw, FieldRef):
            return value.target, str(_field_value(state, raw.name))
        if isinstance(raw, DynamicValue):
            return value.target, str(_evaluate_dynamic_value(state, raw))
        if raw is None:
            return value.target, "nil"
        return value.target, str(raw)
    assert isinstance(value, str), f"Invalid set_field payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, raw


def _evaluate_dynamic_value(state: GameState, value: DynamicValue) -> object:
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        return evaluate_effect_expr(_encounter(state), state.active_encounter.store, value.body)
    return evaluate_world_expr(SCENARIO, state, value.body)


def _apply_effect(item: Effect, state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    value = item.value
    if item.kind == "set_field":
        key, parsed = _resolve_set_field_payload(value, state)
        _set_field(state, key, parsed, extra_lines)
        return
    if item.kind == "add_field":
        key, amount = _resolve_add_field_payload(value)
        _add_field(state, key, amount, extra_lines)
        return
    if item.kind == "copy_field":
        assert isinstance(value, str)
        target, source = value.split(":", 1)
        _set_field(state, target, _field_value(state, source), extra_lines)
        return
    if item.kind == "shift_clock":
        key, amount = _resolve_shift_clock_payload(value)
        shift_clock(state, key, amount, extra_lines)
        return
    if item.kind == "change_health":
        change_health(state, int(value), extra_lines)
        return
    if item.kind == "change_energy":
        change_energy(state, int(value), extra_lines)
        return
    if item.kind == "change_stress":
        change_energy(state, -int(value), extra_lines)
        return
    if item.kind == "advance_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        shift_clock(state, key, int(raw), extra_lines)
        return
    if item.kind == "advance_encounter_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        shift_clock(state, key, int(raw), extra_lines)
        return
    if item.kind == "damage_encounter_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        shift_clock(state, key, -int(raw), extra_lines)
        return
    if item.kind == "set_encounter_store":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        parsed: int | bool | str
        if raw == "true":
            parsed = True
        elif raw == "false":
            parsed = False
        else:
            try:
                parsed = int(raw)
            except ValueError:
                parsed = raw
        _set_field(state, key, parsed, extra_lines)
        return
    if item.kind == "start_encounter":
        assert isinstance(value, str)
        start_encounter(state, value)
        return
    if item.kind == "start_dialogue":
        assert isinstance(value, str)
        start_dialogue(state, value)
        return
    if item.kind == "start_quick_dialogue":
        assert isinstance(value, str)
        start_quick_dialogue(state, value)
        return
    if item.kind == "expr":
        assert state.active_encounter is not None, "Dynamic effect expressions are only supported inside encounters."
        def action_log(message: object) -> None:
            _push_log(state, str(message))

        result = evaluate_effect_expr(_encounter(state), state.active_encounter.store, value, action_log=action_log)
        if isinstance(result, Effect):
            _apply_effect(result, state, rng, extra_lines)
        elif isinstance(result, list) and all(isinstance(entry, Effect) for entry in result):
            _apply_effects(tuple(result), state, rng, extra_lines)
        _mark_content_dirty(state)
        return
    if item.kind == "end_encounter":
        assert isinstance(value, str)
        finish_encounter(state, value, rng, extra_lines)
        return
    if item.kind == "upgrade_spirit_value":
        assert isinstance(value, str)
        spirit, raw = value.split(":", 1)
        _upgrade_spirit_value(state, spirit, int(raw), extra_lines)
        return
    if item.kind == "add_spirit_slot":
        assert isinstance(value, str)
        _add_spirit_slot(state, value, extra_lines)
        return
    if item.kind == "reset_hand":
        reset_hand(state, rng)
        return
    if item.kind == "advance_day":
        state.day += 1
        change_energy(state, -1, extra_lines)
        remaining = state.world.values.get("gang_days_remaining", 0)
        if isinstance(remaining, int) and remaining > 0:
            state.world.values["gang_days_remaining"] = remaining - 1
        _mark_content_dirty(state)
        return
    if item.kind == "end_game":
        if isinstance(value, tuple):
            title, body = value
            end_game(state, title=str(title), body=str(body))
        else:
            end_game(state)
        return
    raise AssertionError(f"Unsupported effect kind: {item.kind}")


def _award_completed_tasks(state: GameState) -> None:
    for task in render_tasks(SCENARIO.get_program(), state):
        if task.kind not in {"主线", "支线"} or not task.completed:
            continue
        if task.title in state.world.rewarded_tasks:
            continue
        state.world.rewarded_tasks.add(task.title)
        state.growth_points += 1
        _push_log(state, f"{task.kind}任务完成：{task.title}，获得 1 点成长。")
        push_notification(state, "success", f"{task.kind}任务完成", f"{task.title}，获得 1 点成长。")


def _resolve_encounter_reacts(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    if state.active_encounter is None or state.screen != ScreenName.ENCOUNTER:
        return
    encounter = _encounter(state)
    blocked_sources: set[str] = set()
    steps = 0
    while state.active_encounter is not None and state.screen == ScreenName.ENCOUNTER:
        blocked_sources = {
            source
            for source in blocked_sources
            if any(rule.source == source and react_rule_matches(encounter, state.active_encounter.store, rule) for rule in evaluate_react_rules(encounter, state.active_encounter.store))
        }
        rule = next_react_rule(encounter, state.active_encounter.store, blocked_sources)
        if rule is None:
            return
        steps += 1
        assert steps <= MAX_REACT_STEPS, f"Encounter react did not converge: {encounter.id}"
        _apply_effects(rule.effects, state, rng, extra_lines, resolve_encounter_reacts=False)
        if state.active_encounter is None or state.screen != ScreenName.ENCOUNTER:
            return
        if react_rule_matches(encounter, state.active_encounter.store, rule):
            blocked_sources.add(rule.source)
        else:
            blocked_sources.discard(rule.source)


def _resolve_world_reacts(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    blocked_sources: set[str] = set()
    steps = 0
    while state.screen == ScreenName.CITY:
        blocked_sources = {
            source
            for source in blocked_sources
            if any(rule.source == source and world_react_rule_matches(SCENARIO, state, rule) for rule in SCENARIO.react_rules)
        }
        rule = next_world_react_rule(SCENARIO, state, blocked_sources)
        if rule is None:
            return
        steps += 1
        assert steps <= MAX_REACT_STEPS, f"World react did not converge: {SCENARIO.id}"
        effects = evaluate_world_react_effects(SCENARIO, state, rule)
        _apply_effects(effects, state, rng, extra_lines, resolve_encounter_reacts=False)
        if world_react_rule_matches(SCENARIO, state, rule):
            blocked_sources.add(rule.source)
        else:
            blocked_sources.discard(rule.source)


def reset_hand(state: GameState, rng: RandomSource) -> None:
    refresh_spirit_slots(state.deck, rng, actors=_active_card_actors(state))
    _reset_action_cycle_from_deck(state)
    _mark_content_dirty(state)


def rest_during_encounter(state: GameState, rng: RandomSource) -> None:
    assert state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None, "Encounter rest is only available during encounters."
    encounter = _encounter(state)
    clear_assembly(state)
    clear_selected_input(state)
    extra_lines: list[str] = []
    change_energy(state, -1)
    if state.screen == ScreenName.ENCOUNTER:
        _apply_effects(evaluate_cycle_effects(encounter, state.active_encounter.store), state, rng, extra_lines)
    if state.screen == ScreenName.ENCOUNTER:
        _resolve_encounter_reaction_die(state, rng, extra_lines)
    if state.screen == ScreenName.ENCOUNTER:
        reset_hand(state, rng)
    cycle_text = f"；{'，'.join(extra_lines[:2])}" if extra_lines else ""
    _push_log(state, f"你短暂休整了一下：精力 -1，重抽行动卡{cycle_text}。")


def _resolve_encounter_reaction_die(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    assert state.active_encounter is not None
    encounter = _encounter(state)
    table = evaluate_reaction_die(encounter, state.active_encounter.store)
    if table is None:
        return
    roll = rng.d6()
    face = next((item for item in table.faces if item.value == roll), None)
    if face is None:
        return
    title = f"反应骰 {roll}：{face.title}"
    _push_log(state, f"{title}。{face.description}" if face.description else f"{title}。")
    if face.title != "空" or face.description or face.effects:
        body = face.description or f"骰面 {roll}"
        push_notification(state, "warning", title, body)
    _apply_effects(face.effects, state, rng, extra_lines)


def can_endure_pressure_during_encounter(state: GameState) -> bool:
    if state.screen != ScreenName.ENCOUNTER or state.active_encounter is None:
        return False
    if state.encounter_pressure_used:
        return False
    if state.attributes.health <= 0:
        return False
    return any(slot_is_available(state, slot_id) for slot_id in state.deck.available_slots)


def endure_pressure_during_encounter(state: GameState, rng: RandomSource) -> None:
    assert state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None, "Encounter pressure is only available during encounters."
    assert not state.encounter_pressure_used, "Encounter pressure can only be used once per cycle."
    assert state.attributes.health > 0, "Encounter pressure requires at least 1 health."
    available_slots = [slot_id for slot_id in state.deck.available_slots if slot_is_available(state, slot_id)]
    assert available_slots, "Encounter pressure requires at least one available action card."
    clear_assembly(state)
    clear_selected_input(state)
    change_health(state, -1)
    target_index = rng.randint(0, len(available_slots) - 1)
    target_slot = available_slots[target_index]
    state.deck.action_card_bonuses[target_slot] = state.deck.action_card_bonuses.get(target_slot, 0) + 1
    state.encounter_pressure_used = True
    _mark_content_dirty(state)
    owner_name = actor_name(state, slot_owner(target_slot))
    card_label = owner_name
    _push_log(state, f"你咬牙承受住压力：生命 -1，{card_label} 的一张行动卡本回合 +1。")
    push_notification(state, "warning", "承受压力", "随机一张可用行动卡本回合 +1。")


def advance_clock(state: GameState, clock_id: str, amount: int = 1, extra_lines: list[str] | None = None) -> None:
    spec = SCENARIO.clocks_by_id[clock_id]
    clock_state = state.world.progress_clocks[clock_id]
    before = clock_state.value
    clock_state.value = max(0, min(spec.segments, clock_state.value + amount))
    clock_state.visible = True
    _mark_content_dirty(state)
    for threshold in spec.thresholds:
        if before < threshold.at <= clock_state.value:
            _apply_effects(threshold.effects, state, RandomSource(state.seed), extra_lines)


def advance_encounter_clock(state: GameState, clock_id: str, amount: int = 1) -> None:
    assert state.active_encounter is not None
    encounter = _encounter(state)
    spec = encounter.clocks_by_id[clock_id]
    current = int(state.active_encounter.store[clock_id])
    state.active_encounter.store[clock_id] = min(spec.segments, current + amount)
    _mark_content_dirty(state)


def damage_encounter_clock(state: GameState, clock_id: str, amount: int = 1) -> None:
    assert state.active_encounter is not None
    current = int(state.active_encounter.store[clock_id])
    state.active_encounter.store[clock_id] = max(0, current - amount)
    _mark_content_dirty(state)


def shift_clock(state: GameState, clock_id: str, amount: int, extra_lines: list[str] | None = None) -> None:
    if state.active_encounter is not None and clock_id in _encounter(state).clocks_by_id:
        if amount >= 0:
            advance_encounter_clock(state, clock_id, amount)
        else:
            damage_encounter_clock(state, clock_id, -amount)
        return
    advance_clock(state, clock_id, amount, extra_lines)


def start_encounter(state: GameState, encounter_id: str) -> None:
    encounter = get_encounter(encounter_id)
    store = _initial_encounter_store(state, encounter)
    state.active_encounter = ActiveEncounterState(
        encounter_id=encounter_id,
        store=store,
    )
    state.screen = ScreenName.ENCOUNTER
    state.modal.kind = ""
    state.modal.primary_id = None
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    clear_assembly(state)
    clear_selected_input(state)
    state.encounter_resource_root_id = ""
    reset_hand(state, RandomSource(state.seed))
    _mark_content_dirty(state)
    _push_log(state, f"进入侦探任务：{encounter.title}")
    _resolve_encounter_reacts(state, RandomSource(state.seed), [])


def _initial_encounter_store(state: GameState, encounter: CompiledEncounterProgram) -> dict[str, int | bool | str]:
    store = initial_store(encounter)
    for key, spec in encounter.store_specs.items():
        if spec.persist == "world_attr":
            store[key] = _world_attr_value(state, key)
        elif spec.persist == "world_inventory":
            store[key] = state.world.inventory.get(key, spec.initial)
        elif spec.persist == "world_value":
            store[key] = state.world.values.get(key, spec.initial)
    return store


def start_encounter_from_dialogue(state: GameState, encounter_id: str) -> None:
    state.active_dialogue = None
    start_encounter(state, encounter_id)


def finish_encounter(state: GameState, outcome: str, rng: RandomSource, extra_lines: list[str] | None = None) -> None:
    if state.active_encounter is None:
        return
    encounter = _encounter(state)
    encounter_store = state.active_encounter.store
    state.active_encounter = None
    state.screen = ScreenName.CITY
    state.modal.kind = ""
    state.modal.primary_id = None
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    clear_assembly(state)
    clear_selected_input(state)
    state.encounter_resource_root_id = ""
    reset_hand(state, rng)
    _mark_content_dirty(state)
    if outcome == "success":
        _apply_effects(evaluate_success_effects(encounter, encounter_store), state, rng, extra_lines)
        _push_log(state, f"{encounter.title}：完成。")
    elif outcome == "fail":
        _apply_effects(evaluate_fail_effects(encounter, encounter_store), state, rng, extra_lines)
        _push_log(state, f"{encounter.title}：失败。")
    else:
        _push_log(state, f"{encounter.title}：中断。")


def finish_encounter_from_dialogue(state: GameState, outcome: str) -> None:
    state.active_dialogue = None
    finish_encounter(state, outcome, RandomSource(state.seed), [])


def change_health(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    actor = _player_actor(state)
    actor.health = max(0, min(actor.max_health, actor.health + amount))
    state.attributes.health = actor.health
    sync_trauma_cards_with_health(state)
    _mark_content_dirty(state)
    if actor.health <= 0:
        state.ending_id = "collapse"
        state.ending_title = "倒下了"
        state.ending_body = "你最终还是没能撑住。"
        state.screen = ScreenName.ENDING


def change_energy(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    actor = _player_actor(state)
    if amount >= 0:
        actor.energy = min(actor.max_energy, actor.energy + amount)
        state.attributes.stress = actor.energy
        _mark_content_dirty(state)
        return
    loss = -amount
    absorbed = min(actor.energy, loss)
    actor.energy -= absorbed
    state.attributes.stress = actor.energy
    overflow = loss - absorbed
    _mark_content_dirty(state)
    if overflow > 0:
        if extra_lines is not None:
            extra_lines.append(f"精力不足，生命 -{overflow}")
        change_health(state, -overflow, extra_lines)
        _push_log(state, "精力耗尽，身体替你付了代价。")


def change_stress(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    change_energy(state, -amount, extra_lines)


def sync_trauma_cards_with_health(state: GameState) -> None:
    state.deck.trauma_by_slot.clear()


def count_spirit_cards(state: GameState) -> dict[str, int]:
    return {
        spirit: 1 + state.deck.extra_slots.get(spirit, 0)
        for spirit in ("logic", "perception", "willpower")
    }


def _upgrade_spirit_value(state: GameState, spirit: str, amount: int, extra_lines: list[str] | None = None) -> None:
    actor = _player_actor(state)
    assert spirit in {"logic", "perception", "willpower"}, f"Unknown spirit: {spirit}"
    setattr(actor, spirit, getattr(actor, spirit) + amount)
    sync_trauma_cards_with_health(state)
    _mark_content_dirty(state)
    if extra_lines is not None:
        extra_lines.append(f"{_field_label(spirit)} +{amount}")


def _add_spirit_slot(state: GameState, spirit: str, extra_lines: list[str] | None = None) -> None:
    assert spirit in state.deck.extra_slots, f"Unknown spirit: {spirit}"
    state.deck.extra_slots[spirit] += 1
    refresh_spirit_slots(state.deck)
    sync_trauma_cards_with_health(state)
    _mark_content_dirty(state)
    if extra_lines is not None:
        extra_lines.append(f"{_field_label(spirit)} 获得额外槽位")


def _check_endings(state: GameState) -> None:
    if state.screen == ScreenName.ENDING:
        return
    pursuit_spec = SCENARIO.clocks_by_id.get("pursuit")
    if pursuit_spec is None:
        return
    assert "pursuit" in state.world.progress_clocks, "Scenario defines `pursuit` clock but state is missing it"
    pursuit = state.world.progress_clocks["pursuit"]
    if pursuit.value >= pursuit_spec.segments:
        state.ending_id = "caught"
        state.ending_title = "被追上了"
        state.ending_body = "你每晚都在争时间，但脚步声终究还是追上了你。"
        state.screen = ScreenName.ENDING


def _compose_resolution_text(result: ResultType, effect_lines: tuple[str, ...], fallback: str) -> str:
    return fallback


def _describe_effects(effects: tuple[Effect, ...], action_id: str, state: GameState) -> tuple[str, ...]:
    lines: list[str] = []
    encounter = _encounter(state) if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None else None
    for item in effects:
        value = item.value
        if item.kind == "set_field":
            key, raw = _describe_set_field_payload(value, state)
            lines.append(f"{_field_label(key)} = {raw}")
        elif item.kind == "add_field":
            key, amount = _resolve_add_field_payload(value)
            if key == "stress":
                energy_amount = -amount
                lines.append(f"精力 {'+' if energy_amount >= 0 else ''}{energy_amount}")
            else:
                lines.append(f"{_field_label(key)} {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "copy_field":
            assert isinstance(value, str)
            target, source = value.split(":", 1)
            lines.append(f"{_field_label(target)} = {_field_label(source)}")
        elif item.kind == "shift_clock":
            key, amount = _resolve_shift_clock_payload(value)
            title = encounter.clocks_by_id[key].title if encounter is not None and key in encounter.clocks_by_id else SCENARIO.clocks_by_id.get(key, None).title if key in SCENARIO.clocks_by_id else key
            lines.append(f"{title} {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_health":
            amount = int(value)
            lines.append(f"生命 {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_energy":
            amount = int(value)
            lines.append(f"精力 {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_stress":
            amount = int(value)
            lines.append(f"精力 {'+' if -amount >= 0 else ''}{-amount}")
        elif item.kind == "advance_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            spec = SCENARIO.clocks_by_id[key]
            if "action_use" in spec.tags:
                continue
            lines.append(f"{spec.title} +{raw}")
        elif item.kind == "advance_encounter_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            title = encounter.clocks_by_id[key].title if encounter is not None else key
            lines.append(f"{title} +{raw}")
        elif item.kind == "damage_encounter_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            title = encounter.clocks_by_id[key].title if encounter is not None else key
            lines.append(f"{title} -{raw}")
        elif item.kind == "set_encounter_store":
            # Encounter store writes drive dynamic scene changes, but most of them
            # are internal authoring facts rather than player-facing outcomes.
            continue
        elif item.kind == "end_encounter":
            lines.append("任务结束")
        elif item.kind == "start_encounter":
            assert isinstance(value, str)
            target = get_encounter(value)
            lines.append(f"进入任务：{target.title}")
        elif item.kind == "start_dialogue":
            assert isinstance(value, str)
            target = get_dialogue(value)
            lines.append(f"进入对话：{target.title}")
        elif item.kind == "reset_hand":
            lines.append("抽取行动卡")
        elif item.kind == "advance_day":
            lines.append("进入下一天，精力 -1")
        elif item.kind == "end_game":
            if isinstance(value, tuple):
                lines.append(str(value[0]))
            else:
                lines.append("游戏结束")
        elif item.kind == "upgrade_spirit_value":
            assert isinstance(value, str)
            spirit, raw = value.split(":", 1)
            lines.append(f"{_field_label(spirit)} +{raw}")
        elif item.kind == "add_spirit_slot":
            assert isinstance(value, str)
            lines.append(f"{_field_label(value)} 获得额外槽位")
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
    return tuple(deduped[:4])


def _item_label(item_id: str) -> str:
    if item_id == "clothes":
        return "华美衣服"
    if item_id == "car_key":
        return "车钥匙"
    if item_id == "repair_case_item":
        return "任务道具"
    if item_id == "gun":
        return "枪"
    return item_id


def _field_label(field_id: str) -> str:
    if field_id == "health":
        return "生命"
    if field_id == "stress":
        return "精力"
    if field_id == "energy":
        return "精力"
    if field_id == "money":
        return "金钱"
    if field_id == "cigarettes":
        return "烟卷"
    if field_id == "logic":
        return "逻辑"
    if field_id == "perception":
        return "感知"
    if field_id == "willpower":
        return "意志"
    return _item_label(field_id)


def claim_growth(state: GameState, growth_id: str) -> None:
    if state.growth_points <= 0:
        return
    growth = GROWTH_DEFS[growth_id]
    if not all_met(growth.conditions, state):
        return
    _apply_effects(growth.effects, state, RandomSource(state.seed))
    state.growth_points = max(0, state.growth_points - 1)
    _push_log(state, f"成长调整：{growth.title}")
    push_notification(state, "success", "成长已确认", growth.title)
    close_modal(state)


def location_for_action(action_id: str, state: GameState) -> str | None:
    content = _current_content(state)
    for location_id, action_ids in content.actions_by_location.items():
        if action_id in action_ids:
            return location_id
    raise AssertionError(f"Unknown action owner: {action_id}")
