from __future__ import annotations

from sincity.constants import MAX_LOG_LINES
from sincity.content import DEBUG_COMPANION_ORDER
from sincity.encounters.defs import CompiledEncounterProgram
from sincity.model.defs import ActionDef, CheckValueBreakdown, DynamicValue, Effect, InputRequirement
from sincity.model.enums import ResultType, ScreenName, Suit
from sincity.model.state import GameState, PartyActorState, PendingResolutionState
from sincity.rules.rng import RandomSource


def _push_log(state: GameState, text: str) -> None:
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def start_new_run(seed: int) -> tuple[GameState, RandomSource]:
    from sincity.game.session import start_new_run as _fn
    return _fn(seed)


def get_action(action_id: str) -> ActionDef:
    return current_world_snapshot(_runtime_projection_state()).actions_by_id[action_id]


def get_action_for_state(state: GameState, action_id: str) -> ActionDef | None:
    from sincity.game.queries import get_action_for_state as _fn
    return _fn(state, action_id)


def _current_content(state: GameState | None = None):
    from sincity.game.queries import _current_content as _fn
    return _fn(state)

def _runtime_projection_state() -> GameState:
    state, _ = start_new_run(0)
    return state


def _encounter(state: GameState):
    from sincity.game.encounters import _encounter as _fn
    return _fn(state)

def _encounter_snapshot(state: GameState):
    assert state.active_encounter is not None
    return current_encounter_snapshot(state)


def _current_encounter_root_id(state: GameState) -> str:
    from sincity.game.resolution import _current_encounter_root_id as _fn
    return _fn(state)

def _reset_action_cycle_from_deck(state: GameState) -> None:
    from sincity.game.session import _reset_action_cycle_from_deck as _fn
    return _fn(state)


def _reset_encounter_action_cycle(state: GameState) -> None:
    _reset_action_cycle_from_deck(state)


def _sync_encounter_action_cycle(state: GameState) -> None:
    from sincity.game.encounters import _sync_encounter_action_cycle as _fn
    _fn(state)


def encounter_action_cards(state: GameState) -> tuple[int, int] | None:
    from sincity.game.encounters import encounter_action_cards as _fn
    return _fn(state)


def current_world_snapshot(state: GameState):
    from sincity.game.queries import current_world_snapshot as _fn
    return _fn(state)


def current_encounter_snapshot(state: GameState):
    from sincity.game.queries import current_encounter_snapshot as _fn
    return _fn(state)


def current_encounter_reaction_table(state: GameState):
    from sincity.game.queries import current_encounter_reaction_table as _fn
    return _fn(state)


def _mark_content_dirty(state: GameState) -> None:
    state.render_cache.revision += 1


def get_clock_value(state: GameState, clock_id: str) -> int:
    from sincity.game.queries import get_clock_value as _fn
    return _fn(state, clock_id)


def sync_world_progress_clocks(state: GameState) -> None:
    from sincity.game.queries import sync_world_progress_clocks as _fn
    return _fn(state)


def get_clock_spec_for_state(state: GameState, clock_id: str):
    from sincity.game.queries import get_clock_spec_for_state as _fn
    return _fn(state, clock_id)


def _field_value(state: GameState, key: str) -> int | bool | str:
    from sincity.game.fields import field_value as _fn
    return _fn(state, key)


