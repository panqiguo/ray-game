from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from raygame.content_lang.runtime_core import (
    flatten_scene as _flatten_scene,
    host_values as _host_values,
    keyword_args as _keyword_args,
    render_scene as _render_scene,
    validate_action_template as _validate_action_template,
    validate_react_template as _validate_react_template,
    validate_schema_forms as _validate_schema_forms_generic,
    validate_scene_template as _validate_scene_template,
)
from raygame.encounters.defs import ActionTemplate, ClockTemplate, EncounterMeta, EncounterSchemaError, EncounterSchemeError, ReactRule, ReactTemplate, SceneTemplate, StateBindingValue, StoreFieldSpec
from raygame.encounters.lispy import Environment, _MISSING, base_environment, evaluate, expand_includes, truthy
from raygame.model.defs import CompiledScenario, Effect, LocationNode, ProgressClockSpec
from raygame.model.enums import ScreenName
from raygame.model.state import GameState, ProgressClockState


@dataclass(frozen=True)
class CompiledWorldProgram:
    id: str
    title: str
    description: str
    source_path: Path | None
    screen: ScreenName
    clocks_by_id: dict[str, ProgressClockSpec]
    definitions: dict[str, Any]
    react_rules: tuple[ReactRule, ...]
    view_expr: Any
    initial_health: int
    initial_stress: int
    initial_money: int
    initial_cigarettes: int
    initial_inventory: dict[str, int]
    initial_values: dict[str, int | bool | str]
    initial_growth_choices: tuple[str, ...] = ()


WORLD_EFFECTS = frozenset({
    "set_field",
    "add_field",
    "shift_clock",
    "reset_hand",
    "advance_day",
    "end_game",
    "start_encounter",
    "start_dialogue",
    "start_quick_dialogue",
})


def compile_world_program(
    source: str,
    *,
    source_path: str | Path | None = None,
    initial_health: int,
    initial_stress: int,
    initial_money: int,
    initial_cigarettes: int,
    initial_inventory: dict[str, int] | None = None,
    initial_values: dict[str, int | bool | str] | None = None,
) -> CompiledWorldProgram:
    path = Path(source_path) if source_path is not None else None
    forms = expand_includes(source, source_path=path, include_stack=(() if path is None else (path,)))
    definitions: dict[str, Any] = {}
    content_form: Any | None = None
    for form in forms:
        if isinstance(form, list) and form and form[0] == "define":
            assert len(form) == 3 and isinstance(form[1], str), "`define` expects name and expr."
            definitions[form[1]] = form[2]
            continue
        assert content_form is None, "World module can contain only one top-level `(content ...)` form."
        content_form = form
    assert isinstance(content_form, list) and content_form and content_form[0] == "content", "World module must end with a `(content ...)` form."
    kwargs = _keyword_args(content_form[1:], allowed={":meta", ":state", ":reacts", ":root"})
    clocks, state_values = _resolve_state_specs(kwargs.get(":state"), definitions)
    env = _world_schema_env(definitions=definitions, clocks_by_id=clocks, initial_values=state_values, initial_inventory=dict(initial_inventory or {}))
    metadata = _resolve_meta(kwargs.get(":meta"), env, definitions, path)
    react_rules = _resolve_reacts(kwargs.get(":reacts"), env, definitions)
    root_expr = _resolve_expr(kwargs.get(":root"), definitions)
    assert root_expr is not None, "Content is missing required field: :root"
    runtime_definitions = {
        name: expr
        for name, expr in definitions.items()
        if name not in clocks and not (isinstance(expr, list) and expr and expr[0] == "state")
    }
    program = CompiledWorldProgram(
        id=metadata.key,
        title=metadata.title,
        description=metadata.description,
        source_path=path,
        screen=ScreenName.CITY,
        clocks_by_id=clocks,
        definitions=runtime_definitions,
        react_rules=tuple(react_rules),
        view_expr=root_expr,
        initial_health=initial_health,
        initial_stress=initial_stress,
        initial_money=initial_money,
        initial_cigarettes=initial_cigarettes,
        initial_inventory=dict(initial_inventory or {}),
        initial_values={**state_values, **dict(initial_values or {})},
    )
    validate_world_program(program)
    return program


