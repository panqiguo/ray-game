from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sincity.content_lang.runtime_core import (
    flatten_scene as _flatten_scene,
    eval_react_condition as _eval_react_condition,
    eval_effect_list as _eval_effect_list,
    host_values as _host_values,
    keyword_args as _keyword_args,
    render_scene as _render_scene,
    validate_action_template as _validate_action_template,
    validate_react_template as _validate_react_template,
    validate_schema_forms as _validate_schema_forms_generic,
    validate_scene_template as _validate_scene_template,
)
from sincity.encounters.defs import ActionTemplate, ClockTemplate, EncounterMeta, EncounterSchemaError, EncounterSchemeError, ReactRule, ReactTemplate, SceneTemplate, StateBindingValue, StoreFieldSpec, TaskStepTemplate, TaskTemplate
from sincity.encounters.lispy import Environment, Procedure, StringAtom, _MISSING, base_environment, desugar_define_form, evaluate, expand_includes, truthy
from sincity.model.defs import CompiledScenario, Effect, LocationNode, ProgressClockSpec
from sincity.model.enums import ScreenName
from sincity.model.state import GameState, ProgressClockState


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
    task_templates: tuple[TaskTemplate, ...]
    view_expr: Any
    initial_health: int
    initial_stress: int
    initial_money: int
    initial_cigarettes: int
    initial_inventory: dict[str, int]
    initial_values: dict[str, int | bool | str]
    initial_growth_choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class RenderedTaskStep:
    title: str
    completed: bool
    active: bool = False


@dataclass(frozen=True)
class RenderedTask:
    kind: str
    title: str
    description: str
    active: bool
    completed: bool
    failed: bool
    steps: tuple[RenderedTaskStep, ...] = ()


