from __future__ import annotations


ITEM_LABELS = {
    "money": "美元",
    "cigarettes": "卷烟",
    "clothes": "西装",
    "hotel_pass": "房卡",
    "car_key": "车钥匙",
    "repair_case_item": "任务道具",
    "gun": "枪",
    "food": "干粮",
    "liquor": "便宜酒",
    "fake_id": "假证件",
    "passage_ticket": "船票",
    "first_aid": "药品",
    "tools": "工具",
    "mysterious_item": "神秘物品",
    "wounded_man_lead": "死者线索",
}


def lookup_input_label(key: str) -> str:
    label = ITEM_LABELS.get(key)
    assert label, f"Missing input label for key: {key}"
    return label
