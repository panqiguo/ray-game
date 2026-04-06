from __future__ import annotations

from raygame.model.enums import ScreenName
from raygame.model.state import GameState

from .city_screen import draw_city_screen
from .ending_screen import draw_ending_screen
from .mission_screen import draw_mission_screen


def draw_current_screen(font, state: GameState, rng) -> None:
    if state.screen == ScreenName.CITY:
        draw_city_screen(font, state, rng)
    elif state.screen == ScreenName.MISSION:
        draw_mission_screen(font, state, rng)
    else:
        draw_ending_screen(font, state)

