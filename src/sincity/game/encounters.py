from __future__ import annotations

from sincity.encounters import evaluate_fail_effects, evaluate_success_effects, get_encounter, initial_store
from sincity.encounters.defs import CompiledEncounterProgram
from sincity.model.enums import ScreenName
from sincity.model.state import ActiveEncounterState, GameState
from sincity.game.rng import RandomSource

from sincity.game.actions import clear_assembly, clear_selected_input
from sincity.game.effects import apply_effects
from sincity.game.fields import _mark_content_dirty, world_attr_value


def _push_log(state: GameState, text: str) -> None:
    from sincity.constants import MAX_LOG_LINES
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def _push_notification(state: GameState, kind: str, title: str, body: str) -> None:
    from sincity.game.notifications import push_notification
    push_notification(state, kind, title, body)


def _encounter(state: GameState):
    assert state.active_encounter is not None
    return get_encounter(state.active_encounter.encounter_id)


def _current_encounter_root_id(state: GameState) -> str:
    from sincity.game.queries import current_encounter_snapshot
    return current_encounter_snapshot(state).root_location_id


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


def _initial_encounter_store(state: GameState, encounter: CompiledEncounterProgram) -> dict[str, int | bool | str]:
    store = initial_store(encounter)
    for key, spec in encounter.store_specs.items():
        if spec.persist == "world_attr":
            store[key] = world_attr_value(state, key)
        elif spec.persist == "world_inventory":
            store[key] = state.world.inventory.get(key, spec.initial)
        elif spec.persist == "world_value":
            store[key] = state.world.values.get(key, spec.initial)
    return store


def start_encounter(state: GameState, encounter_id: str) -> None:
    from sincity.game.reacts import resolve_encounter_reacts
    from sincity.game.clocks import reset_hand

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
    resolve_encounter_reacts(state, RandomSource(state.seed), [])


def start_encounter_from_dialogue(state: GameState, encounter_id: str) -> None:
    state.active_dialogue = None
    start_encounter(state, encounter_id)


def finish_encounter(state: GameState, outcome: str, rng: RandomSource, extra_lines: list[str] | None = None) -> None:
    from sincity.game.clocks import reset_hand
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
    state.modal.stacked_frames.clear()
    clear_assembly(state)
    clear_selected_input(state)
    state.encounter_resource_root_id = ""
    reset_hand(state, rng)
    _mark_content_dirty(state)
    if outcome == "success":
        apply_effects(evaluate_success_effects(encounter, encounter_store), state, rng, extra_lines)
        _push_log(state, f"{encounter.title}：完成。")
    elif outcome == "fail":
        apply_effects(evaluate_fail_effects(encounter, encounter_store), state, rng, extra_lines)
        _push_log(state, f"{encounter.title}：失败。")
    else:
        _push_log(state, f"{encounter.title}：中断。")


def finish_encounter_from_dialogue(state: GameState, outcome: str) -> None:
    state.active_dialogue = None
    finish_encounter(state, outcome, RandomSource(state.seed), [])


def can_endure_pressure_during_encounter(state: GameState) -> bool:
    if state.screen != ScreenName.ENCOUNTER or state.active_encounter is None:
        return False
    if state.encounter_pressure_used:
        return False
    if state.attributes.health <= 0:
        return False
    from sincity.game.actions import slot_is_available
    return any(slot_is_available(state, slot_id) for slot_id in state.deck.available_slots)


def endure_pressure_during_encounter(state: GameState, rng: RandomSource) -> None:
    from sincity.game.actions import slot_is_available, slot_owner
    from sincity.game.fields import actor_name, change_health

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
    _push_log(state, f"你咬牙承受住压力：生命 -1，{owner_name} 的一张行动卡本回合 +1。")
    _push_notification(state, "warning", "承受压力", "随机一张可用行动卡本回合 +1。")
