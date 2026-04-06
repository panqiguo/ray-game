from __future__ import annotations

from raygame.content.endings import ENDING_DEFS
from raygame.model.state import GameState
from raygame.rules.conditions import all_met


def determine_ending(state: GameState) -> tuple[str, str, str]:
    if state.clocks.crow_time <= 0:
        state.flags.add("crow_dead")
    for ending in sorted(ENDING_DEFS.values(), key=lambda item: item.priority, reverse=True):
        if all_met(ending.conditions, state):
            return ending.id, ending.title, ending.body
    fallback = ENDING_DEFS["silent_justice"]
    return fallback.id, fallback.title, fallback.body

