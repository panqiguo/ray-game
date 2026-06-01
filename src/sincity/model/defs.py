from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import Risk, ScreenName, Suit


@dataclass(frozen=True)
class Condition:
    kind: str
    value: str | int | bool | tuple[str, ...] | None = None
    label: str = ""


@dataclass(frozen=True)
class FieldRef:
    name: str


@dataclass(frozen=True)
class DynamicValue:
    body: Any


EffectScalar = str | int | bool | None


@dataclass(frozen=True)
class SetFieldPayload:
    target: str
    value: EffectScalar | FieldRef | DynamicValue


@dataclass(frozen=True)
class AddFieldPayload:
    target: str
    amount: int


@dataclass(frozen=True)
class ShiftClockPayload:
    target: str
    amount: int


@dataclass(frozen=True)
class Effect:
    kind: str
    value: str | int | bool | tuple[str, ...] | FieldRef | DynamicValue | SetFieldPayload | AddFieldPayload | ShiftClockPayload | None = None


@dataclass(frozen=True)
class InputRequirement:
    kind: str
    key: str
    amount: int = 1
    label: str = ""
    consume: bool = True


@dataclass(frozen=True)
class CardDef:
    id: str
    title: str
    suit: Suit | None
    points: int
    description: str
    is_negative: bool = False
    negative_family: str | None = None


@dataclass(frozen=True)
class OutcomeDef:
    text: str
    effects: tuple[Effect, ...] = ()
    completes: bool = True


@dataclass(frozen=True)
class CheckFactorDef:
    value: int
    label: str
    active: bool = True
    source: Any | None = None


@dataclass(frozen=True)
class CheckDef:
    suits: tuple[Suit, ...]
    risk: Risk
    success: OutcomeDef
    cost: OutcomeDef
    fail: OutcomeDef
    factors: tuple[CheckFactorDef, ...] = ()


@dataclass(frozen=True)
class ActionRevealDef:
    text: str
    duration: float = 4.0
    title: str = ""


@dataclass(frozen=True)
class ActionDef:
    id: str
    title: str
    description: str
    screen: ScreenName
    position: tuple[int, int] | None = None
    check: CheckDef | None = None
    inputs: tuple[InputRequirement, ...] = ()
    effects: tuple[Effect, ...] = ()
    conditions: tuple[Condition, ...] = ()
    linked_clock_ids: tuple[str, ...] = ()
    reveal: ActionRevealDef | None = None
    button_label: str = ""


@dataclass(frozen=True)
class LocationNode:
    id: str
    title: str
    description: str
    position: tuple[int, int] | None = None
    show_clock_ids: tuple[str, ...] = ()
    actions: tuple[ActionDef, ...] = ()
    children: tuple["LocationNode", ...] = ()
    conditions: tuple[Condition, ...] = ()


@dataclass(frozen=True)
class ClockThreshold:
    at: int
    effects: tuple[Effect, ...]


@dataclass(frozen=True)
class ProgressClockDisplay:
    scope: str = "auto"
    anchor_id: str | None = None


@dataclass(frozen=True)
class ProgressClockSpec:
    id: str
    title: str
    segments: int
    description: str = ""
    initial: int = 0
    thresholds: tuple[ClockThreshold, ...] = ()
    tags: tuple[str, ...] = ()
    hidden: bool = False
    display: ProgressClockDisplay = field(default_factory=ProgressClockDisplay)


@dataclass(frozen=True)
class GrowthDef:
    id: str
    title: str
    description: str
    effects: tuple[Effect, ...]
    conditions: tuple[Condition, ...] = ()


@dataclass(frozen=True)
class EndingDef:
    id: str
    title: str
    body: str
    priority: int
    conditions: tuple[Condition, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CompiledScenario:
    id: str
    title: str
    screen: ScreenName
    world_root_id: str
    root_location_ids: tuple[str, ...]
    locations_by_id: dict[str, LocationNode]
    parent_by_id: dict[str, str | None]
    actions_by_id: dict[str, ActionDef]
    actions_by_location: dict[str, tuple[str, ...]]
    clocks_by_id: dict[str, ProgressClockSpec]
    global_clock_ids: tuple[str, ...]
    location_clock_ids: dict[str, tuple[str, ...]]
    initial_health: int
    initial_energy: int
    initial_money: int
    initial_cigarettes: int
    initial_inventory: dict[str, int]
    initial_growth_choices: tuple[str, ...]

    @property
    def root_location_id(self) -> str:
        return self.world_root_id

    @property
    def root_location(self) -> LocationNode:
        return self.locations_by_id[self.world_root_id]

    @property
    def root_child_location_ids(self) -> tuple[str, ...]:
        return self.root_location_ids
