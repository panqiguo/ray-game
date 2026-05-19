from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

from sincity.model.defs import ActionDef, CheckDef, Effect, InputRequirement, LocationNode, OutcomeDef, ProgressClockSpec


@dataclass(frozen=True)
class StringAtom:
    value: str


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
    initial: int | bool | str
    title: str = ""
    maximum: int | None = None
    persist: str = "encounter"


@dataclass(frozen=True)
class ReactRule:
    condition: Any
    effects: tuple[Effect, ...]
    source: str


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
    cycle_effects: tuple[Effect, ...] = ()
    reaction_die_expr: Any | None = None


@dataclass(frozen=True)
class ActionHandle:
    action_id: str
    scene_path: tuple[str, ...]
    slot_index: int
    action_key: str


@dataclass(frozen=True)
class RenderedAction:
    handle: ActionHandle
    action: ActionDef


@dataclass(frozen=True)
class RenderedScene:
    scene_id: str
    root: LocationNode
    shown_clock_ids: tuple[str, ...]
    actions: tuple[RenderedAction, ...]
    children: tuple["RenderedScene", ...]


@dataclass(frozen=True)
class RenderedEncounter:
    title: str
    description: str
    root: RenderedScene
    locations_by_id: dict[str, LocationNode]
    parent_by_id: dict[str, str | None]
    actions_by_id: dict[str, ActionDef]
    actions_by_location: dict[str, tuple[str, ...]]
    action_handles_by_id: dict[str, ActionHandle]
    shown_clock_ids_by_scene: dict[str, tuple[str, ...]]

    @property
    def root_location_id(self) -> str:
        return self.root.root.id

    @property
    def root_location(self) -> LocationNode:
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
    suits: tuple[str, ...]
    risk: str
    success: OutcomeTemplate
    cost: OutcomeTemplate
    fail: OutcomeTemplate


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


@dataclass(frozen=True)
class SceneTemplate:
    title: str
    description: str
    position: tuple[int, int] | None = None
    shown_clock_ids: tuple[str, ...] = ()
    conditions: tuple[Any, ...] = ()
    actions: tuple[ActionTemplate, ...] = ()
    children: tuple["SceneTemplate", ...] = ()


@dataclass(frozen=True)
class ReactTemplate:
    condition: Any
    effects: tuple[Effect, ...]


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
    cycle_effects: tuple[Effect, ...] = ()
    root_expr: Any | None = None
