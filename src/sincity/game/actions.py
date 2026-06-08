from __future__ import annotations

import time

from sincity.model.defs import ActionDef, InputRequirement
from sincity.model.enums import ScreenName
from sincity.model.state import (
    ActionAssemblyState,
    CardHintFlashState,
    GameState,
    ModalFrame,
    SelectedInputState,
)

from sincity.game.queries import get_action_for_state
from sincity.model.defs import CheckValuePart, CheckValueBreakdown

from sincity.rules.deck import list_spirit_slots


# ── Internal helpers needed by other game modules ─────────────────

SUIT_LABEL_MAP = {
    "force": "暴力",
    "charm": "魅力",
    "knowledge": "知识",
    "sense": "敏锐",
    "wound": "流血",
    "shock": "惊悸",
}


def _suit_label(suit) -> str:
    from sincity.model.enums import Suit
    if suit == Suit.FORCE:
        return "暴力"
    if suit == Suit.CHARM:
        return "魅力"
    if suit == Suit.KNOWLEDGE:
        return "知识"
    if suit == Suit.SENSE:
        return "敏锐"
    if suit == Suit.WOUND:
        return "流血"
    if suit == Suit.SHOCK:
        return "惊悸"
    return str(suit)


def _all_spirit_slots(state: GameState) -> list[str]:
    return list_spirit_slots(state.deck)


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


def _slot_can_execute_check(state: GameState, slot_id: str, check) -> bool:
    from sincity.game.encounters import _sync_encounter_action_cycle
    _sync_encounter_action_cycle(state)
    if not _slot_can_spend_energy(state, slot_id):
        return False
    return slot_effective_value(state, slot_id, check) > 0


def _slot_can_spend_energy(state: GameState, slot_id: str) -> bool:
    from sincity.game.encounters import _sync_encounter_action_cycle
    _sync_encounter_action_cycle(state)
    if not slot_is_available(state, slot_id):
        return False
    return True


# ── Modal state ────────────────────────────────────────────────────

def open_action(state: GameState, action_id: str, modal_kind: str = "action") -> None:
    # toggle: clicking the same action clears assembly
    if state.assembly.action_id == action_id and state.modal.kind == modal_kind:
        clear_assembly(state)
        clear_selected_input(state)
        state.modal.kind = ""
        state.modal.primary_id = None
        return
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    state.assembly = ActionAssemblyState(action_id=action_id)
    state.selected_input = SelectedInputState()
    state.modal.kind = modal_kind
    state.modal.primary_id = action_id


def open_modal(state: GameState, kind: str, primary_id: str | None = None) -> None:
    from sincity.game.resolution import dismiss_pending_resolution
    dismiss_pending_resolution(state)
    clear_action_reveal(state)
    state.modal.stacked_frames.clear()
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    state.modal.kind = kind
    state.modal.primary_id = primary_id
    if kind == "location" and primary_id is not None and state.screen == ScreenName.CITY:
        state.world.fresh_locations.discard(primary_id)
    if kind != "action":
        clear_assembly(state)
        clear_selected_input(state)


def open_overlay(state: GameState, kind: str, primary_id: str | None = None) -> None:
    from sincity.game.resolution import dismiss_pending_resolution
    dismiss_pending_resolution(state)
    clear_action_reveal(state)
    assert state.modal.kind, "overlay requires an active base modal"
    state.modal.stacked_frames.append(ModalFrame(kind=state.modal.kind, primary_id=state.modal.primary_id))
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    state.modal.kind = kind
    state.modal.primary_id = primary_id


def close_modal(state: GameState) -> None:
    from sincity.game.dialogues import _clear_dialogue_modal
    from sincity.game.resolution import dismiss_pending_resolution
    dismiss_pending_resolution(state)
    if state.modal.kind == "dialogue":
        _clear_dialogue_modal(state)
        return
    if state.modal.stacked_frames:
        frame = state.modal.stacked_frames.pop()
        state.modal.kind = frame.kind
        state.modal.primary_id = frame.primary_id
        state.modal.return_kind = ""
        state.modal.return_primary_id = None
        return
    state.modal.kind = ""
    state.modal.primary_id = None
    clear_assembly(state)
    clear_selected_input(state)


def focus_action(state: GameState, action_id: str) -> None:
    if state.assembly.action_id == action_id:
        return
    clear_action_reveal(state)
    state.assembly = ActionAssemblyState(action_id=action_id)


def clear_assembly(state: GameState) -> None:
    clear_action_reveal(state)
    state.assembly = ActionAssemblyState()


def clear_selected_input(state: GameState) -> None:
    state.selected_input = SelectedInputState()


