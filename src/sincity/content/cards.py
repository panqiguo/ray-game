from __future__ import annotations

from sincity.model.defs import CardDef
from sincity.model.enums import Suit


CARD_DEFS: dict[str, CardDef] = {
    "force": CardDef("force", "暴力", Suit.FORCE, 1, "你用力量和压迫破开局面。"),
    "charm": CardDef("charm", "魅力", Suit.CHARM, 1, "你用语言和表情先铺好路。"),
    "knowledge": CardDef("knowledge", "知识", Suit.KNOWLEDGE, 1, "你让脑子走在手脚前面。"),
    "sense": CardDef("sense", "敏锐", Suit.SENSE, 1, "你让直觉先于判断捕捉危险。"),
    "trauma": CardDef("trauma", "创伤", Suit.WOUND, 0, "旧伤会在最不该颤的时候让你发抖。", is_negative=True, negative_family="physical"),
    "bleeding": CardDef("bleeding", "流血", Suit.WOUND, 1, "伤口一直在提醒你别动作太大。", is_negative=True, negative_family="physical"),
    "bite": CardDef("bite", "咬伤", Suit.WOUND, 1, "犬齿留下的热痛让动作发虚。", is_negative=True, negative_family="physical"),
    "fatigue": CardDef("fatigue", "疲惫", Suit.SHOCK, 1, "眼前像隔着一层雨幕。", is_negative=True, negative_family="mental"),
    "panic": CardDef("panic", "惊悸", Suit.SHOCK, 1, "心跳大得像会把人出卖。", is_negative=True, negative_family="mental"),
}
