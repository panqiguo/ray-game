from __future__ import annotations

from raygame.content.cards import CARD_DEFS
from raygame.model.defs import ActionMethodDef
from raygame.model.enums import ResultType, Suit


RESULT_TABLE: dict[int, tuple[ResultType, ...]] = {
    1: (ResultType.FAIL, ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.SUCCESS),
    2: (ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.COST, ResultType.SUCCESS),
    3: (ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS),
    4: (ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
    5: (ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
    6: (ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
}


def compute_action_value(
    card_id: str | None,
    method: ActionMethodDef,
    wildcard_suit: Suit | None = None,
    extra_bonus: int = 0,
) -> int:
    if card_id is None:
        return 0
    card = CARD_DEFS[card_id]
    if card.is_negative:
        return 0
    suit = wildcard_suit or card.suit
    # Current prototype follows the design mock: method difficulty provides the
    # baseline action value shown in the panel, matching suit pushes it up by 1.
    value = method.difficulty + card.points + extra_bonus + method.bonus
    if suit in method.suits:
        value += 1
    return max(1, min(6, value))


def roll_result(action_value: int, die_roll: int) -> ResultType:
    clamped = max(1, min(6, action_value))
    return RESULT_TABLE[clamped][die_roll - 1]
