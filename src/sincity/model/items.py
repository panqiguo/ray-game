from __future__ import annotations

from .defs import ItemDef


ITEMS: dict[str, ItemDef] = {
    # ── 金钱 ──
    "money": ItemDef(key="money", name="美元", type="金钱"),

    # ── 食物 ──
    "food": ItemDef(key="food", name="干粮", type="食物"),

    # ── 药品 ──
    "first_aid": ItemDef(key="first_aid", name="药品", type="药品"),

    # --- 材料 ---
    "废料" : ItemDef(key="scrap", name="废料", type="材料"),
    "零件" : ItemDef(key="part", name="零件", type="材料"),

    # ── 效果 ──
    "cigarettes": ItemDef(key="cigarettes", name="卷烟", type="效果"),
    "liquor": ItemDef(key="liquor", name="便宜酒", type="效果"),
    "clothes": ItemDef(key="clothes", name="西装", type="效果"),

    "gun": ItemDef(key="gun", name="枪", type="特殊用途物品"),
    "tools": ItemDef(key="tools", name="工具", type="特殊用途物品"),
    "lockpick": ItemDef(key="lockpick", name="开锁器", type="特殊用途物品"),

    # ── 特殊用途物品 ──
        "hotel_pass": ItemDef(key="hotel_pass", name="房卡", type="特殊用途物品"),
    "car_key": ItemDef(key="car_key", name="车钥匙", type="特殊用途物品"),
    "fake_id": ItemDef(key="fake_id", name="假证件", type="特殊用途物品"),
    "passage_ticket": ItemDef(key="passage_ticket", name="船票", type="特殊用途物品"),
    "repair_case_item": ItemDef(key="repair_case_item", name="任务道具", type="特殊用途物品"),
    "mysterious_item": ItemDef(key="mysterious_item", name="神秘物品", type="特殊用途物品"),
    "wounded_man_lead": ItemDef(key="wounded_man_lead", name="死者线索", type="特殊用途物品"),
    "criminal_clue": ItemDef(key="criminal_clue", name="罪案线索", type="特殊用途物品"),
}
