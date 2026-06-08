from __future__ import annotations

from sincity.model.defs import ActionDef
from sincity.model.enums import ScreenName
from sincity.model.state import ActionResolution
from sincity.model.enums import ResultType
from sincity.model.state import GameState, PendingResolutionState, ActiveActionRevealState
from sincity.game.rng import RandomSource

from sincity.game.actions import clear_action_reveal, clear_assembly, clear_selected_input, current_action, action_ready_to_execute, action_requires_energy_slot
from sincity.game.effects import apply_effects, describe_effects
from sincity.game.queries import location_for_action
from sincity.game.fields import _push_log
from sincity.game.judgment import roll_result


# ── Pending resolution lifecycle ───────────────────────────────────

def _check_endings(state: GameState) -> None:
    if state.screen == ScreenName.ENDING:
        return
    from sincity.content import SCENARIO
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


def _should_auto_dismiss_pending_resolution(
    state: GameState,
    pending: PendingResolutionState,
    *,
    previous_screen: ScreenName,
    previous_encounter_root_id: str | None,
) -> bool:
    from sincity.game.encounters import _current_encounter_root_id
    from sincity.game.conditions import location_is_visible
    if state.screen != previous_screen:
        return True
    if previous_screen == ScreenName.ENCOUNTER:
        if state.active_encounter is None:
            return True
        from sincity.game.queries import get_action_for_state
        if get_action_for_state(state, pending.resolution.action_id) is None:
            return True
        if previous_encounter_root_id is not None and _current_encounter_root_id(state) != previous_encounter_root_id:
            return True
        if pending.location_id and not location_is_visible(pending.location_id, state):
            return True
    return False


def advance_pending_resolution(state: GameState, rng: RandomSource, dt: float) -> None:
    pending = state.pending_resolution
    if pending is None:
        return
    if not pending.settled:
        from sincity.game.encounters import _current_encounter_root_id
        from sincity.game.events import ResolutionSettled
        previous_screen = state.screen
        if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
            previous_encounter_root_id = _current_encounter_root_id(state)
        else:
            previous_encounter_root_id = None
        pending.progress = min(1.0, pending.progress + dt / 0.7)
        if pending.progress >= 1.0:
            _push_log(state, pending.log_text)
            saved_actor_id = state.acting_actor_id
            state.acting_actor_id = pending.acting_actor_id
            extra_lines = apply_effects(pending.effects, state, rng)
            state.acting_actor_id = saved_actor_id
            if extra_lines:
                merged = list(pending.resolution.effect_lines)
                for line in extra_lines:
                    if line not in merged:
                        merged.append(line)
                pending.resolution.effect_lines = tuple(merged[:6])
            state.last_resolution = pending.resolution
            _check_endings(state)
            if pending.completion_kind == "reveal" and state.screen == previous_screen:
                state.action_reveal = ActiveActionRevealState(
                    action_id=pending.resolution.action_id,
                    title=pending.reveal_title,
                    text=pending.reveal_text,
                    duration=pending.reveal_duration,
                )
                state.pending_resolution = None
                state.pending_events.append(ResolutionSettled(action_id=pending.resolution.action_id))
                return
            if state.modal.kind == "location" and state.modal.primary_id is not None:
                from sincity.game.conditions import location_is_visible
                if not location_is_visible(state.modal.primary_id, state):
                    from sincity.game.actions import close_modal
                    close_modal(state)
            pending.settled = True
            state.pending_events.append(ResolutionSettled(action_id=pending.resolution.action_id))
            if _should_auto_dismiss_pending_resolution(
                state, pending,
                previous_screen=previous_screen,
                previous_encounter_root_id=previous_encounter_root_id,
            ):
                dismiss_pending_resolution(state)
        return


def _current_encounter_root_id(state: GameState) -> str:
    from sincity.game.encounters import _current_encounter_root_id as _fn
    return _fn(state)


def dismiss_pending_resolution(state: GameState) -> None:
    """清除当前 pending resolution。调用者必须保证 pending 已 settled（effect 已落地），否则说明调用时机错误。"""
    pending = state.pending_resolution
    if pending is None:
        return
    assert pending.settled, (
        f"dismiss_pending_resolution() called on unsettled pending "
        f"(action={pending.resolution.action_id}, progress={pending.progress:.2f}). "
        f"Effects have not been applied yet. "
        f"Call advance_pending_resolution() first, or wait for settlement."
    )
    if state.assembly.action_id == pending.resolution.action_id:
        clear_assembly(state)
    state.pending_resolution = None


# ── Action reveal ──────────────────────────────────────────────────

def advance_action_reveal(state: GameState, dt: float) -> None:
    reveal = state.action_reveal
    if reveal is None:
        return
    if reveal.duration <= 0:
        return
    reveal.elapsed += dt
    if reveal.elapsed >= reveal.duration:
        clear_action_reveal(state)


# ── Action execution ───────────────────────────────────────────────

def _slotted_card_id(state: GameState) -> str | None:
    from sincity.game.actions import _slotted_card_id as _fn
    return _fn(state)


