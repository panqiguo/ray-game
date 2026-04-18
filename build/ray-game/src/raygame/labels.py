from __future__ import annotations


ITEM_LABELS = {
    "money": "美元",
    "cigarettes": "卷烟",
    "clothes": "西装",
    "hotel_pass": "房卡",
    "car_key": "车钥匙",
    "repair_case_item": "任务道具",
    "gun": "枪",
}


def lookup_input_label(key: str) -> str:
    label = ITEM_LABELS.get(key)
    assert label, f"Missing input label for key: {key}"
    return label
