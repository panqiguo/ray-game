from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

from raygame.model.defs import ActionDef, CheckDef, Effect, InputRequirement, LocationNode, OutcomeDef, ProgressClockSpec


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
    condition_expr: Any
    effects: tuple[Effect, ...]
    source: str


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


@dataclass(frozen=True)
class ClockTemplate:
    title: str
    initial: int
    maximum: int
    persist: str = "encounter"


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
    key: str | None
    title: str
    description: str
    inputs: tuple[InputRequirement, ...] = ()
    before: tuple[Effect, ...] = ()
    effects: tuple[Effect, ...] = ()
    check: CheckTemplate | None = None


@dataclass(frozen=True)
class SceneTemplate:
    key: str | None
    title: str
    description: str
    shown_clock_ids: tuple[str, ...] = ()
    actions: tuple[ActionTemplate, ...] = ()
    children: tuple["SceneTemplate", ...] = ()


@dataclass(frozen=True)
class ReactTemplate:
    condition_expr: Any
    effects: tuple[Effect, ...]
    key: str | None = None


@dataclass(frozen=True)
class ModuleDeclaration:
    kind: str
    value: Any


@dataclass
class ModuleState:
    metadata: EncounterMeta | None = None
    store_specs: dict[str, StoreFieldSpec] = field(default_factory=dict)
    clocks_by_id: dict[str, ProgressClockSpec] = field(default_factory=dict)
    react_rules: list[ReactRule] = field(default_factory=list)
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()
    root_expr: Any | None = None
