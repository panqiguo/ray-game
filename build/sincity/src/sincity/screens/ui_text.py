from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pyray import *  # type: ignore


TextLevel = Literal["title", "subtitle", "body", "body_sm", "caption"]
TextTone = Literal["default", "muted", "subtle", "accent", "danger", "warning", "disabled"]


@dataclass(frozen=True)
class TextLevelSpec:
    size: int
    line_height: int


@dataclass(frozen=True)
class UiTextStyle:
    size: int
    line_height: int
    color: Color


_LEVEL_SPECS: dict[TextLevel, TextLevelSpec] = {
    "title": TextLevelSpec(size=30, line_height=36),
    "subtitle": TextLevelSpec(size=24, line_height=30),
    "body": TextLevelSpec(size=16, line_height=22),
    "body_sm": TextLevelSpec(size=14, line_height=18),
    "caption": TextLevelSpec(size=12, line_height=16),
}

_TONE_COLORS: dict[TextTone, Color] = {
    "default": Color(245, 245, 245, 255),
    "muted": Color(200, 200, 200, 255),
    "subtle": Color(170, 170, 170, 255),
    "accent": Color(212, 196, 132, 255),
    "danger": Color(220, 110, 110, 255),
    "warning": Color(224, 196, 104, 255),
    "disabled": Color(118, 118, 118, 255),
}


def ui_text_style(
    level: TextLevel,
    tone: TextTone = "default",
    *,
    scale: float = 1.0,
    color: Color | None = None,
    minimum_size: int | None = None,
    minimum_line_height: int | None = None,
) -> UiTextStyle:
    size = ui_text_size(level, scale=scale, minimum_size=minimum_size)
    line_height = ui_line_height(level, scale=scale, minimum_line_height=minimum_line_height)
    return UiTextStyle(size=size, line_height=line_height, color=(color if color is not None else ui_text_color(tone)))


def ui_text_size(level: TextLevel, *, scale: float = 1.0, minimum_size: int | None = None) -> int:
    spec = _LEVEL_SPECS[level]
    size = max(1, int(round(spec.size * scale)))
    if minimum_size is not None:
        size = max(size, minimum_size)
    return size


def ui_line_height(level: TextLevel, *, scale: float = 1.0, minimum_line_height: int | None = None) -> int:
    spec = _LEVEL_SPECS[level]
    line_height = max(1, int(round(spec.line_height * scale)))
    if minimum_line_height is not None:
        line_height = max(line_height, minimum_line_height)
    return line_height


def ui_text_color(tone: TextTone) -> Color:
    return _TONE_COLORS[tone]
