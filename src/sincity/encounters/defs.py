from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

from sincity.model.defs import ActionDef, CheckDef, CheckFactorDef, Effect, InputRequirement, LocationDef, OutcomeDef, ProgressClockSpec


@dataclass(frozen=True)
class StringAtom:
    value: str


@dataclass(frozen=True)
class SourceRef:
    source_path: Path | None
    line: int
    column: int


SexpAtom: TypeAlias = str | int | bool | StringAtom
SexpNode: TypeAlias = SexpAtom | list["SexpNode"]


class EncounterCompileError(Exception):
    pass


class EncounterReadError(EncounterCompileError):
    pass


class EncounterModuleError(EncounterCompileError):
    pass


class EncounterSchemeError(EncounterCompileError):
    pass


class EncounterSchemaError(EncounterCompileError):
    pass


@dataclass(frozen=True)
class StoreFieldSpec:
    id: str
    kind: str
    initial: Any
    title: str = ""
    maximum: int | None = None
    persist: str = "encounter"


@dataclass(frozen=True)
class ObjectValue:
    fields: dict[str, Any]


@dataclass(frozen=True)
class RuntimeClockValue:
    title: str
    description: str
    value: int
    maximum: int


@dataclass(frozen=True)
class ReactRule:
    condition: Any
    effects: tuple[Effect, ...]
    source: str
    effects_expr: Any | None = None


@dataclass(frozen=True)
class ReactionFace:
    value: int
    title: str
    description: str
    effects: tuple[Effect, ...] = ()


@dataclass(frozen=True)
class ReactionTable:
    faces: tuple[ReactionFace, ...]


@dataclass(frozen=True)
class EncounterMeta:
    key: str
    title: str
    description: str


@dataclass(frozen=True)
class CompiledEncounterProgram:
    id: str
    title: str
    description: str
    source_path: Path | None
    store_specs: dict[str, StoreFieldSpec]
    clocks_by_id: dict[str, ProgressClockSpec]
    definitions: dict[str, Any]
    react_rules: tuple[ReactRule, ...]
    view_expr: Any
    rewards: tuple[Effect, ...]
    fail_effects: tuple[Effect, ...]
    cycle_start_effects: tuple[Effect, ...] = ()
    reacts_expr: Any | None = None
    rewards_expr: Any | None = None
    fail_effects_expr: Any | None = None
    cycle_start_effects_expr: Any | None = None
    reaction_die_expr: Any | None = None


@dataclass(frozen=True)
class ActionHandle:
    action_id: str
    location_path: tuple[str, ...]
    slot_index: int
    action_key: str


@dataclass(frozen=True)
class RenderedAction:
    handle: ActionHandle
    action: ActionDef


@dataclass(frozen=True)
class RenderedClock:
    id: str
    title: str
    description: str
    value: int
    maximum: int


@dataclass(frozen=True)
class RenderedLocation:
    location_id: str
    root: LocationDef
    shown_clock_ids: tuple[str, ...]
    shown_clocks: tuple[RenderedClock, ...]
    nested_clocks: dict[str, RuntimeClockValue]
    actions: tuple[RenderedAction, ...]
    children: tuple["RenderedLocation", ...]


@dataclass(frozen=True)
class RenderedEncounter:
    title: str
    description: str
    root: RenderedLocation
    locations_by_id: dict[str, LocationDef]
    parent_by_id: dict[str, str | None]
    actions_by_id: dict[str, ActionDef]
    actions_by_location: dict[str, tuple[str, ...]]
    action_handles_by_id: dict[str, ActionHandle]
    shown_clock_ids_by_location: dict[str, tuple[str, ...]]
    shown_clocks_by_location: dict[str, tuple[RenderedClock, ...]]
    nested_clocks_by_id: dict[str, RuntimeClockValue]

    @property
    def root_location_id(self) -> str:
        return self.root.location_id

    @property
    def root_location(self) -> LocationDef:
        return self.root.root

    @property
    def root_child_location_ids(self) -> tuple[str, ...]:
        return tuple(child.root.id for child in self.root.children)


@dataclass(frozen=True)
class ClockTemplate:
    title: str
    description: str
    initial: int
    maximum: int


@dataclass(frozen=True)
class StateBindingValue:
    name: str
    spec: StoreFieldSpec
    value: int | bool | str


@dataclass(frozen=True)
class OutcomeTemplate:
    text: str
    effects: tuple[Effect, ...]


@dataclass(frozen=True)
class CheckTemplate:
    suit: str
    risk: str
    success: OutcomeTemplate
    cost: OutcomeTemplate
    fail: OutcomeTemplate
    factors: tuple[CheckFactorDef, ...] = ()


@dataclass(frozen=True)
class ActionTemplate:
    title: str
    description: str
    position: tuple[int, int] | None = None
    inputs: tuple[InputRequirement, ...] = ()
    before: tuple[Effect, ...] = ()
    effects: tuple[Effect, ...] = ()
    conditions: tuple[Any, ...] = ()
    check: CheckTemplate | None = None
    reveal: Any = None
    button_label: str = ""


@dataclass(frozen=True)
class LocationTemplate:
    title: str
    description: str
    position: tuple[int, int] | None = None
    shown_clock_ids: tuple[Any, ...] = ()
    conditions: tuple[Any, ...] = ()
    actions: tuple[ActionTemplate, ...] = ()
    children: tuple["LocationTemplate", ...] = ()


@dataclass(frozen=True)
class ReactTemplate:
    condition: Any
    effects: tuple[Effect, ...]
    effects_expr: Any | None = None
    source: str = ""


@dataclass(frozen=True)
class TaskStepTemplate:
    title: Any
    completed: Any


@dataclass(frozen=True)
class TaskTemplate:
    kind: str
    title: Any
    description: Any
    active: Any
    completed: Any
    failed: Any
    steps: tuple[TaskStepTemplate, ...] = ()


@dataclass
class ModuleState:
    metadata: EncounterMeta | None = None
    store_specs: dict[str, StoreFieldSpec] = field(default_factory=dict)
    clocks_by_id: dict[str, ProgressClockSpec] = field(default_factory=dict)
    react_rules: list[ReactRule] = field(default_factory=list)
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()
    cycle_start_effects: tuple[Effect, ...] = ()
    root_expr: Any | None = None
