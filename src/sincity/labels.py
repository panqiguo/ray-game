from __future__ import annotations

from sincity.model.items import ITEMS


def lookup_input_label(key: str) -> str:
    item = ITEMS.get(key)
    assert item, f"Missing item definition for key: {key}"
    return item.name
