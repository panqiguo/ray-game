from __future__ import annotations

from raygame.model.defs import CardDef
from raygame.model.enums import Suit


CARD_DEFS: dict[str, CardDef] = {
    "reason_0_a": CardDef("reason_0_a", "理性", Suit.REASON, 0, "冷静拆解眼前的问题。"),
    "reason_0_b": CardDef("reason_0_b", "理性", Suit.REASON, 0, "把线索重新排好顺序。"),
    "reason_0_c": CardDef("reason_0_c", "理性", Suit.REASON, 0, "先想清楚再动手。"),
    "instinct_0_a": CardDef("instinct_0_a", "直觉", Suit.INSTINCT, 0, "嗅到异常的流向。"),
    "instinct_0_b": CardDef("instinct_0_b", "直觉", Suit.INSTINCT, 0, "靠身体先一步反应。"),
    "instinct_0_c": CardDef("instinct_0_c", "直觉", Suit.INSTINCT, 0, "从碎片里闻出不对劲。"),
    "empathy_0_a": CardDef("empathy_0_a", "共情", Suit.EMPATHY, 0, "试着站在对方那边。"),
    "empathy_0_b": CardDef("empathy_0_b", "共情", Suit.EMPATHY, 0, "先让对方松口气。"),
    "empathy_0_c": CardDef("empathy_0_c", "共情", Suit.EMPATHY, 0, "把语气压低一点。"),
    "force_0_a": CardDef("force_0_a", "强硬", Suit.FORCE, 0, "硬着头皮也得上。"),
    "force_0_b": CardDef("force_0_b", "强硬", Suit.FORCE, 0, "牙咬住，先把事做成。"),
    "force_0_c": CardDef("force_0_c", "强硬", Suit.FORCE, 0, "今天没耐心。"),
    "paranoid_reason_1": CardDef("paranoid_reason_1", "偏执专长·理性", Suit.REASON, 1, "这张基础牌被偏执磨出锋刃。"),
    "paranoid_instinct_1": CardDef("paranoid_instinct_1", "偏执专长·直觉", Suit.INSTINCT, 1, "这张基础牌被偏执磨出锋刃。"),
    "paranoid_empathy_1": CardDef("paranoid_empathy_1", "偏执专长·共情", Suit.EMPATHY, 1, "这张基础牌被偏执磨出锋刃。"),
    "paranoid_force_1": CardDef("paranoid_force_1", "偏执专长·强硬", Suit.FORCE, 1, "这张基础牌被偏执磨出锋刃。"),
    "bleeding": CardDef("bleeding", "流血", Suit.WOUND, 0, "伤口不停提醒你。", is_negative=True, negative_family="physical"),
    "bite": CardDef("bite", "咬伤", Suit.WOUND, 0, "犬齿留下了热痛。", is_negative=True, negative_family="physical"),
    "fatigue": CardDef("fatigue", "疲惫", Suit.SHOCK, 0, "眼前像隔着一层雨幕。", is_negative=True, negative_family="mental"),
    "panic": CardDef("panic", "惊悸", Suit.SHOCK, 0, "心跳大得像会把人出卖。", is_negative=True, negative_family="mental"),
}

STARTING_DECK: list[str] = [
    "reason_0_a",
    "reason_0_b",
    "reason_0_c",
    "instinct_0_a",
    "instinct_0_b",
    "instinct_0_c",
    "empathy_0_a",
    "empathy_0_b",
    "empathy_0_c",
    "force_0_a",
    "force_0_b",
    "force_0_c",
]

