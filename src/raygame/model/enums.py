from __future__ import annotations

from enum import Enum


class Suit(str, Enum):
    REASON = "reason"
    INSTINCT = "instinct"
    EMPATHY = "empathy"
    FORCE = "force"
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
    MISSION = "mission"
    ENDING = "ending"


class AreaName(str, Enum):
    PERIMETER = "perimeter"
    CORRIDOR = "corridor"
    FREEZER = "freezer"


SUIT_LABELS = {
    Suit.REASON: "理性",
    Suit.INSTINCT: "直觉",
    Suit.EMPATHY: "共情",
    Suit.FORCE: "强硬",
    Suit.WOUND: "流血",
    Suit.SHOCK: "惊悸",
}

RISK_LABELS = {
    Risk.NONE: "无风险",
    Risk.LOW: "低风险",
    Risk.MID: "中风险",
    Risk.HIGH: "高风险",
}