def _set_field(state: GameState, key: str, value: int | bool | str, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import set_field as _fn
    _fn(state, key, value, extra_lines)


def _world_attr_value(state: GameState, key: str) -> int:
    from sincity.game.fields import world_attr_value as _fn
    return _fn(state, key)


def _set_world_attr(state: GameState, key: str, value: int) -> None:
    from sincity.game.fields import set_world_attr as _fn
    _fn(state, key, value)


def _add_field(state: GameState, key: str, amount: int, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import add_field as _fn
    _fn(state, key, amount, extra_lines)


def _slot_spirit(slot_id: str) -> str:
    return slot_owner(slot_id)


def slot_owner(slot_id: str) -> str:
    from sincity.game.actions import slot_owner as _fn
    return _fn(slot_id)


def _player_actor(state: GameState):
    from sincity.game.fields import player_actor as _fn
    return _fn(state)


def party_actor(state: GameState, actor_id: str):
    from sincity.game.fields import party_actor as _fn
    return _fn(state, actor_id)


def actor_name(state: GameState, actor_id: str) -> str:
    from sincity.game.fields import actor_name as _fn
    return _fn(state, actor_id)


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
    from sincity.game.session import _active_card_actors as _fn
    return _fn(state)


def _all_spirit_slots(state: GameState) -> list[str]:
    from sincity.game.actions import _all_spirit_slots as _fn
    return _fn(state)


def slot_trauma_count(state: GameState, slot_id: str) -> int:
    from sincity.game.actions import slot_trauma_count as _fn
    return _fn(state, slot_id)


def slot_base_raw_value(state: GameState, slot_id: str) -> int:
    from sincity.game.actions import slot_base_raw_value as _fn
    return _fn(state, slot_id)


def slot_base_value(state: GameState, slot_id: str) -> int:
    from sincity.game.actions import slot_base_value as _fn
    return _fn(state, slot_id)


def slot_current_value(state: GameState, slot_id: str) -> int:
    from sincity.game.actions import slot_current_value as _fn
    return _fn(state, slot_id)


def slot_is_available(state: GameState, slot_id: str) -> bool:
    from sincity.game.actions import slot_is_available as _fn
    return _fn(state, slot_id)


def slot_is_exhausted(state: GameState, slot_id: str) -> bool:
    from sincity.game.actions import slot_is_exhausted as _fn
    return _fn(state, slot_id)


def slot_is_locked(state: GameState, slot_id: str) -> bool:
    from sincity.game.actions import slot_is_locked as _fn
    return _fn(state, slot_id)


def slot_is_preferred_for_check(slot_id: str, check) -> bool | None:
    del slot_id, check
    return None


def _actor_attribute_value(state: GameState, owner_id: str, suit: Suit) -> int:
    from sincity.game.fields import _actor_attribute_value as _fn
    return _fn(state, owner_id, suit)


def slot_effective_value(state: GameState, slot_id: str, check) -> int:
    from sincity.game.actions import slot_effective_value as _fn
    return _fn(state, slot_id, check)


def slot_value_breakdown(state: GameState, slot_id: str, check) -> CheckValueBreakdown:
    from sincity.game.actions import slot_value_breakdown as _fn
    return _fn(state, slot_id, check)


def _suit_label(suit: Suit) -> str:
    from sincity.game.actions import _suit_label as _fn
    return _fn(suit)


def _slot_can_execute_check(state: GameState, slot_id: str, check) -> bool:
    from sincity.game.actions import _slot_can_execute_check as _fn
    return _fn(state, slot_id, check)


def _slot_can_spend_energy(state: GameState, slot_id: str) -> bool:
    from sincity.game.actions import _slot_can_spend_energy as _fn
    return _fn(state, slot_id)


def _coerce_like(current: int | bool | str, value: int | bool | str) -> int | bool | str:
    from sincity.game.fields import _coerce_like as _fn
    return _fn(current, value)


def action_is_visible(action: ActionDef, state: GameState) -> bool:
    from sincity.game.conditions import action_is_visible as _fn
    return _fn(action, state)


def action_is_available(action: ActionDef, state: GameState) -> bool:
    from sincity.game.conditions import action_is_available as _fn
    return _fn(action, state)


def location_is_visible(location_id: str, state: GameState) -> bool:
    from sincity.game.conditions import location_is_visible as _fn
    return _fn(location_id, state)


def location_is_available(location_id: str, state: GameState) -> bool:
    from sincity.game.conditions import location_is_available as _fn
    return _fn(location_id, state)


def all_met(conditions, state: GameState) -> bool:
    from sincity.game.conditions import all_met as _fn
    return _fn(conditions, state)


def evaluate_condition(item, state: GameState) -> bool:
    from sincity.game.conditions import evaluate_condition as _fn
    return _fn(item, state)


def requirements_affordable(inputs: tuple[InputRequirement, ...], state: GameState) -> bool:
    from sincity.game.conditions import requirements_affordable as _fn
    return _fn(inputs, state)


def open_action(state: GameState, action_id: str, modal_kind: str = "action") -> None:
    from sincity.game.actions import open_action as _fn
    return _fn(state, action_id, modal_kind)

def open_modal(state: GameState, kind: str, primary_id: str | None = None) -> None:
    from sincity.game.actions import open_modal as _fn
    return _fn(state, kind, primary_id)

def open_overlay(state: GameState, kind: str, primary_id: str | None = None) -> None:
    from sincity.game.actions import open_overlay as _fn
    return _fn(state, kind, primary_id)

def clear_assembly(state: GameState) -> None:
    from sincity.game.actions import clear_assembly as _fn
    return _fn(state)

def clear_selected_input(state: GameState) -> None:
    from sincity.game.actions import clear_selected_input as _fn
    return _fn(state)

def trigger_card_hint_flash(state: GameState, action: ActionDef, *, duration: float = 0.75) -> None:
    from sincity.game.actions import trigger_card_hint_flash as _fn
    return _fn(state, action, duration=duration)

def card_hint_flash_active(state: GameState, action: ActionDef | None = None) -> bool:
    from sincity.game.actions import card_hint_flash_active as _fn
    return _fn(state, action)

def card_matches_action_check(action: ActionDef | None, card_id: str) -> bool:
    from sincity.game.actions import card_matches_action_check as _fn
    return _fn(action, card_id)

def close_modal(state: GameState) -> None:
    from sincity.game.actions import close_modal as _fn
    return _fn(state)

def select_card_input(state: GameState, card_id: str, card_index: int | None = None) -> None:
    from sincity.game.actions import select_card_input as _fn
    return _fn(state, card_id, card_index)

def select_item_input(state: GameState, key: str) -> None:
    from sincity.game.actions import select_item_input as _fn
    return _fn(state, key)

def start_dialogue(state: GameState, dialogue_id: str) -> None:
    from sincity.game.dialogues import start_dialogue as _fn
    _fn(state, dialogue_id)


def start_quick_dialogue(state: GameState, raw_text: str) -> None:
    from sincity.game.dialogues import start_quick_dialogue as _fn
    _fn(state, raw_text)


def _open_dialogue_session(state: GameState, session, *, primary_id: str) -> None:
    from sincity.game.dialogues import _open_dialogue_session as _fn
    return _fn(state, session, primary_id=primary_id)

def continue_dialogue(state: GameState) -> None:
    from sincity.game.dialogues import continue_dialogue as _fn
    _fn(state)


def fast_forward_dialogue(state: GameState) -> bool:
    from sincity.game.dialogues import fast_forward_dialogue as _fn
    return _fn(state)


def choose_dialogue_option(state: GameState, index: int) -> None:
    from sincity.game.dialogues import choose_dialogue_option as _fn
    _fn(state, index)


def finish_dialogue(state: GameState) -> None:
    from sincity.game.dialogues import finish_dialogue as _fn
    _fn(state)


def _clear_dialogue_modal(state: GameState) -> None:
    from sincity.game.dialogues import _clear_dialogue_modal as _fn
    return _fn(state)

def _apply_game_over(state: GameState, *, title: str, body: str) -> None:
    from sincity.game.dialogues import _apply_game_over as _fn
    return _fn(state, title=title, body=body)

def end_game(state: GameState, *, title: str = "游戏结束", body: str = "") -> None:
    from sincity.game.dialogues import end_game as _fn
    _fn(state, title=title, body=body)


def focus_action(state: GameState, action_id: str) -> None:
    from sincity.game.actions import focus_action as _fn
    return _fn(state, action_id)

def action_slot_ready(state: GameState, action: ActionDef, requirement: InputRequirement | None = None, *, energy_slot: bool = False) -> bool:
    from sincity.game.actions import action_slot_ready as _fn
    return _fn(state, action, requirement, energy_slot=energy_slot)

def action_can_accept_selected_input(state: GameState, action: ActionDef, requirement: InputRequirement | None = None, *, energy_slot: bool = False) -> bool:
    from sincity.game.actions import action_can_accept_selected_input as _fn
    return _fn(state, action, requirement, energy_slot=energy_slot)

def first_usable_energy_slot(state: GameState, action: ActionDef) -> tuple[str, int] | None:
    from sincity.game.actions import first_usable_energy_slot as _fn
    return _fn(state, action)

def toggle_action_energy_slot(state: GameState, action: ActionDef) -> None:
    from sincity.game.actions import toggle_action_energy_slot as _fn
    return _fn(state, action)

def toggle_action_requirement_slot(state: GameState, action: ActionDef, requirement: InputRequirement) -> None:
    from sincity.game.actions import toggle_action_requirement_slot as _fn
    return _fn(state, action, requirement)

def slot_card(state: GameState, card_id: str) -> None:
    from sincity.game.actions import slot_card as _fn
    return _fn(state, card_id)

def toggle_requirement_input(state: GameState, requirement: InputRequirement) -> None:
    from sincity.game.actions import toggle_requirement_input as _fn
    return _fn(state, requirement)

def requirement_is_slotted(state: GameState, requirement: InputRequirement) -> bool:
    from sincity.game.actions import requirement_is_slotted as _fn
    return _fn(state, requirement)

def action_ready_to_execute(action: ActionDef, state: GameState) -> bool:
    from sincity.game.actions import action_ready_to_execute as _fn
    return _fn(action, state)

def action_requires_energy_slot(action: ActionDef) -> bool:
    from sincity.game.actions import action_requires_energy_slot as _fn
    return _fn(action)

def action_is_direct(action: ActionDef) -> bool:
    from sincity.game.actions import action_is_direct as _fn
    return _fn(action)

def action_is_reveal(action: ActionDef) -> bool:
    from sincity.game.actions import action_is_reveal as _fn
    return _fn(action)

def action_is_instant(action: ActionDef) -> bool:
    from sincity.game.actions import action_is_instant as _fn
    return _fn(action)

def current_action(state: GameState) -> ActionDef | None:
    from sincity.game.actions import current_action as _fn
    return _fn(state)

def perform_current_action(state: GameState, rng: RandomSource) -> None:
    from sincity.game.resolution import perform_current_action as _fn
    return _fn(state, rng)


def perform_instant_action(state: GameState, action: ActionDef, rng: RandomSource) -> None:
    from sincity.game.resolution import perform_instant_action as _fn
    return _fn(state, action, rng)


def perform_reveal_action(state: GameState, action: ActionDef, rng: RandomSource) -> None:
    from sincity.game.resolution import perform_reveal_action as _fn
    return _fn(state, action, rng)


def advance_action_reveal(state: GameState, dt: float) -> None:
    from sincity.game.resolution import advance_action_reveal as _fn
    return _fn(state, dt)

def clear_action_reveal(state: GameState) -> None:
    from sincity.game.actions import clear_action_reveal as _fn
    return _fn(state)

def advance_pending_resolution(state: GameState, rng: RandomSource, dt: float) -> None:
    from sincity.game.resolution import advance_pending_resolution as _fn
    return _fn(state, rng, dt)


def dismiss_pending_resolution(state: GameState) -> None:
    from sincity.game.resolution import dismiss_pending_resolution as _fn
    return _fn(state)

def _should_auto_dismiss_pending_resolution(
    state: GameState,
    pending: PendingResolutionState,
    *,
    previous_screen: ScreenName,
    previous_encounter_root_id: str | None,
) -> bool:
    from sincity.game.resolution import _should_auto_dismiss_pending_resolution as _fn
    return _fn(state, pending, previous_screen=previous_screen, previous_encounter_root_id=previous_encounter_root_id)

def _consume_inputs(state: GameState, action: ActionDef) -> None:
    from sincity.game.resolution import _consume_inputs as _fn
    _fn(state, action)


def _consume_slotted_card(state: GameState) -> None:
    from sincity.game.resolution import _consume_slotted_card as _fn
    _fn(state)


def _consume_check_resource(state: GameState, slot_id: str) -> None:
    from sincity.game.resolution import _consume_check_resource as _fn
    _fn(state, slot_id)


def _consume_energy_from_slot(state: GameState, slot_id: str) -> None:
    from sincity.game.resolution import _consume_energy_from_slot as _fn
    _fn(state, slot_id)


def _selected_card_id(state: GameState) -> str | None:
    from sincity.game.actions import _selected_card_id as _fn
    return _fn(state)

def _slotted_card_id(state: GameState) -> str | None:
    from sincity.game.actions import _slotted_card_id as _fn
    return _fn(state)

def _apply_effects(
    effects: tuple[Effect, ...],
    state: GameState,
    rng: RandomSource,
    extra_lines: list[str] | None = None,
    *,
    resolve_encounter_reacts: bool = True,
) -> tuple[str, ...]:
    from sincity.game.effects import apply_effects
    return apply_effects(effects, state, rng, extra_lines, resolve_encounter_reacts=resolve_encounter_reacts)


def _parse_legacy_scalar(raw: str) -> int | bool | str:
    from sincity.game.effects import _parse_legacy_scalar as _fn
    return _fn(raw)

def _resolve_set_field_payload(value: object, state: GameState, rng: RandomSource) -> tuple[str, int | bool | str]:
    from sincity.game.effects import _resolve_set_field_payload as _fn
    return _fn(value, state, rng)

def _resolve_add_field_payload(value: object) -> tuple[str, int]:
    from sincity.game.effects import _resolve_add_field_payload as _fn
    return _fn(value)

def _resolve_shift_clock_payload(value: object) -> tuple[str, int]:
    from sincity.game.effects import _resolve_shift_clock_payload as _fn
    return _fn(value)

def _describe_set_field_payload(value: object, state: GameState) -> tuple[str, str]:
    from sincity.game.effects import _describe_set_field_payload as _fn
    return _fn(value, state)

def _evaluate_dynamic_value(state: GameState, value: DynamicValue, rng: RandomSource) -> object:
    from sincity.game.effects import _evaluate_dynamic_value as _fn
    return _fn(state, value, rng)

def _apply_effect(item: Effect, state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    from sincity.game.effects import apply_effect
    return apply_effect(item, state, rng, extra_lines)


def _award_completed_tasks(state: GameState) -> None:
    from sincity.game.reacts import award_completed_tasks as _fn
    _fn(state)


def _resolve_encounter_reacts(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    from sincity.game.reacts import resolve_encounter_reacts as _fn
    _fn(state, rng, extra_lines)


def _resolve_world_reacts(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    from sincity.game.reacts import resolve_world_reacts as _fn
    _fn(state, rng, extra_lines)


def _react_non_convergence_message(kind: str, program_id: str, fired_sources: list[str]) -> str:
    from sincity.game.reacts import react_non_convergence_message as _fn
    return _fn(kind, program_id, fired_sources)


def reset_hand(state: GameState, rng: RandomSource) -> None:
    from sincity.game.clocks import reset_hand as _fn
    return _fn(state, rng)


def advance_cycle(state: GameState, rng: RandomSource) -> None:
    from sincity.game.clocks import advance_cycle as _fn
    _fn(state, rng)


def _resolve_encounter_reaction_die(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    from sincity.game.reacts import resolve_encounter_reaction_die as _fn
    _fn(state, rng, extra_lines)


def can_endure_pressure_during_encounter(state: GameState) -> bool:
    from sincity.game.encounters import can_endure_pressure_during_encounter as _fn
    return _fn(state)


def endure_pressure_during_encounter(state: GameState, rng: RandomSource) -> None:
    from sincity.game.encounters import endure_pressure_during_encounter as _fn
    _fn(state, rng)


def advance_clock(state: GameState, clock_id: str, amount: int = 1, extra_lines: list[str] | None = None) -> None:
    from sincity.game.clocks import advance_clock as _fn
    _fn(state, clock_id, amount, extra_lines)


def advance_encounter_clock(state: GameState, clock_id: str, amount: int = 1) -> None:
    from sincity.game.clocks import advance_encounter_clock as _fn
    _fn(state, clock_id, amount)


def damage_encounter_clock(state: GameState, clock_id: str, amount: int = 1) -> None:
    from sincity.game.clocks import damage_encounter_clock as _fn
    _fn(state, clock_id, amount)


def shift_clock(state: GameState, clock_id: str, amount: int, extra_lines: list[str] | None = None) -> None:
    from sincity.game.clocks import shift_clock as _fn
    _fn(state, clock_id, amount, extra_lines)


def start_encounter(state: GameState, encounter_id: str) -> None:
    from sincity.game.encounters import start_encounter as _fn
    _fn(state, encounter_id)


def _initial_encounter_store(state: GameState, encounter: CompiledEncounterProgram) -> dict[str, int | bool | str]:
    from sincity.game.encounters import _initial_encounter_store as _fn
    return _fn(state, encounter)


def start_encounter_from_dialogue(state: GameState, encounter_id: str) -> None:
    from sincity.game.encounters import start_encounter_from_dialogue as _fn
    _fn(state, encounter_id)


def finish_encounter(state: GameState, outcome: str, rng: RandomSource, extra_lines: list[str] | None = None) -> None:
    from sincity.game.encounters import finish_encounter as _fn
    _fn(state, outcome, rng, extra_lines)


def finish_encounter_from_dialogue(state: GameState, outcome: str) -> None:
    from sincity.game.encounters import finish_encounter_from_dialogue as _fn
    _fn(state, outcome)


def change_health(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import change_health as _fn
    _fn(state, amount, extra_lines)


def change_actor_pressure(state: GameState, amount: int, actor_id: str, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import change_actor_pressure as _fn
    _fn(state, amount, actor_id, extra_lines)


def pressure_recovery_threshold(actor: PartyActorState) -> int:
    from sincity.game.fields import pressure_recovery_threshold as _fn
    return _fn(actor)


def add_actor_status(actor: PartyActorState, status_id: str) -> None:
    from sincity.game.fields import add_actor_status as _fn
    _fn(actor, status_id)


def tick_actor_statuses_after_draw(state: GameState) -> None:
    from sincity.game.fields import tick_actor_statuses_after_draw as _fn
    return _fn(state)

def change_energy(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import change_energy as _fn
    _fn(state, amount, extra_lines)


def sync_trauma_cards_with_health(state: GameState) -> None:
    from sincity.game.fields import sync_trauma_cards_with_health as _fn
    _fn(state)


def count_spirit_cards(state: GameState) -> dict[str, int]:
    from sincity.game.actions import count_spirit_cards as _fn
    return _fn(state)

def _upgrade_spirit_value(state: GameState, spirit: str, amount: int, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import upgrade_spirit_value as _fn
    return _fn(state, spirit, amount, extra_lines)


def _add_spirit_slot(state: GameState, spirit: str, extra_lines: list[str] | None = None) -> None:
    from sincity.game.fields import add_spirit_slot as _fn
    return _fn(state, spirit, extra_lines)


def _check_endings(state: GameState) -> None:
    from sincity.game.resolution import _check_endings as _fn
    return _fn(state)


def _compose_resolution_text(result: ResultType, effect_lines: tuple[str, ...], fallback: str) -> str:
    from sincity.game.resolution import _compose_resolution_text as _fn
    return _fn(result, effect_lines, fallback)


def _describe_effects(effects: tuple[Effect, ...], action_id: str, state: GameState) -> tuple[str, ...]:
    from sincity.game.effects import describe_effects as _fn
    return _fn(effects, action_id, state)


def _field_label(field_id: str) -> str:
    from sincity.game.effects import _field_label as _fn
    return _fn(field_id)


def claim_growth(state: GameState, growth_id: str) -> None:
    from sincity.game.actions import claim_growth as _fn
    return _fn(state, growth_id)


def location_for_action(action_id: str, state: GameState) -> str | None:
    from sincity.game.queries import location_for_action as _fn
    return _fn(action_id, state)
