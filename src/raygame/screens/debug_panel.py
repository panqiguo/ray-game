from __future__ import annotations

from pyray import *  # type: ignore

from raygame.model.state import GameState
from raygame.rendering import draw_text
from raygame.screens.widgets import text_button


def draw_debug_panel(font: Font | None, state: GameState) -> None:
    if not state.debug_open:
        return
    rect = Rectangle(1080, 92, 330, 300)
    draw_rectangle_rounded(rect, 0.08, 8, Color(16, 17, 22, 245))
    draw_text(font, "调试", 1096, 104, 24, RAYWHITE)
    y = 142
    if text_button(font, Rectangle(1096, y, 140, 30), "加钱 +20", 18):
        state.resources.money += 20
    if text_button(font, Rectangle(1248, y, 140, 30), "Stress +2", 18):
        state.resources.stress = min(state.resources.max_stress, state.resources.stress + 2)
    y += 40
    if text_button(font, Rectangle(1096, y, 140, 30), "Health -1", 18):
        state.resources.health -= 1
    if text_button(font, Rectangle(1248, y, 140, 30), "塞入惊悸", 18):
        state.deck.discard_pile.append("panic")
    y += 40
    if text_button(font, Rectangle(1096, y, 140, 30), "解锁线索A", 18):
        state.clues.add("clue_a")
        state.flags.add("clue_a")
    if text_button(font, Rectangle(1248, y, 140, 30), "解锁线索B", 18):
        state.clues.add("clue_b")
        state.flags.add("clue_b")
    y += 40
    if text_button(font, Rectangle(1096, y, 140, 30), "乌鸦时间-1", 18):
        state.clocks.crow_time = max(0, state.clocks.crow_time - 1)
    if text_button(font, Rectangle(1248, y, 140, 30), "Heat +1", 18):
        state.clocks.heat = min(state.clocks.heat_max, state.clocks.heat + 1)
