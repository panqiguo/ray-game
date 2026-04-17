from __future__ import annotations

from raygame.model.defs import CardDef
from raygame.model.enums import Suit


CARD_DEFS: dict[str, CardDef] = {
    "reason_0_a": CardDef("reason_0_a", "基础·理性", Suit.REASON, 2, "你先把思路稳住。"),
    "instinct_0_a": CardDef("instinct_0_a", "基础·直觉", Suit.INSTINCT, 2, "你让身体先替你察觉不对。"),
    "empathy_0_a": CardDef("empathy_0_a", "基础·感知", Suit.EMPATHY, 2, "你试着贴近对方真正的情绪。"),
    "force_0_a": CardDef("force_0_a", "基础·强硬", Suit.FORCE, 2, "你把迟疑压下去，先顶上去。"),
    "reason_1_a": CardDef("reason_1_a", "热情·理性", Suit.REASON, 3, "线索忽然在脑中咬合起来。"),
    "instinct_1_a": CardDef("instinct_1_a", "热情·直觉", Suit.INSTINCT, 3, "你几乎立刻闻到了危险。"),
    "empathy_1_a": CardDef("empathy_1_a", "热情·感知", Suit.EMPATHY, 3, "你一下就抓住了对方最松动的地方。"),
    "force_1_a": CardDef("force_1_a", "热情·强硬", Suit.FORCE, 3, "你不再犹豫，整个人往前压过去。"),
    "reason_2_a": CardDef("reason_2_a", "灵感·理性", Suit.REASON, 4, "所有碎片突然排成了一条路。"),
    "instinct_2_a": CardDef("instinct_2_a", "灵感·直觉", Suit.INSTINCT, 4, "你几乎像提前看见了下一秒。"),
    "empathy_2_a": CardDef("empathy_2_a", "灵感·感知", Suit.EMPATHY, 4, "你在沉默里听见了真正的话。"),
    "force_2_a": CardDef("force_2_a", "灵感·强硬", Suit.FORCE, 4, "那一瞬间你比恐惧更快。"),
    "paranoid_reason_1": CardDef("paranoid_reason_1", "偏执专长·理性", Suit.REASON, 3, "偏执让这张牌变得比平静更锋利。"),
    "paranoid_instinct_1": CardDef("paranoid_instinct_1", "偏执专长·直觉", Suit.INSTINCT, 3, "偏执让这张牌变得比平静更锋利。"),
    "paranoid_empathy_1": CardDef("paranoid_empathy_1", "偏执专长·感知", Suit.EMPATHY, 3, "偏执让这张牌变得比平静更锋利。"),
    "paranoid_force_1": CardDef("paranoid_force_1", "偏执专长·强硬", Suit.FORCE, 3, "偏执让这张牌变得比平静更锋利。"),
    "trauma": CardDef("trauma", "创伤", Suit.WOUND, 0, "旧伤会在最不该颤的时候让你发抖。", is_negative=True, negative_family="physical"),
    "bleeding": CardDef("bleeding", "流血", Suit.WOUND, 1, "伤口一直在提醒你别动作太大。", is_negative=True, negative_family="physical"),
    "bite": CardDef("bite", "咬伤", Suit.WOUND, 1, "犬齿留下的热痛让动作发虚。", is_negative=True, negative_family="physical"),
    "fatigue": CardDef("fatigue", "疲惫", Suit.SHOCK, 1, "眼前像隔着一层雨幕。", is_negative=True, negative_family="mental"),
    "panic": CardDef("panic", "惊悸", Suit.SHOCK, 1, "心跳大得像会把人出卖。", is_negative=True, negative_family="mental"),
}

STARTING_DECK: list[str] = [
    "reason_0_a",
    "instinct_0_a",
    "empathy_0_a",
    "force_0_a",
    "reason_1_a",
    "instinct_1_a",
    "empathy_1_a",
    "force_1_a",
]
