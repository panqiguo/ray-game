from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from raygame.model.defs import ActionDef, Effect, LocationNode, ProgressClockSpec


@dataclass(frozen=True)
class StringAtom:
    value: str


@dataclass(frozen=True)
class ClockRef:
    id: str


@dataclass(frozen=True)
class StoreSlotRef:
    id: str


SexpAtom: TypeAlias = str | int | bool | StringAtom
SexpNode: TypeAlias = SexpAtom | list["SexpNode"]


class EncounterCompileError(Exception):
    pass


@dataclass(frozen=True)
class StoreFieldSpec:
    id: str
    kind: str
    initial: int | bool | str
    title: str = ""
    maximum: int | None = None


@dataclass(frozen=True)
class ReactRule:
    condition: SexpNode
    effects: tuple[Effect, ...]
    source: str


@dataclass(frozen=True)
class MacroTemplate:
    name: str
    params: tuple[str, ...]
    body: SexpNode


@dataclass(frozen=True)
class CompiledEncounterProgram:
    id: str
    title: str
    description: str
    store_specs: dict[str, StoreFieldSpec]
    clocks_by_id: dict[str, ProgressClockSpec]
    bindings: dict[str, SexpNode]
    macros: dict[str, MacroTemplate]
    react_rules: tuple[ReactRule, ...]
    view_expr: SexpNode
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
