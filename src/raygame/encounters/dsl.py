from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from raygame.content.builders import action, clock, location
from raygame.encounters.defs import EncounterActDef, EncounterDef, EncounterStateDef, EncounterTransitionDef
from raygame.model.defs import ActionDef, Effect, LocationNode, ProgressClockSpec
from raygame.model.enums import ScreenName


@dataclass(frozen=True)
class EncounterStateScript:
    id: str
    title: str
    description: str
    root_id: str
    actions: tuple[str, ...]
    children: tuple[LocationNode, ...] = ()


@dataclass(frozen=True)
class EncounterActScript:
    id: str
    title: str
    description: str
    objective_clock: ProgressClockSpec
    initial_state_id: str
    action_defs: Mapping[str, ActionDef]
    states: tuple[EncounterStateScript, ...]
    clocks: tuple[ProgressClockSpec, ...] = ()
    transitions: tuple[EncounterTransitionDef, ...] = ()


@dataclass(frozen=True)
class EncounterScript:
    id: str
    title: str
    description: str
    initial_act_id: str
    acts: tuple[EncounterActScript, ...]
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()


def encounter_action(**kwargs) -> ActionDef:
    return action(screen=ScreenName.ENCOUNTER, **kwargs)


def objective_clock(id: str, title: str, segments: int) -> ProgressClockSpec:
    return clock(id=id, title=title, segments=segments)


def local_clock(id: str, title: str, segments: int) -> ProgressClockSpec:
    return clock(id=id, title=title, segments=segments)


def state(
    id: str,
    title: str,
    description: str,
    *,
    root_id: str | None = None,
    actions: tuple[str, ...],
    children: tuple[LocationNode, ...] = (),
) -> EncounterStateScript:
    return EncounterStateScript(
        id=id,
        title=title,
        description=description,
        root_id=root_id or f"{id}_root",
        actions=actions,
        children=children,
    )


def act(
    *,
    id: str,
    title: str,
    description: str,
    objective_clock: ProgressClockSpec,
    initial_state_id: str,
    action_defs: Mapping[str, ActionDef],
    states: tuple[EncounterStateScript, ...],
    clocks: tuple[ProgressClockSpec, ...] = (),
    transitions: tuple[EncounterTransitionDef, ...] = (),
) -> EncounterActScript:
    return EncounterActScript(
        id=id,
        title=title,
        description=description,
        objective_clock=objective_clock,
        initial_state_id=initial_state_id,
        action_defs=action_defs,
        states=states,
        clocks=clocks,
        transitions=transitions,
    )


def encounter(
    *,
    id: str,
    title: str,
    description: str,
    initial_act_id: str,
    acts: tuple[EncounterActScript, ...],
    rewards: tuple[Effect, ...] = (),
    fail_effects: tuple[Effect, ...] = (),
) -> EncounterScript:
    return EncounterScript(
        id=id,
        title=title,
        description=description,
        initial_act_id=initial_act_id,
        acts=acts,
        rewards=rewards,
        fail_effects=fail_effects,
    )


def on_clock_full(source: str, *effects: Effect) -> EncounterTransitionDef:
    return EncounterTransitionDef(kind="clock_full", source=source, effects=effects)


def on_clock_empty(source: str, *effects: Effect) -> EncounterTransitionDef:
    return EncounterTransitionDef(kind="clock_empty", source=source, effects=effects)


def _state_scoped_action(action_def: ActionDef, state_id: str) -> ActionDef:
    return replace(
        action_def,
        id=f"{action_def.id}_{state_id}",
    )


def compile_state_script(
    script: EncounterStateScript,
    *,
    action_defs: Mapping[str, ActionDef],
) -> EncounterStateDef:
    seen_keys: set[str] = set()
    built_actions: list[ActionDef] = []
    for item in script.actions:
        assert item not in seen_keys, f"Duplicate action key in state {script.id}: {item}"
        seen_keys.add(item)
        assert item in action_defs, f"Unknown action key in state {script.id}: {item}"
        built_actions.append(_state_scoped_action(action_defs[item], script.id))
    root, _ = location(
        id=script.root_id,
        title="",
        description="",
        actions=tuple(built_actions),
        children=script.children,
    )
    return EncounterStateDef(
        id=script.id,
        title=script.title,
        description=script.description,
        root=root,
    )


def compile_encounter_script(script: EncounterScript) -> EncounterDef:
    compiled_acts: list[EncounterActDef] = []
    for act_script in script.acts:
        compiled_states = tuple(
            compile_state_script(
                state_script,
                action_defs=act_script.action_defs,
            )
            for state_script in act_script.states
        )
        compiled_acts.append(
            EncounterActDef(
                id=act_script.id,
                title=act_script.title,
                description=act_script.description,
                objective_clock=act_script.objective_clock,
                initial_state_id=act_script.initial_state_id,
                states=compiled_states,
                clocks=act_script.clocks,
                transitions=act_script.transitions,
            )
        )
    return EncounterDef(
        id=script.id,
        title=script.title,
        description=script.description,
        initial_act_id=script.initial_act_id,
        acts=tuple(compiled_acts),
        rewards=script.rewards,
        fail_effects=script.fail_effects,
    )
