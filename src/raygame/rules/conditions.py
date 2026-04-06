from __future__ import annotations

from raygame.model.defs import Condition
from raygame.model.enums import ScreenName
from raygame.model.state import GameState


def evaluate(condition: Condition, state: GameState) -> bool:
    value = condition.value
    if condition.kind == "has_clue":
        return isinstance(value, str) and value in state.clues
    if condition.kind == "has_item":
        return isinstance(value, str) and value in state.items
    if condition.kind == "clock_at_least":
        assert isinstance(value, str)
        clock_name, raw_amount = value.split(":")
        amount = int(raw_amount)
        return getattr(state.clocks, clock_name) >= amount
    if condition.kind == "flag_set":
        return isinstance(value, str) and value in state.flags
    if condition.kind == "flag_not_set":
        return isinstance(value, str) and value not in state.flags
    if condition.kind == "action_done":
        return isinstance(value, str) and value in state.mission.completed_actions
    if condition.kind == "mode_is":
        return state.screen == ScreenName(value)
    if condition.kind == "day_at_least":
        return state.day >= int(value)
    if condition.kind == "day_at_most":
        return state.day <= int(value)
    if condition.kind == "if_clue_reduce":
        return True
    if condition.kind == "resource_at_most":
        assert isinstance(value, str)
        resource_name, raw_amount = value.split(":")
        amount = int(raw_amount)
        return getattr(state.resources, resource_name) <= amount
    raise AssertionError(f"Unsupported condition {condition.kind}")


def all_met(conditions: tuple[Condition, ...], state: GameState) -> bool:
    return all(evaluate(condition, state) for condition in conditions)

