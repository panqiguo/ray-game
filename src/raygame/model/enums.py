from __future__ import annotations

from enum import Enum


class Suit(str, Enum):
    LOGIC = "logic"
    PERCEPTION = "perception"
    WILLPOWER = "willpower"
    WOUND = "wound"
    SHOCK = "shock"


class Risk(str, Enum):
    NONE = "none"
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class ResultType(str, Enum):
    FAIL = "fail"
    COST = "cost"
    SUCCESS = "success"


class ScreenName(str, Enum):
    CITY = "city"
    ENCOUNTER = "encounter"
    ENDING = "ending"


SUIT_LABELS = {
    Suit.LOGIC: "逻辑",
    Suit.PERCEPTION: "感知",
    Suit.WILLPOWER: "意志",
    Suit.WOUND: "流血",
    Suit.SHOCK: "惊悸",
}

RISK_LABELS = {
    Risk.NONE: "无风险",
    Risk.LOW: "低风险",
    Risk.MID: "中风险",
    Risk.HIGH: "高风险",
}
