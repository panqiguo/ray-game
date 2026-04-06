from __future__ import annotations

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.screens.widgets import draw_frame


def draw_ending_screen(font: Font | None, state: GameState) -> None:
    rect = Rectangle(120, 120, 1200, 580)
    draw_frame(rect, Color(18, 20, 25, 248))
    draw_text(font, state.ending_title or "结局", 160, 170, 40, RAYWHITE)
    draw_text(font, state.ending_body, 160, 250, 24, LIGHTGRAY)
    draw_text(font, "F5 可重新开局", 160, 620, 20, Color(200, 180, 120, 255))
