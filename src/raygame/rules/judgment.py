from __future__ import annotations

from raygame.content.cards import CARD_DEFS
from raygame.model.defs import CheckDef
from raygame.model.enums import ResultType, Suit


MATCH_BONUS = 1

RESULT_TABLE: dict[int, tuple[ResultType, ...]] = {
    1: (ResultType.FAIL, ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.COST),
    2: (ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.COST, ResultType.SUCCESS),
    3: (ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS),
    4: (ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
}


def clamp_action_value(action_value: int) -> int:
    return max(1, min(4, action_value))


def compute_action_value(card_id: str | None, check: CheckDef, wildcard_suit: Suit | None = None) -> int:
    if card_id is None:
        return 0
    card = CARD_DEFS[card_id]
    suit = wildcard_suit or card.suit
    value = card.points
    if suit in check.suits:
        value += MATCH_BONUS
    return clamp_action_value(value)


def roll_result(action_value: int, die_roll: int) -> ResultType:
    clamped = clamp_action_value(action_value)
    return RESULT_TABLE[clamped][die_roll - 1]