WORLD_EFFECTS = frozenset({
    "set_field",
    "add_field",
    "copy_field",
    "shift_clock",
    "reset_hand",
    "advance_day",
    "end_game",
    "upgrade_spirit_value",
    "add_spirit_slot",
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
    raw_definitions: dict[str, Any] = {}
    content_form: Any | None = None
    for form in forms:
        define_form = desugar_define_form(form)
        if define_form is not None:
            name, expr = define_form
            raw_definitions[name] = expr
            continue
        if isinstance(form, list) and form and form[0] == "content":
            assert content_form is None, "World module can contain only one top-level `(content ...)` form."
            content_form = form
            continue
    assert isinstance(content_form, list) and content_form and content_form[0] == "content", "World module must end with a `(content ...)` form."
    kwargs = _keyword_args(content_form[1:], allowed={":meta", ":state", ":reacts", ":tasks", ":root"})
    clocks, state_values = _resolve_state_specs(kwargs.get(":state"), raw_definitions)
    env = _world_schema_env(definitions={}, clocks_by_id=clocks, initial_values=state_values, initial_inventory=dict(initial_inventory or {}))
    definitions = _eval_top_level_definitions(forms, env)
    metadata = _resolve_meta(kwargs.get(":meta"), env, path)
    react_rules = _resolve_reacts(kwargs.get(":reacts"), env)
    task_templates = _resolve_tasks(kwargs.get(":tasks"), env)
    root_expr = kwargs.get(":root")
    assert root_expr is not None, "Content is missing required field: :root"
    program = CompiledWorldProgram(
        id=metadata.key,
        title=metadata.title,
        description=metadata.description,
        source_path=path,
        screen=ScreenName.CITY,
        clocks_by_id=clocks,
        definitions=definitions,
        react_rules=tuple(react_rules),
        task_templates=task_templates,
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


def render_tasks(program: CompiledWorldProgram, state: GameState) -> tuple[RenderedTask, ...]:
    env = _world_env(program, state)
    rendered: list[RenderedTask] = []
    for task in program.task_templates:
        active = truthy(_eval_react_condition(task.active, env))
        completed = truthy(_eval_react_condition(task.completed, env))
        failed = truthy(_eval_react_condition(task.failed, env))
        if not (active or completed or failed):
            continue
        steps = _render_task_steps(task.steps, env)
        rendered.append(
            RenderedTask(
                kind=task.kind,
                title=str(evaluate(task.title, env)),
                description=str(evaluate(task.description, env)),
                active=active,
                completed=completed,
                failed=failed,
                steps=steps,
            )
        )
    return tuple(rendered)


def evaluate_world_expr(program: CompiledWorldProgram, state: GameState, expr: Any) -> Any:
    return evaluate(expr, _world_env(program, state))


def evaluate_world_react_effects(program: CompiledWorldProgram, state: GameState, rule: ReactRule) -> tuple[Effect, ...]:
    if rule.effects_expr is None:
        return rule.effects
    return _eval_effect_list(rule.effects_expr, _world_env(program, state))


def _render_task_steps(steps: tuple[TaskStepTemplate, ...], env: Environment) -> tuple[RenderedTaskStep, ...]:
    rendered: list[RenderedTaskStep] = []
    first_open_seen = False
    for step in steps:
        completed = truthy(_eval_react_condition(step.completed, env))
        active = False
        if not completed and not first_open_seen:
            active = True
            first_open_seen = True
        rendered.append(RenderedTaskStep(title=str(evaluate(step.title, env)), completed=completed, active=active))
    return tuple(rendered)


def validate_world_program(program: CompiledWorldProgram) -> None:
    dummy_state = _dummy_state(program)
    env = _world_env(program, dummy_state)
    for name, value in program.definitions.items():
        try:
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
        assert isinstance(rule.condition, Procedure) and not rule.condition.params, f"{program.id}: react `{rule.source}` condition must be a zero-argument procedure"
        _validate_world_schema_forms(rule.condition.body, env, context=f"{program.id}: react `{rule.source}` condition")
        for effect in rule.effects:
            assert isinstance(effect, Effect), f"{program.id}: react `{rule.source}` contains non-effect value: {effect!r}"
    snapshot = render_world(program, dummy_state)
    assert snapshot.root_child_location_ids, f"{program.id}: world root must expose at least one child node."
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
    for task in program.task_templates:
        _validate_task_template(program, task, env)


def _validate_world_schema_forms(expr: Any, env: Environment, *, context: str) -> None:
    _validate_schema_forms_generic(expr, env, context=context, allow_nil_templates=True)


def react_rule_matches(program: CompiledWorldProgram, state: GameState, rule: ReactRule) -> bool:
    return truthy(_eval_react_condition(rule.condition, _world_env(program, state)))


def next_react_rule(program: CompiledWorldProgram, state: GameState, blocked_sources: set[str]) -> ReactRule | None:
    for rule in program.react_rules:
        if rule.source in blocked_sources and react_rule_matches(program, state, rule):
            continue
        if react_rule_matches(program, state, rule):
            return rule
    return None


def _eval_top_level_definitions(forms: list[Any], env: Environment) -> dict[str, Any]:
    definitions: dict[str, Any] = {}
    for form in forms:
        if not isinstance(form, list) or not form:
            evaluate(form, env)
            continue
        head = form[0]
        if head == "content":
            continue
        define_form = desugar_define_form(form)
        if define_form is not None:
            name, expr = define_form
            value = evaluate(expr, env)
            env.values[name] = value
            definitions[name] = value
            continue
        evaluate(form, env)
    return definitions


def _resolve_meta(expr: Any, env: Environment, path: Path | None) -> EncounterMeta:
    if expr is None:
        stem = path.stem if path is not None else "content"
        return EncounterMeta(key=stem, title=stem, description="")
    value = evaluate(expr, env)
    assert isinstance(value, EncounterMeta), f"meta form did not produce meta: {value!r}"
    return value


def _resolve_state_specs(expr: Any, definitions: dict[str, Any]) -> tuple[dict[str, ProgressClockSpec], dict[str, int | bool | str]]:
    if expr is None:
        return {}, {}
    env = Environment(parent=base_environment(), values={**_host_values(store_specs={}, store={}), **_schema_definition_values(definitions)})
    value = evaluate(expr, env)
    bindings = _flatten_state_bindings(value)
    clocks_by_id: dict[str, ProgressClockSpec] = {}
    initial_values: dict[str, int | bool | str] = {}
    for binding in bindings:
        name = binding[0]
        value = evaluate(binding[1], env)
        if isinstance(value, ClockTemplate):
            clocks_by_id[name] = ProgressClockSpec(id=name, title=value.title, description=value.description, segments=value.maximum)
        else:
            assert isinstance(value, (bool, int, str)), f"Unsupported world state value for {name}: {value!r}"
            initial_values[name] = value
    return clocks_by_id, initial_values


def _flatten_state_bindings(value: Any) -> list[list[Any]]:
    if value is None:
        return []
    assert isinstance(value, list), f"World :state must evaluate to a list of var bindings, got: {value!r}"
    if len(value) == 2 and isinstance(value[0], str):
        return [value]
    result: list[list[Any]] = []
    for item in value:
        result.extend(_flatten_state_bindings(item))
    names: set[str] = set()
    for binding in result:
        assert len(binding) == 2 and isinstance(binding[0], str), f"Each world state binding must be `(var 'name value)`, got: {binding!r}"
        assert binding[0] not in names, f"Duplicate state binding: {binding[0]}"
        names.add(binding[0])
    return result


def _resolve_expr(expr: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(expr, str) and expr in definitions:
        return definitions[expr]
    return expr


def _schema_definition_values(definitions: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    env = Environment(parent=base_environment(), values={**_host_values(store_specs={}, store={}), **values})
    for name, expr in definitions.items():
        if not _is_schema_definition_expr(name, expr):
            continue
        value = evaluate(expr, env)
        env.values[name] = value
        values[name] = value
    return values


def _is_schema_definition_expr(name: str, expr: Any) -> bool:
    if isinstance(expr, (bool, int, StringAtom)):
        return True
    if not isinstance(expr, list) or not expr:
        return False
    if expr[0] in {"quote", "lambda", "var"}:
        return True
    return expr[0] in {"list", "append"} and (name.endswith("-vars") or name.endswith("_vars") or name.endswith("-state") or name.endswith("_state"))


def _resolve_reacts(expr: Any, env: Environment) -> list[ReactRule]:
    if expr is None:
        return []
    value = evaluate(expr, env)
    assert isinstance(value, list), f":reacts must evaluate to a list of react forms, got: {value!r}"
    rules: list[ReactRule] = []
    for index, item in enumerate(value):
        if item is None:
            continue
        _validate_react_template(item)
        rules.append(ReactRule(condition=item.condition, effects=item.effects, source=f"react[{index}]", effects_expr=item.effects_expr))
    return rules


def _resolve_tasks(expr: Any, env: Environment) -> tuple[TaskTemplate, ...]:
    if expr is None:
        return ()
    value = evaluate(expr, env)
    assert isinstance(value, list), f":tasks must evaluate to a list of task forms, got: {value!r}"
    tasks: list[TaskTemplate] = []
    seen_titles: set[str] = set()
    for item in value:
        if item is None:
            continue
        assert isinstance(item, TaskTemplate), f"tasks expects task forms, got: {item!r}"
        title = str(evaluate(item.title, env))
        assert title not in seen_titles, f"Duplicate task title: {title}"
        assert item.kind in {"主线", "支线", "压力"}, f"Unsupported task kind: {item.kind}"
        seen_titles.add(title)
        tasks.append(item)
    return tuple(tasks)


def _validate_task_template(program: CompiledWorldProgram, task: TaskTemplate, env: Environment) -> None:
    assert task.kind in {"主线", "支线", "压力"}, f"{program.id}: unsupported task kind: {task.kind}"
    truthy(_eval_react_condition(task.active, env))
    truthy(_eval_react_condition(task.completed, env))
    truthy(_eval_react_condition(task.failed, env))
    evaluate(task.title, env)
    evaluate(task.description, env)
    for step in task.steps:
        assert isinstance(step, TaskStepTemplate), f"{program.id}: task contains non-step: {step!r}"
        evaluate(step.title, env)
        _eval_react_condition(step.completed, env)


def _world_schema_env(
    *,
    definitions: dict[str, Any],
    clocks_by_id: dict[str, ProgressClockSpec],
    initial_values: dict[str, int | bool | str],
    initial_inventory: dict[str, int],
) -> Environment:
    return Environment(
        parent=base_environment(),
        values={**_host_values(store_specs={}, store={}), **definitions},
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
    if name in {"health", "stress", "energy", "money", "cigarettes"}:
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="run"), value=0)
    if name in initial_values:
        initial = initial_values[name]
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=initial, persist="run"), value=initial)
    if name in initial_inventory:
        initial = initial_inventory[name]
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=initial, persist="run"), value=initial)
    return _MISSING


def _world_env(program: CompiledWorldProgram, state: GameState) -> Environment:
    env = Environment(
        parent=base_environment(),
        values={**_host_values(store_specs={}, store={})},
        resolver=lambda name: _world_resolver(name, program, state),
    )
    env.values.update({name: _bind_world_definition(value, env) for name, value in program.definitions.items()})
    return env


def _bind_world_definition(value: Any, env: Environment) -> Any:
    if isinstance(value, Procedure):
        return Procedure(params=value.params, body=value.body, env=env)
    return value


def _world_resolver(name: str, program: CompiledWorldProgram, state: GameState) -> Any:
    if name == "day":
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=1, persist="run"), value=state.day)
    if name in program.clocks_by_id:
        spec = program.clocks_by_id[name]
        value = state.world.progress_clocks.get(name)
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="clock", initial=0, title=spec.title, maximum=spec.segments, persist="run"), value=(0 if value is None else value.value))
    if name in {"health", "stress", "energy"}:
        attr_name = "stress" if name == "energy" else name
        return StateBindingValue(name=name, spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="run"), value=getattr(state.attributes, attr_name))
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
    from sincity.model.state import AttributeState, DeckState, GameState, WorldState

    return GameState(
        deck=DeckState(),
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
