from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TextLevel = Literal["title", "subtitle", "body", "body_sm", "caption"]


@dataclass(frozen=True)
class TextLevelSpec:
    size: int
    line_height: int


_LEVEL_SPECS: dict[TextLevel, TextLevelSpec] = {
    "title": TextLevelSpec(size=30, line_height=36),
    "subtitle": TextLevelSpec(size=24, line_height=30),
    "body": TextLevelSpec(size=16, line_height=22),
    "body_sm": TextLevelSpec(size=14, line_height=18),
    "caption": TextLevelSpec(size=12, line_height=16),
}


def ui_text_size(level: TextLevel) -> int:
    return _LEVEL_SPECS[level].size
