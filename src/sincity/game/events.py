from __future__ import annotations

from dataclasses import dataclass

from sincity.model.enums import ResultType
from sincity.model.state import GameState


@dataclass(frozen=True)
class ActionStarted:
    action_id: str
    result: ResultType | None


@dataclass(frozen=True)
class ResolutionSettled:
    action_id: str


@dataclass(frozen=True)
class EncounterStarted:
    encounter_id: str


@dataclass(frozen=True)
class DialogueStarted:
    dialogue_id: str


@dataclass(frozen=True)
class GameEnded:
    ending_id: str | None


@dataclass(frozen=True)
class DialogueFastForwarded:
    pass


GameEvent = ActionStarted | ResolutionSettled | EncounterStarted | DialogueStarted | DialogueFastForwarded | GameEnded


def drain_pending_events(state: GameState) -> list[GameEvent]:
    events = state.pending_events
    state.pending_events = []
    return events


def has_event(state: GameState, event_type: type) -> bool:
    return any(isinstance(e, event_type) for e in state.pending_events)


def consume_event(state: GameState, event_type: type) -> bool:
    for i, e in enumerate(state.pending_events):
        if isinstance(e, event_type):
            state.pending_events.pop(i)
            return True
    return False
