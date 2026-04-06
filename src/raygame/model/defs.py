from __future__ import annotations

from dataclasses import dataclass, field

from .enums import AreaName, ResultType, Risk, ScreenName, Suit


@dataclass(frozen=True)
class Condition:
    kind: str
    value: str | int | bool | None = None


@dataclass(frozen=True)
class Effect:
    kind: str
    value: str | int | bool | None = None


@dataclass(frozen=True)
class ActionCostDef:
    kind: str
    key: str
    amount: int = 1
    label: str = ""


@dataclass(frozen=True)
class CardDef:
    id: str
    title: str
    suit: Suit
    points: int
    description: str
    is_negative: bool = False
    negative_family: str | None = None


@dataclass(frozen=True)
class OutcomeDef:
    text: str
    effects: tuple[Effect, ...] = ()
    completes: bool = True
    available_text: str | None = None


@dataclass(frozen=True)
class ActionMethodDef:
    id: str
    title: str
    suits: tuple[Suit, ...]
    difficulty: int
    risk: Risk
    success: OutcomeDef
    cost: OutcomeDef
    fail: OutcomeDef
    description: str = ""
    conditions: tuple[Condition, ...] = ()
    bonus: int = 0


@dataclass(frozen=True)
class ActionPointDef:
    id: str
    title: str
    description: str
    screen: ScreenName
    methods: tuple[ActionMethodDef, ...] = ()
    costs: tuple[ActionCostDef, ...] = ()
    free_effects: tuple[Effect, ...] = ()
    free_text: str = ""
    free_completes: bool = True
    conditions: tuple[Condition, ...] = ()
    area: AreaName | None = None
    special: str = ""


@dataclass(frozen=True)
class LocationDef:
    id: str
    title: str
    description: str
    action_ids: tuple[str, ...]


@dataclass(frozen=True)
class GrowthDef:
    id: str
    title: str
    description: str
    effects: tuple[Effect, ...]


@dataclass(frozen=True)
class EndingDef:
    id: str
    title: str
    body: str
    priority: int
    conditions: tuple[Condition, ...] = field(default_factory=tuple)
