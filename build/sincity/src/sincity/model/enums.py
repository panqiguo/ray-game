from __future__ import annotations

from enum import Enum


class Suit(str, Enum):
    FORCE = "force"
    CHARM = "charm"
    KNOWLEDGE = "knowledge"
    SENSE = "sense"
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
    Suit.FORCE: "暴力",
    Suit.CHARM: "魅力",
    Suit.KNOWLEDGE: "知识",
    Suit.SENSE: "敏锐",
    Suit.WOUND: "流血",
    Suit.SHOCK: "惊悸",
}

RISK_LABELS = {
    Risk.NONE: "无风险",
    Risk.LOW: "低风险",
    Risk.MID: "中风险",
    Risk.HIGH: "高风险",
}