def render_world(program: CompiledWorldProgram, state: GameState) -> CompiledScenario:
    env = _world_env(program, state)
    scene = evaluate(program.view_expr, env)
    assert isinstance(scene, SceneTemplate), f"World root must resolve to a node: {program.id}"
    rendered = _render_scene(program, scene, scene_path=())
    locations_by_id: dict[str, LocationNode] = {}
    parent_by_id: dict[str, str | None] = {}
    actions_by_id = {}
    actions_by_location = {}
    action_handles_by_id = {}
    shown_clock_ids_by_scene: dict[str, tuple[str, ...]] = {}
    _flatten_scene(
        rendered,
        parent_id=None,
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        action_handles_by_id=action_handles_by_id,
        shown_clock_ids_by_scene=shown_clock_ids_by_scene,
    )
    return CompiledScenario(
        id=program.id,
        title=program.title,
        screen=ScreenName.CITY,
        world_root_id=rendered.root.id,
        root_location_ids=tuple(child.root.id for child in rendered.children),
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        clocks_by_id=dict(program.clocks_by_id),
        global_clock_ids=rendered.shown_clock_ids,
        location_clock_ids=dict(shown_clock_ids_by_scene),
        initial_health=program.initial_health,
        initial_stress=program.initial_stress,
        initial_money=program.initial_money,
        initial_cigarettes=program.initial_cigarettes,
        initial_inventory=dict(program.initial_inventory),
        initial_growth_choices=(),
    )


def validate_world_program(program: CompiledWorldProgram) -> None:
    dummy_state = _dummy_state(program)
    env = _world_env(program, dummy_state)
    for name, expr in program.definitions.items():
        _validate_world_schema_forms(expr, env, context=f"{program.id}: definition `{name}`")
        if isinstance(expr, list) and expr and expr[0] == "state":
            continue
        try:
            value = env.lookup(name)
            if isinstance(value, SceneTemplate):
                _validate_scene_template(value)
            elif isinstance(value, ActionTemplate):
                _validate_action_template(value)
            elif isinstance(value, ReactTemplate):
                _validate_react_template(value)
        except EncounterSchemeError as exc:
            raise EncounterSchemeError(f"{program.id}: definition `{name}` has Scheme error: {exc}") from exc
        except EncounterSchemaError as exc:
            raise EncounterSchemaError(f"{program.id}: definition `{name}` has schema error: {exc}") from exc
    _validate_world_schema_forms(program.view_expr, env, context=f"{program.id}: root node")
    for rule in program.react_rules:
        _validate_world_schema_forms(rule.condition_expr, env, context=f"{program.id}: react `{rule.source}` condition")
        for effect in rule.effects:
            assert isinstance(effect, Effect), f"{program.id}: react `{rule.source}` contains non-effect value: {effect!r}"
    snapshot = render_world(program, dummy_state)
    assert snapshot.root_location_ids, f"{program.id}: world root must expose at least one child node."
    for location in snapshot.locations_by_id.values():
        assert location.title, f"{program.id}: location missing title."
    for action in snapshot.actions_by_id.values():
        _assert_effects_allowed(action.effects, context=f"{program.id}: action `{action.title}`")
        if action.check is not None:
            for outcome_name, outcome in (("ok", action.check.success), ("partial", action.check.cost), ("fail", action.check.fail)):
                _assert_effects_allowed(outcome.effects, context=f"{program.id}: action `{action.title}` {outcome_name}")
        for condition in action.conditions:
            assert condition.kind, f"{program.id}: action contains malformed condition: {condition!r}"
    for rule in program.react_rules:
        _assert_effects_allowed(rule.effects, context=f"{program.id}: react `{rule.source}`")


def _validate_world_schema_forms(expr: Any, env: Environment, *, context: str) -> None:
    _validate_schema_forms_generic(expr, env, context=context, skip_heads=frozenset({"state"}), allow_nil_templates=True)


def react_rule_matches(program: CompiledWorldProgram, state: GameState, rule: ReactRule) -> bool:
    return truthy(evaluate(rule.condition_expr, _world_env(program, state)))


def next_react_rule(program: CompiledWorldProgram, state: GameState, blocked_sources: set[str]) -> ReactRule | None:
    for rule in program.react_rules:
        if rule.source in blocked_sources and react_rule_matches(program, state, rule):
            continue
        if react_rule_matches(program, state, rule):
            return rule
    return None


def _resolve_meta(expr: Any, env: Environment, definitions: dict[str, Any], path: Path | None) -> EncounterMeta:
    if expr is None:
        stem = path.stem if path is not None else "content"
        return EncounterMeta(key=stem, title=stem, description="")
    value = evaluate(_resolve_expr(expr, definitions), env)
    assert isinstance(value, EncounterMeta), f"meta form did not produce meta: {value!r}"
    return value


