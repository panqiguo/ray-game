from __future__ import annotations

from dataclasses import dataclass, field

from .enums import Risk, ScreenName, Suit


@dataclass(frozen=True)
class Condition:
    kind: str
    value: str | int | bool | tuple[str, ...] | None = None


@dataclass(frozen=True)
class Effect:
    kind: str
    value: str | int | bool | tuple[str, ...] | None = None


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


@dataclass(frozen=True)
class CheckDef:
    suits: tuple[Suit, ...]
    risk: Risk
    success: OutcomeDef
    cost: OutcomeDef
    fail: OutcomeDef


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


@dataclass(frozen=True)
class LocationNode:
    id: str
    title: str
    description: str
    position: tuple[int, int] | None = None
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


@dataclass(frozen=True)
class EndingDef:
    id: str
    title: str
    body: str
    priority: int
    conditions: tuple[Condition, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScenarioDef:
    id: str
    title: str
    screen: ScreenName
    world_root: LocationNode
    clocks: tuple[ProgressClockSpec, ...]
    initial_visible_locations: tuple[str, ...]
    initial_visible_clocks: tuple[str, ...]
    initial_health: int
    initial_stress: int
    initial_money: int
    initial_cigarettes: int
    initial_inventory: dict[str, int] = field(default_factory=dict)
    initial_growth_choices: tuple[str, ...] = ()


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
    action_clock_ids: dict[str, tuple[str, ...]]
    initial_visible_locations: tuple[str, ...]
    initial_visible_clocks: tuple[str, ...]
    initial_health: int
    initial_stress: int
    initial_money: int
    initial_cigarettes: int
    initial_inventory: dict[str, int]
    initial_growth_choices: tuple[str, ...]
