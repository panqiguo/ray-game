from __future__ import annotations

from dataclasses import dataclass

from raygame.model.defs import ActionDef, Effect, LocationNode, ProgressClockSpec


@dataclass(frozen=True)
class EncounterTransitionDef:
    kind: str
    source: str
    effects: tuple[Effect, ...]


@dataclass(frozen=True)
class EncounterStateDef:
    id: str
    title: str
    description: str
    root: LocationNode


@dataclass(frozen=True)
class EncounterActDef:
    id: str
    title: str
    description: str
    objective_clock: ProgressClockSpec
    initial_state_id: str
    states: tuple[EncounterStateDef, ...]
    transitions: tuple[EncounterTransitionDef, ...] = ()


@dataclass(frozen=True)
class EncounterDef:
    id: str
    title: str
    description: str
    initial_act_id: str
    acts: tuple[EncounterActDef, ...]
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()


@dataclass(frozen=True)
class CompiledEncounter:
    id: str
    title: str
    description: str
    initial_act_id: str
    acts_by_id: dict[str, EncounterActDef]
    root_by_state: dict[tuple[str, str], str]
    states_by_key: dict[tuple[str, str], EncounterStateDef]
    locations_by_id: dict[str, LocationNode]
    parent_by_id: dict[str, str | None]
    actions_by_id: dict[str, ActionDef]
    actions_by_location: dict[str, tuple[str, ...]]
    clocks_by_id: dict[str, ProgressClockSpec]
    transitions_by_act: dict[str, tuple[EncounterTransitionDef, ...]]
    rewards: tuple[Effect, ...]
    fail_effects: tuple[Effect, ...]
