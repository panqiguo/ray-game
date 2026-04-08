from __future__ import annotations

from raygame.model.enums import ScreenName
from raygame.model.state import GameState

from .city_screen import draw_city_screen
from .ending_screen import draw_ending_screen


def draw_current_screen(font, state: GameState, rng) -> None:
    if state.screen == ScreenName.ENDING:
        draw_ending_screen(font, state)
    else:
        draw_city_screen(font, state, rng)