def _resolve_state_specs(expr: Any, definitions: dict[str, Any]) -> tuple[dict[str, ProgressClockSpec], dict[str, int | bool | str]]:
    if expr is None:
        return {}, {}
    expr = _resolve_expr(expr, definitions)
    assert isinstance(expr, list) and expr and expr[0] == "state", "World :state must be a `(state ...)` form."
    env = Environment(parent=base_environment(), values=_host_values(store_specs={}, store={}), lazy_values=definitions)
    clocks_by_id: dict[str, ProgressClockSpec] = {}
    initial_values: dict[str, int | bool | str] = {}
    for binding in expr[1:]:
        assert isinstance(binding, list) and len(binding) == 2 and isinstance(binding[0], str), "Each world state binding must be `(name value)`."
        name = binding[0]
        value = evaluate(binding[1], env)
        if isinstance(value, ClockTemplate):
            clocks_by_id[name] = ProgressClockSpec(id=name, title=value.title, description=value.description, segments=value.maximum)
        else:
            assert isinstance(value, (bool, int, str)), f"Unsupported world state value for {name}: {value!r}"
            initial_values[name] = value
    return clocks_by_id, initial_values


def _resolve_reacts(expr: Any, env: Environment, definitions: dict[str, Any]) -> list[ReactRule]:
    if expr is None:
        return []
    value = evaluate(_resolve_expr(expr, definitions), env)
    items = value if isinstance(value, list) else [value]
    rules: list[ReactRule] = []
    for index, item in enumerate(items):
        if item is None:
            continue
        _validate_react_template(item)
        rules.append(ReactRule(condition_expr=item.condition_expr, effects=item.effects, source=f"react[{index}]"))
    return rules


def _world_schema_env(
    *,
    definitions: dict[str, Any],
    clocks_by_id: dict[str, ProgressClockSpec],
    initial_values: dict[str, int | bool | str],
    initial_inventory: dict[str, int],
) -> Environment:
    return Environment(
        parent=base_environment(),
        values=_host_values(store_specs={}, store={}),
        lazy_values=definitions,
        resolver=lambda name: _world_schema_resolver(name, clocks_by_id=clocks_by_id, initial_values=initial_values, initial_inventory=initial_inventory),
    )


def _world_schema_resolver(
    name: str,
    *,
    clocks_by_id: dict[str, ProgressClockSpec],
    initial_values: dict[str, int | bool | str],
    initial_inventory: dict[str, int],
) -> Any:
    if name == "day":
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=1, persist="run"), value=1)
    if name in clocks_by_id:
        spec = clocks_by_id[name]
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="clock", initial=0, title=spec.title, maximum=spec.segments, persist="run"), value=0)
    if name in {"health", "stress", "money", "cigarettes"}:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="run"), value=0)
    if name in initial_values:
        initial = initial_values[name]
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=initial, persist="run"), value=initial)
    if name in initial_inventory:
        initial = initial_inventory[name]
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=initial, persist="run"), value=initial)
    return _MISSING


def _resolve_expr(expr: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(expr, str) and expr in definitions:
        return definitions[expr]
    return expr


def _world_env(program: CompiledWorldProgram, state: GameState) -> Environment:
    return Environment(
        parent=base_environment(),
        values=_host_values(store_specs={}, store={}),
        lazy_values=program.definitions,
        resolver=lambda name: _world_resolver(name, program, state),
    )


def _world_resolver(name: str, program: CompiledWorldProgram, state: GameState) -> Any:
    if name == "day":
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=1, persist="run"), value=state.day)
    if name in program.clocks_by_id:
        spec = program.clocks_by_id[name]
        value = state.world.progress_clocks.get(name)
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="clock", initial=0, title=spec.title, maximum=spec.segments, persist="run"), value=(0 if value is None else value.value))
    if name in {"health", "stress"}:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="run"), value=getattr(state.attributes, name))
    if name in {"money", "cigarettes"}:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="run"), value=state.world.inventory.get(name, 0))
    if name in state.world.values:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=state.world.values[name], persist="run"), value=state.world.values[name])
    if name in program.initial_values:
        initial = program.initial_values[name]
        current = state.world.values.get(name, initial)
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=initial, persist="run"), value=current)
    if name in program.initial_inventory:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=program.initial_inventory[name], persist="run"), value=state.world.inventory.get(name, program.initial_inventory[name]))
    if name in state.world.inventory:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="run"), value=state.world.inventory[name])
    return _MISSING
def _dummy_state(program: CompiledWorldProgram) -> GameState:
    from raygame.model.state import AttributeState, DeckState, GameState, WorldState

    return GameState(
        deck=DeckState(draw_pile=[]),
        attributes=AttributeState(health=program.initial_health, stress=program.initial_stress),
        world=WorldState(
            progress_clocks={clock_id: ProgressClockState(value=0, visible=True) for clock_id in program.clocks_by_id},
            inventory={
                **dict(program.initial_inventory),
                "money": program.initial_money,
                "cigarettes": program.initial_cigarettes,
            },
            values=dict(program.initial_values),
        ),
        screen=ScreenName.CITY,
    )


def _assert_effects_allowed(effects: tuple[Effect, ...], *, context: str) -> None:
    for effect in effects:
        assert effect.kind in WORLD_EFFECTS, f"{context} uses disallowed effect `{effect.kind}`"
