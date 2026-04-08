from __future__ import annotations

from dataclasses import dataclass, field

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rendering import draw_text

from .ui_core import clickable, draw_frame
from .ui_tags import draw_action_corner_clocks, draw_clock_badges, draw_corner_labels


@dataclass(frozen=True)
class TableCardStyle:
    width: float
    height: float
    title_size: int
    body_size: int


@dataclass(frozen=True)
class TableCardModel:
    title: str
    body: str
    labels: tuple[str, ...] = ()
    clock_ids: tuple[str, ...] = ()
    metadata: tuple[str, ...] = ()
    active: bool = False
    disabled: bool = False
    interactive: bool = True
    style: TableCardStyle = field(default_factory=lambda: TABLE_CARD)


WORLD_CARD = TableCardStyle(width=188.0, height=96.0, title_size=22, body_size=16)
TABLE_CARD = TableCardStyle(width=188.0, height=96.0, title_size=22, body_size=16)
ACTION_CARD = TableCardStyle(width=232.0, height=224.0, title_size=22, body_size=15)


def draw_table_card(font: Font | None, rect: Rectangle, state: GameState, model: TableCardModel) -> bool:
    fill = Color(72, 57, 42, 255) if model.active else Color(28, 32, 40, 255)
    border = Color(191, 157, 96, 255) if model.active else Color(92, 96, 104, 220)
    if model.disabled:
        fill = Color(22, 24, 30, 240)
        border = Color(62, 66, 74, 180)
    clicked = clickable(rect) if model.interactive and not model.disabled else False
    draw_frame(rect, fill, border)
    draw_text(
        font,
        model.title,
        int(rect.x) + 14,
        int(rect.y) + 14,
        model.style.title_size,
        RAYWHITE if not model.disabled else Color(120, 120, 120, 255),
    )
    draw_text(
        font,
        model.body,
        int(rect.x) + 14,
        int(rect.y) + 42,
        model.style.body_size,
        LIGHTGRAY if not model.disabled else Color(98, 98, 98, 255),
    )
    meta_y = int(rect.y) + 42 + model.style.body_size + 14
    for line in model.metadata:
        draw_text(font, line, int(rect.x) + 14, meta_y, 14, Color(198, 198, 198, 255))
        meta_y += 20
    if model.clock_ids:
        draw_action_corner_clocks(rect, model.clock_ids, state, align="left")
        draw_clock_badges(font, rect, model.clock_ids, state, outside=True)
    if model.labels:
        draw_corner_labels(font, rect, model.labels, "right")
    return clicked
