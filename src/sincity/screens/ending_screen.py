from __future__ import annotations

from pyray import *  # type: ignore

from sincity.model.state import GameState
from sincity.rendering import draw_text
from sincity.screens.widgets import draw_frame
from .ui_text import ui_text_style


def draw_ending_screen(font: Font | None, state: GameState) -> None:
    rect = Rectangle(120, 120, 1200, 580)
    draw_frame(rect, Color(18, 20, 25, 248))
    title_style = ui_text_style("title", scale=(40 / 30))
    body_style = ui_text_style("subtitle", "muted")
    hint_style = ui_text_style("subtitle", "accent", scale=(20 / 24))
    draw_text(font, state.ending_title or "结局", 160, 170, title_style.size, title_style.color)
    draw_text(font, state.ending_body, 160, 250, body_style.size, body_style.color)
    draw_text(font, "R 可重新开局", 160, 620, hint_style.size, hint_style.color)
