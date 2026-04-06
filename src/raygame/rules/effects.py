from __future__ import annotations

from raygame.content.cards import CARD_DEFS
from raygame.model.defs import Effect
from raygame.model.state import GameState

from .deck import remove_negative_cards, replace_first_base_card


def _stress_overflow(state: GameState) -> None:
    if state.resources.stress < state.resources.max_stress:
        return
    state.resources.stress = max(0, state.resources.max_stress - 2)
    state.deck.discard_pile.append("panic")
    state.action_log.append("Stress 满载，惊悸被塞回了牌库。")


def apply_effect(effect: Effect, state: GameState) -> None:
    kind = effect.kind
    value = effect.value
    if kind == "gain_money":
        state.resources.money += int(value)
        return
    if kind == "spend_money":
        cost = int(value)
        assert state.resources.money >= cost, "Money is not enough"
        state.resources.money -= cost
        return
    if kind == "spend_all_money":
        state.resources.money = 0
        return
    if kind == "gain_cigarettes":
        state.resources.cigarettes += int(value)
        return
    if kind == "add_stress":
        state.resources.stress = min(state.resources.max_stress, state.resources.stress + int(value))
        _stress_overflow(state)
        return
    if kind == "lose_health":
        damage = int(value)
        state.resources.health -= damage
        if "enable_old_scars" in state.flags and not state.used_old_wound_buffer:
            state.used_old_wound_buffer = True
        else:
            state.deck.discard_pile.append("bleeding")
        if state.resources.health <= 0:
            state.flags.add("run_failed")
        return
    if kind == "insert_card":
        assert isinstance(value, str) and value in CARD_DEFS
        state.deck.discard_pile.append(value)
        return
    if kind == "remove_negative":
        remove_negative_cards(state.deck, int(value))
        return
    if kind == "remove_negative_family":
        removed = remove_negative_cards(state.deck, 1, str(value))
        assert removed > 0, f"No {value} negative card to remove"
        return
    if kind == "advance_clock":
        assert isinstance(value, str)
        clock_name, raw_amount = value.split(":")
        amount = int(raw_amount)
        current = getattr(state.clocks, clock_name)
        max_value = getattr(state.clocks, f"{clock_name}_max")
        setattr(state.clocks, clock_name, min(max_value, current + amount))
        return
    if kind == "freeze_clock":
        state.clocks.freeze_crow_time_once = True
        return
    if kind == "set_flag":
        assert isinstance(value, str)
        state.flags.add(value)
        if value.startswith("clue_"):
            state.clues.add(value)
        if value == "skip_guard":
            state.mission.skipped_guard = True
        if value == "lights_off":
            state.mission.lights_off = True
        if value == "evidence_unlocked":
            state.mission.evidence_unlocked = True
        if value == "freezer_shortcut":
            state.mission.freezer_shortcut = True
        if value == "crow_rescued":
            state.mission.crow_rescued = True
        if value == "crow_talked":
            state.mission.crow_talked = True
        if value in {"boss_force", "boss_deal", "boss_ledger", "boss_bypass"}:
            state.mission.boss_resolution = value
        return
    if kind == "give_item":
        assert isinstance(value, str)
        state.items.add(value)
        if value == "ledger":
            state.mission.ledger_found = True
        return
    if kind == "fail_run":
        state.flags.add("run_failed")
        return
    if kind == "increase_stress_cap":
        state.resources.max_stress += int(value)
        return
    if kind == "enable_casebook":
        state.flags.add("enable_casebook")
        return
    if kind == "enable_old_scars":
        state.flags.add("enable_old_scars")
        return
    if kind == "upgrade_card":
        upgraded = replace_first_base_card(state.deck, str(value), f"paranoid_{value}_1")
        assert upgraded, f"No base card for suit {value}"
        return
    raise AssertionError(f"Unsupported effect {kind}")


def apply_effects(effects: tuple[Effect, ...], state: GameState) -> None:
    for effect in effects:
        apply_effect(effect, state)