def _compose_resolution_text(result: ResultType, effect_lines: tuple[str, ...], fallback: str) -> str:
    return fallback


def perform_current_action(state: GameState, rng: RandomSource) -> None:
    from sincity.game.actions import slot_effective_value, slot_owner
    action = current_action(state)
    assert action is not None
    assert action_ready_to_execute(action, state), f"Action not ready: {action.id}"
    location_id = location_for_action(action.id, state)
    card_id = _slotted_card_id(state)
    state.acting_actor_id = slot_owner(card_id) if card_id else ""
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
            effect_lines=describe_effects(action.effects, action.id, state),
        )
        state.pending_resolution = PendingResolutionState(
            resolution=resolution,
            effects=action.effects,
            log_text=f"{action.title}: {action.description}",
            location_id=location_id or "",
            acting_actor_id=state.acting_actor_id,
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
        effect_lines = describe_effects(resolved_effects, action.id, state)
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
            acting_actor_id=state.acting_actor_id,
        )
    clear_selected_input(state)


def perform_instant_action(state: GameState, action: ActionDef, rng: RandomSource) -> None:
    del rng
    from sincity.game.conditions import action_is_available
    from sincity.game.actions import action_is_instant, clear_assembly as _ca, clear_selected_input as _csi
    assert action_is_instant(action), f"Action is not an instant action: {action.id}"
    assert action_is_available(action, state), f"Instant action not available: {action.id}"
    _ca(state)
    _csi(state)
    location_id = location_for_action(action.id, state)
    effect_lines = describe_effects(action.effects, action.id, state)
    resolution = ActionResolution(
        action_id=action.id,
        card_id=None,
        result=None,
        die_roll=None,
        value=None,
        text=action.description,
        effect_lines=effect_lines,
    )
    log_text = action.title + ("：" + "，".join(effect_lines[:1]) if effect_lines else "")
    state.pending_resolution = PendingResolutionState(
        resolution=resolution,
        effects=action.effects,
        log_text=log_text,
        location_id=location_id or "",
        completion_kind="instant",
    )


def perform_reveal_action(state: GameState, action: ActionDef, rng: RandomSource) -> None:
    del rng
    from sincity.game.conditions import action_is_available
    from sincity.game.actions import action_is_reveal, clear_assembly as _ca, clear_selected_input as _csi
    assert action_is_reveal(action), f"Action is not a reveal action: {action.id}"
    assert action_is_available(action, state), f"Reveal action not available: {action.id}"
    _ca(state)
    _csi(state)
    reveal = action.reveal
    assert reveal is not None
    location_id = location_for_action(action.id, state)
    effect_lines = describe_effects(action.effects, action.id, state)
    resolution = ActionResolution(
        action_id=action.id,
        card_id=None,
        result=None,
        die_roll=None,
        value=None,
        text=action.description,
        effect_lines=effect_lines,
    )
    log_text = action.title + ("：" + "，".join(effect_lines[:1]) if effect_lines else "")
    state.pending_resolution = PendingResolutionState(
        resolution=resolution,
        effects=action.effects,
        log_text=log_text,
        location_id=location_id or "",
        completion_kind="reveal",
        reveal_title=reveal.title or action.title,
        reveal_text=reveal.text,
        reveal_duration=reveal.duration,
    )


# ── Input consumption ────────────────────────────────────────────────

def _consume_slotted_card(state: GameState) -> None:
    slot_id = state.assembly.slotted_card_id
    if slot_id is None:
        return
    state.deck.action_card_bonuses.pop(slot_id, None)
    state.deck.action_card_penalties.pop(slot_id, None)
    state.deck.action_card_labels.pop(slot_id, None)
    if slot_id in state.deck.available_slots:
        state.deck.available_slots.remove(slot_id)
    if slot_id not in state.deck.exhausted_slots:
        state.deck.exhausted_slots.append(slot_id)


def _consume_energy_from_slot(state: GameState, slot_id: str) -> None:
    from sincity.game.actions import _slot_can_spend_energy
    from sincity.game.encounters import _sync_encounter_action_cycle
    from sincity.game.fields import _mark_content_dirty
    assert _slot_can_spend_energy(state, slot_id), f"energy slot cannot spend energy: {slot_id}"
    _sync_encounter_action_cycle(state)
    _consume_slotted_card(state)
    _mark_content_dirty(state)


def _consume_check_resource(state: GameState, slot_id: str) -> None:
    _consume_energy_from_slot(state, slot_id)


def _consume_inputs(state: GameState, action: ActionDef) -> None:
    for requirement in action.inputs:
        from sincity.game.actions import requirement_is_slotted
        assert requirement_is_slotted(state, requirement), f"Requirement not slotted: {requirement}"
        if requirement.kind == "item" and requirement.consume:
            from sincity.game.fields import add_field
            add_field(state, requirement.key, -requirement.amount)
        if requirement.kind == "card" and action.check is None:
            _consume_slotted_card(state)


def consume_inputs(state: GameState, action: ActionDef) -> None:
    _consume_inputs(state, action)
