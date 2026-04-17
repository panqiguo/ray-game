from __future__ import annotations

from dataclasses import dataclass, field

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rendering import draw_text

from .ui_core import clickable, draw_frame, measure_text_width, wrap_text_lines_any
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
ACTION_CARD = TableCardStyle(width=232.0, height=224.0, title_size=22, body_size=17)


def draw_table_card(font: Font | None, rect: Rectangle, state: GameState, model: TableCardModel, scale: float = 1.0) -> bool:
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
        int(rect.x + 14 * scale),
        int(rect.y + 14 * scale),
        max(10, int(round(model.style.title_size * scale))),
        RAYWHITE if not model.disabled else Color(120, 120, 120, 255),
    )
    body_size = max(9, int(round(model.style.body_size * scale)))
    body_x = int(rect.x + 14 * scale)
    body_y = int(rect.y + 42 * scale)
    body_w = max(1.0, rect.width - 28 * scale)
    line_h = max(12, int(round(body_size + 2)))
    reserved_meta = int(round(24 * scale)) if len(model.metadata) == 2 else len(model.metadata) * int(round(20 * scale))
    max_body_bottom = rect.y + rect.height - (10 * scale) - reserved_meta
    max_lines = max(1, int((max_body_bottom - body_y) // line_h))
    body_lines = wrap_text_lines_any(font, model.body, body_w, body_size)[:max_lines]
    for index, line in enumerate(body_lines):
        draw_text(
            font,
            line,
            body_x,
            body_y + index * line_h,
            body_size,
            LIGHTGRAY if not model.disabled else Color(98, 98, 98, 255),
        )
    meta_y = int(body_y + len(body_lines) * line_h + int(round(10 * scale)))
    if len(model.metadata) == 2:
        draw_action_metadata(font, rect, model, meta_y, scale=scale)
    else:
        for line in model.metadata:
            draw_text(font, line, int(rect.x + 14 * scale), meta_y, max(9, int(round(14 * scale))), Color(198, 198, 198, 255))
            meta_y += int(round(20 * scale))
    if model.clock_ids:
        draw_action_corner_clocks(rect, model.clock_ids, state, align="left", scale=scale)
        draw_clock_badges(font, rect, model.clock_ids, state, outside=True, scale=scale)
    if model.labels:
        draw_corner_labels(font, rect, model.labels, "right", scale=scale)
    return clicked


def draw_action_metadata(font: Font | None, rect: Rectangle, model: TableCardModel, meta_y: int, scale: float = 1.0) -> None:
    suit_label, risk_label = model.metadata
    label_size = max(10, int(round(15 * scale)))
    padding_x = 12.0 * scale
    padding_y = 5.0 * scale
    suit_width = max(56.0 * scale, measure_text_width(font, suit_label, label_size) + padding_x * 2)
    suit_rect = Rectangle(rect.x + 14.0 * scale, meta_y, suit_width, 22.0 * scale)
    draw_frame(suit_rect, Color(18, 20, 26, 255), Color(168, 168, 168, 220))
    draw_text(font, suit_label, int(suit_rect.x + padding_x), int(suit_rect.y + padding_y - 1), label_size, RAYWHITE)

    risk_color = _risk_text_color(risk_label)
    risk_width = measure_text_width(font, risk_label, label_size)
    risk_x = rect.x + rect.width - 14.0 * scale - risk_width
    draw_text(font, risk_label, int(risk_x), meta_y, label_size, risk_color)


def _risk_text_color(label: str) -> Color:
    if label == "中风险":
        return Color(224, 196, 104, 255)
    if label == "高风险":
        return Color(220, 110, 110, 255)
    return RAYWHITE
