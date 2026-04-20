from __future__ import annotations

from raygame.model.defs import CardDef
from raygame.model.enums import Suit


CARD_DEFS: dict[str, CardDef] = {
    "logic": CardDef("logic", "基础·逻辑", Suit.LOGIC, 2, "你先把思路稳住。"),
    "perception": CardDef("perception", "基础·感知", Suit.PERCEPTION, 2, "你让自己先捕捉那些细微而危险的变化。"),
    "willpower": CardDef("willpower", "基础·意志", Suit.WILLPOWER, 2, "你把迟疑压下去，让心神硬顶住局面。"),
    "trauma": CardDef("trauma", "创伤", Suit.WOUND, 0, "旧伤会在最不该颤的时候让你发抖。", is_negative=True, negative_family="physical"),
    "bleeding": CardDef("bleeding", "流血", Suit.WOUND, 1, "伤口一直在提醒你别动作太大。", is_negative=True, negative_family="physical"),
    "bite": CardDef("bite", "咬伤", Suit.WOUND, 1, "犬齿留下的热痛让动作发虚。", is_negative=True, negative_family="physical"),
    "fatigue": CardDef("fatigue", "疲惫", Suit.SHOCK, 1, "眼前像隔着一层雨幕。", is_negative=True, negative_family="mental"),
    "panic": CardDef("panic", "惊悸", Suit.SHOCK, 1, "心跳大得像会把人出卖。", is_negative=True, negative_family="mental"),
}

STARTING_DECK: list[str] = [
    "logic",
    "logic",
    "logic",
    "perception",
    "perception",
    "perception",
    "willpower",
    "willpower",
    "willpower",
]