# ── Action reveal state ────────────────────────────────────────────

def clear_action_reveal(state: GameState) -> None:
    state.action_reveal = None


# ── Card hint flash ────────────────────────────────────────────────

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


# ── Growth (re-exported from session for UI convenience) ────────────────

def claim_growth(state: GameState, growth_id: str) -> None:
    from sincity.game.session import claim_growth
    claim_growth(state, growth_id)


# ── Input selection ────────────────────────────────────────────────

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


# ── Slot query helpers ─────────────────────────────────────────────

def slot_owner(slot_id: str) -> str:
    owner, _, _ = slot_id.partition(":")
    assert owner, f"Unknown action card: {slot_id}"
    return owner


def slot_base_raw_value(state: GameState, slot_id: str) -> int:
    return state.deck.action_card_values.get(slot_id, 0)


def slot_base_value(state: GameState, slot_id: str) -> int:
    return state.deck.action_card_values.get(slot_id, 0)


def slot_current_value(state: GameState, slot_id: str) -> int:
    return max(0, slot_base_value(state, slot_id) + state.deck.action_card_bonuses.get(slot_id, 0) + state.deck.action_card_penalties.get(slot_id, 0))


def slot_trauma_count(state: GameState, slot_id: str) -> int:
    return max(0, slot_base_raw_value(state, slot_id) - slot_base_value(state, slot_id))


def slot_is_available(state: GameState, slot_id: str) -> bool:
    if slot_id not in state.deck.available_slots:
        return False
    owner_id = slot_owner(slot_id)
    actor = state.party.get(owner_id)
    if actor is not None and not actor.can_act:
        return False
    return True


def slot_is_exhausted(state: GameState, slot_id: str) -> bool:
    return slot_id in state.deck.exhausted_slots


def slot_is_locked(state: GameState, slot_id: str) -> bool:
    return slot_id in state.deck.locked_slots


def count_spirit_cards(state: GameState) -> dict[str, int]:
    return {
        attr: 1 + state.deck.extra_slots.get(attr, 0)
        for attr in ("force", "charm", "knowledge", "sense")
    }


# ── Assembly queries ───────────────────────────────────────────────

def requirement_is_slotted(state: GameState, requirement: InputRequirement) -> bool:
    if requirement.kind == "card":
        if requirement.key == "negative":
            return False
        card_id = _slotted_card_id(state)
        return card_id is not None and slot_is_available(state, card_id)
    if requirement.kind == "item":
        return state.assembly.slotted_items.get(requirement.key, 0) >= requirement.amount
    raise AssertionError(f"Unsupported requirement kind: {requirement.kind}")


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
        from sincity.game.fields import field_value
        return selected.kind == "item" and selected.key == requirement.key and int(field_value(state, requirement.key)) >= requirement.amount
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
        from sincity.game.fields import field_value
        amount = field_value(state, requirement.key)
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
        from sincity.game.fields import field_value
        if state.assembly.slotted_items.get(requirement.key, 0) >= requirement.amount:
            state.assembly.slotted_items.pop(requirement.key, None)
        elif int(field_value(state, requirement.key)) >= requirement.amount:
            state.assembly.slotted_items[requirement.key] = requirement.amount


def action_ready_to_execute(action: ActionDef, state: GameState) -> bool:
    from sincity.game.conditions import action_is_available
    if not action_is_available(action, state):
        return False
    if action.check is None and not action.effects and action.reveal is None:
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


# ── Action classification ─────────────────────────────────────────

def action_requires_energy_slot(action: ActionDef) -> bool:
    return action.check is not None


def action_is_direct(action: ActionDef) -> bool:
    return action.check is None and not action.inputs


def action_is_reveal(action: ActionDef) -> bool:
    return action_is_direct(action) and action.reveal is not None


def action_is_instant(action: ActionDef) -> bool:
    return action_is_direct(action) and action.reveal is None and bool(action.effects)


# ── Slot value computation ────────────────────────────────────────

def slot_effective_value(state: GameState, slot_id: str, check) -> int:
    return slot_value_breakdown(state, slot_id, check).total


def slot_value_breakdown(state: GameState, slot_id: str, check):
    from sincity.game.fields import _actor_attribute_value, actor_name
    from sincity.game.judgment import compute_action_value
    base_value = slot_current_value(state, slot_id)
    owner_id = state.deck.action_card_owners.get(slot_id, slot_owner(slot_id))
    actor_part = CheckValuePart(label=f"{actor_name(state, owner_id)} {_suit_label(check.suit)}", value=_actor_attribute_value(state, owner_id, check.suit), source="actor", actor_id=owner_id)
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
