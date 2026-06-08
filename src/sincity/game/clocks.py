from __future__ import annotations

from sincity.content import SCENARIO
from sincity.content.runtime import evaluate_world_cycle_start_effects
from sincity.encounters import evaluate_cycle_start_effects
from sincity.model.enums import ScreenName
from sincity.model.state import GameState
from sincity.rules.rng import RandomSource

from sincity.game.actions import clear_assembly, clear_selected_input
from sincity.game.effects import apply_effects
from sincity.game.fields import _mark_content_dirty, _push_log, change_actor_pressure, change_energy, tick_actor_statuses_after_draw


def advance_clock(state: GameState, clock_id: str, amount: int = 1, extra_lines: list[str] | None = None) -> None:
    from sincity.rules.rng import RandomSource
    spec = SCENARIO.clocks_by_id[clock_id]
    clock_state = state.world.progress_clocks[clock_id]
    before = clock_state.value
    clock_state.value = max(0, min(spec.segments, clock_state.value + amount))
    clock_state.visible = True
    _mark_content_dirty(state)
    for threshold in spec.thresholds:
        if before < threshold.at <= clock_state.value:
            apply_effects(threshold.effects, state, RandomSource(state.seed), extra_lines)


def advance_encounter_clock(state: GameState, clock_id: str, amount: int = 1) -> None:
    from sincity.game.encounters import _encounter
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
    if state.active_encounter is not None:
        from sincity.game.encounters import _encounter
        if clock_id in _encounter(state).clocks_by_id:
            if amount >= 0:
                advance_encounter_clock(state, clock_id, amount)
            else:
                damage_encounter_clock(state, clock_id, -amount)
            return
    advance_clock(state, clock_id, amount, extra_lines)


def reset_hand(state: GameState, rng: RandomSource) -> None:
    from sincity.content import ACTOR_STATUS_DEFS
    from sincity.rules.deck import refresh_spirit_slots
    from sincity.game.session import _active_card_actors, _reset_action_cycle_from_deck
    refresh_spirit_slots(state.deck, rng, actors=_active_card_actors(state), screen=state.screen, status_defs=ACTOR_STATUS_DEFS)
    _reset_action_cycle_from_deck(state)
    _mark_content_dirty(state)


def advance_cycle(state: GameState, rng: RandomSource) -> None:
    from sincity.game.reacts import resolve_encounter_reaction_die, resolve_encounter_reacts, resolve_world_reacts
    from sincity.game.effects import apply_effects as _apply_effects

    extra_lines: list[str] = []
    from_effect = state.pending_resolution is not None

    if state.screen == ScreenName.CITY:
        state.day += 1
        change_energy(state, -1, extra_lines)
        for actor_id in [state.player_actor_id, *state.companion_actor_ids]:
            actor = state.party.get(actor_id)
            if actor is not None:
                change_actor_pressure(state, -1, actor_id, extra_lines)
    elif state.screen == ScreenName.ENCOUNTER:
        assert state.active_encounter is not None
        clear_assembly(state)
        clear_selected_input(state)
        change_energy(state, -1, extra_lines)
    else:
        return

    if state.screen == ScreenName.CITY:
        cycle_effects = evaluate_world_cycle_start_effects(SCENARIO, state, rng)
    else:
        from sincity.game.encounters import _encounter
        cycle_effects = evaluate_cycle_start_effects(_encounter(state), state.active_encounter.store, rng)
    _apply_effects(cycle_effects, state, rng, extra_lines, resolve_encounter_reacts=False)

    if state.screen == ScreenName.ENCOUNTER:
        resolve_encounter_reaction_die(state, rng, extra_lines)

    if state.screen in (ScreenName.CITY, ScreenName.ENCOUNTER):
        reset_hand(state, rng)
        if state.screen == ScreenName.CITY:
            tick_actor_statuses_after_draw(state)

    if not from_effect and state.screen == ScreenName.ENCOUNTER:
        cycle_text = f"；{'，'.join(extra_lines[:2])}" if extra_lines else ""
        _push_log(state, f"你短暂休整了一下：精力 -1，重抽行动卡{cycle_text}。")

    if not from_effect:
        if state.screen == ScreenName.CITY:
            resolve_world_reacts(state, rng, extra_lines)
        elif state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
            resolve_encounter_reacts(state, rng, extra_lines)

    _mark_content_dirty(state)
