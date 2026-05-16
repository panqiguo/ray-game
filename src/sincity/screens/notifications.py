from __future__ import annotations

from pyray import *

from sincity.model.state import GameState
from sincity.rendering import draw_text

from .ui_core import draw_frame, measure_text_width, wrap_text_lines_any
from .ui_text import ui_text_size, ui_text_style

FADE_IN = 0.3
FADE_OUT = 0.5
TOAST_WIDTH = 320.0
TOAST_PADDING_X = 16.0
TOAST_PADDING_Y = 10.0
LINE_HEIGHT = 16.0
MAX_VISIBLE = 4
BODY_SIZE = ui_text_size("body_sm")

_FILL = Color(18, 20, 26, 245)
_BORDER = Color(78, 84, 96, 210)

_NOTIFICATION_TONES = {
    "success": "accent",
    "info":    "accent",
    "warning": "warning",
    "danger":  "danger",
}


def draw_notifications(font: Font | None, state: GameState) -> None:
    items = state.notifications[-MAX_VISIBLE:]
    if not items:
        return

    w = get_screen_width()
    base_x = w - TOAST_WIDTH - 16.0
    base_y = 40.0

    for item in items:
        alpha = _toast_alpha(item.age, item.duration)
        if alpha <= 0.0:
            continue

        body_lines = wrap_text_lines_any(font, item.body, TOAST_WIDTH - TOAST_PADDING_X * 2, BODY_SIZE) if item.body else ()
        toast_h = _toast_height(body_lines)
        rect = Rectangle(base_x, base_y, TOAST_WIDTH, toast_h)

        offset_y = -16.0 * min(1.0, item.age / FADE_IN)
        draw_rect = Rectangle(rect.x, rect.y + offset_y, rect.width, rect.height)

        fill = Color(_FILL.r, _FILL.g, _FILL.b, int(_FILL.a * alpha))
        border = Color(_BORDER.r, _BORDER.g, _BORDER.b, int(_BORDER.a * alpha))
        draw_frame(draw_rect, fill, border)

        title_style = ui_text_style("body", _NOTIFICATION_TONES[item.kind])
        title_color = Color(title_style.color.r, title_style.color.g, title_style.color.b, int(255 * alpha))
        draw_text(font, item.title, int(draw_rect.x + TOAST_PADDING_X), int(draw_rect.y + TOAST_PADDING_Y), title_style.size, title_color)

        if body_lines:
            body_style = ui_text_style("body_sm", "muted")
            body_color = Color(body_style.color.r, body_style.color.g, body_style.color.b, int(255 * alpha))
            body_y = draw_rect.y + TOAST_PADDING_Y + title_style.line_height
            for line in body_lines:
                draw_text(font, line, int(draw_rect.x + TOAST_PADDING_X), int(body_y), body_style.size, body_color)
                body_y += body_style.line_height - 2

        base_y += toast_h + 8.0


def _toast_alpha(age: float, duration: float) -> float:
    if age < FADE_IN:
        return age / FADE_IN
    remaining = duration - age
    if remaining <= FADE_OUT:
        return max(0.0, remaining / FADE_OUT)
    return 1.0


def _toast_height(body_lines: tuple[str, ...]) -> float:
    if not body_lines:
        return 44.0
    return 48.0 + len(body_lines) * LINE_HEIGHT
