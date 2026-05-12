from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayActionCommand:
    action_id: str
    method_id: str | None
    card_id: str | None


@dataclass(frozen=True)
class EndDayCommand:
    pass


@dataclass(frozen=True)
class EnterMissionCommand:
    pass


@dataclass(frozen=True)
class PushThroughCommand:
    pass


@dataclass(frozen=True)
class UseCigaretteCommand:
    hand_card_id: str | None = None

