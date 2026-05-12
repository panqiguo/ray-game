from __future__ import annotations

from sincity.model.defs import CheckDef
from sincity.model.enums import ResultType

RESULT_TABLE: dict[int, tuple[ResultType, ...]] = {
    1: (ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.COST, ResultType.SUCCESS),
    2: (ResultType.FAIL, ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS),
    3: (ResultType.FAIL, ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
    4: (ResultType.COST, ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
    5: (ResultType.COST, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS, ResultType.SUCCESS),
}


def clamp_action_value(action_value: int) -> int:
    return max(1, min(5, action_value))


def compute_action_value(slot_value: int, check: CheckDef, *, preferred: bool | None) -> int:
    modifier = 0
    if preferred is True:
        modifier = 2
    return clamp_action_value(slot_value + modifier)


def roll_result(action_value: int, die_roll: int) -> ResultType:
    clamped = clamp_action_value(action_value)
    return RESULT_TABLE[clamped][die_roll - 1]
