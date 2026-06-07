from __future__ import annotations

from dataclasses import dataclass, field

from pyray import *  # type: ignore

from sincity.model.state import GameState
from sincity.rendering import draw_text

from .ui_core import clickable, draw_frame, measure_text_width, wrap_text_lines_any
from .ui_text import ui_text_color, ui_text_size, ui_text_style
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


WORLD_CARD = TableCardStyle(width=188.0, height=96.0, title_size=ui_text_size("subtitle"), body_size=ui_text_size("body"))
TABLE_CARD = TableCardStyle(width=188.0, height=96.0, title_size=ui_text_size("subtitle"), body_size=ui_text_size("body"))
ACTION_CARD = TableCardStyle(width=232.0, height=224.0, title_size=ui_text_size("subtitle"), body_size=ui_text_size("body") + 2)


def draw_table_card(
    font: Font | None,
    rect: Rectangle,
    state: GameState,
    model: TableCardModel,
    scale: float = 1.0,
    *,
    z: int | None = None,
) -> bool:
    fill = Color(72, 57, 42, 255) if model.active else Color(28, 32, 40, 255)
    border = Color(191, 157, 96, 255) if model.active else Color(92, 96, 104, 220)
    if model.disabled:
        fill = Color(22, 24, 30, 240)
        border = Color(62, 66, 74, 180)
    clicked = clickable(rect, z=z) if model.interactive and not model.disabled else False
    draw_frame(rect, fill, border)
    title_style = ui_text_style(
        "subtitle",
        "disabled" if model.disabled else "default",
        scale=(model.style.title_size / ui_text_size("subtitle")) * scale,
        minimum_size=10,
    )
    draw_text(
        font,
        model.title,
        int(rect.x + 14 * scale),
        int(rect.y + 14 * scale),
        title_style.size,
        title_style.color if not model.disabled else ui_text_color("disabled"),
    )
    body_size = max(9, int(round(model.style.body_size * scale)))
    body_style = ui_text_style(
        "body",
        "disabled" if model.disabled else "muted",
        scale=(model.style.body_size / ui_text_size("body")) * scale,
        minimum_size=9,
    )
    body_x = int(rect.x + 14 * scale)
    body_y = int(rect.y + 42 * scale)
    body_w = max(1.0, rect.width - 28 * scale)
    line_h = max(12, body_style.line_height)
    reserved_meta = (
        int(round(24 * scale))
        if len(model.metadata) == 2
        else int(round((24 + max(0, len(model.metadata) - 2) * 20) * scale))
        if len(model.metadata) > 2
        else 0
    )
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
            body_style.color if not model.disabled else ui_text_color("disabled"),
        )
    meta_y = int(body_y + len(body_lines) * line_h + int(round(10 * scale)))
    if len(model.metadata) >= 2:
        draw_action_metadata(font, rect, model, meta_y, scale=scale)
    else:
        meta_style = ui_text_style("body_sm", "muted", scale=scale, minimum_size=9)
        for line in model.metadata:
            draw_text(font, line, int(rect.x + 14 * scale), meta_y, meta_style.size, meta_style.color)
            meta_y += int(round(20 * scale))
    if model.clock_ids:
        draw_action_corner_clocks(rect, model.clock_ids, state, align="left", scale=scale)
        draw_clock_badges(font, rect, model.clock_ids, state, outside=True, scale=scale)
    if model.labels:
        draw_corner_labels(font, rect, model.labels, "right", scale=scale)
    return clicked


def draw_action_metadata(font: Font | None, rect: Rectangle, model: TableCardModel, meta_y: int, scale: float = 1.0) -> None:
    suit_label, risk_label, *modifier_labels = model.metadata
    label_style = ui_text_style("body_sm", scale=scale, minimum_size=10)
    label_size = label_style.size
    padding_x = 12.0 * scale
    padding_y = 5.0 * scale
    suit_width = max(56.0 * scale, measure_text_width(font, suit_label, label_size) + padding_x * 2)
    suit_rect = Rectangle(rect.x + 14.0 * scale, meta_y, suit_width, 22.0 * scale)
    draw_frame(suit_rect, Color(18, 20, 26, 255), Color(168, 168, 168, 220))
    draw_text(font, suit_label, int(suit_rect.x + padding_x), int(suit_rect.y + padding_y - 1), label_size, ui_text_color("default"))

    risk_color = _risk_text_color(risk_label)
    risk_width = measure_text_width(font, risk_label, label_size)
    risk_x = rect.x + rect.width - 14.0 * scale - risk_width
    draw_text(font, risk_label, int(risk_x), meta_y, label_size, risk_color)
    if not modifier_labels:
        return
    x = rect.x + 14.0 * scale
    y = meta_y + 28.0 * scale
    max_x = rect.x + rect.width - 14.0 * scale
    for label in modifier_labels:
        chip_width = measure_text_width(font, label, label_size) + padding_x * 2
        if x + chip_width > max_x and x > rect.x + 14.0 * scale:
            x = rect.x + 14.0 * scale
            y += 20.0 * scale
        chip_rect = Rectangle(x, y, chip_width, 18.0 * scale)
        border = Color(120, 132, 150, 190)
        if " -" in label:
            border = Color(176, 92, 92, 210)
        elif " +" in label:
            border = Color(96, 154, 112, 210)
        draw_frame(chip_rect, Color(18, 20, 26, 245), border)
        draw_text(font, label, int(chip_rect.x + padding_x), int(chip_rect.y + 3.0 * scale), max(9, label_size - 1), ui_text_color("muted"))
        x += chip_width + 6.0 * scale


def _risk_text_color(label: str) -> Color:
    if label == "中风险":
        return ui_text_color("warning")
    if label == "高风险":
        return ui_text_color("danger")
    return ui_text_color("default")
