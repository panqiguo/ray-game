from __future__ import annotations

from raygame.model.defs import CardDef
from raygame.model.enums import Suit


CARD_DEFS: dict[str, CardDef] = {
    "reason_0_a": CardDef("reason_0_a", "理性", Suit.REASON, 0, "冷静拆解眼前的问题。"),
    "instinct_0_a": CardDef("instinct_0_a", "直觉", Suit.INSTINCT, 0, "嗅到异常的流向。"),
    "empathy_0_a": CardDef("empathy_0_a", "共情", Suit.EMPATHY, 0, "试着站在对方那边。"),
    "force_0_a": CardDef("force_0_a", "强硬", Suit.FORCE, 0, "硬着头皮也得上。"),
    "paranoid_reason_1": CardDef("paranoid_reason_1", "偏执专长·理性", Suit.REASON, 1, "这张基础牌被偏执磨出锋刃。"),
    "paranoid_instinct_1": CardDef("paranoid_instinct_1", "偏执专长·直觉", Suit.INSTINCT, 1, "这张基础牌被偏执磨出锋刃。"),
    "paranoid_empathy_1": CardDef("paranoid_empathy_1", "偏执专长·共情", Suit.EMPATHY, 1, "这张基础牌被偏执磨出锋刃。"),
    "paranoid_force_1": CardDef("paranoid_force_1", "偏执专长·强硬", Suit.FORCE, 1, "这张基础牌被偏执磨出锋刃。"),
    "trauma": CardDef("trauma", "创伤", Suit.WOUND, 0, "失血与旧痛会在任何时刻打断你。", is_negative=True, negative_family="physical"),
    "bleeding": CardDef("bleeding", "流血", Suit.WOUND, 0, "伤口不停提醒你。", is_negative=True, negative_family="physical"),
    "bite": CardDef("bite", "咬伤", Suit.WOUND, 0, "犬齿留下了热痛。", is_negative=True, negative_family="physical"),
    "fatigue": CardDef("fatigue", "疲惫", Suit.SHOCK, 0, "眼前像隔着一层雨幕。", is_negative=True, negative_family="mental"),
    "panic": CardDef("panic", "惊悸", Suit.SHOCK, 0, "心跳大得像会把人出卖。", is_negative=True, negative_family="mental"),
}

STARTING_DECK: list[str] = [
    "reason_0_a",
    "instinct_0_a",
    "empathy_0_a",
    "force_0_a",
]
