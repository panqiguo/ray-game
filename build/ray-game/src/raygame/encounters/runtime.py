from __future__ import annotations

from pathlib import Path
from typing import Any

from raygame.content_lang.runtime_core import (
    build_check as _build_check,
    eval_effect_list as _eval_effect_list,
    flatten_scene as _flatten_scene,
    host_values as _host_values,
    keyword_args as _keyword_args,
    render_scene as _render_scene,
    unwrap as _unwrap,
    validate_action_template as _validate_action_template,
    validate_react_template as _validate_react_template,
    validate_schema_forms as _validate_schema_forms_generic,
    validate_scene_template as _validate_scene_template,
    validate_template as _validate_template,
)
from raygame.model.defs import ActionDef, Effect, LocationNode, ProgressClockSpec

from .defs import (
    ActionHandle,
    ClockTemplate,
    CompiledEncounterProgram,
    EncounterMeta,
    EncounterSchemaError,
    EncounterSchemeError,
    ModuleState,
    ReactRule,
    ReactTemplate,
    RenderedEncounter,
    SceneTemplate,
    StateBindingValue,
    StoreFieldSpec,
)
from .lispy import Environment, _MISSING, base_environment, evaluate, expand_includes, truthy


MAX_REACT_STEPS = 64
ENCOUNTER_ACTION_EFFECTS = frozenset({
    "set_field",
    "add_field",
    "shift_clock",
    "reset_hand",
    "start_dialogue",
    "start_quick_dialogue",
    "end_encounter",
})
ENCOUNTER_COMPLETION_EFFECTS = frozenset({
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


def compile_encounter_program(source: str, *, source_path: str | Path | None = None) -> CompiledEncounterProgram:
    path = Path(source_path) if source_path is not None else None
    forms = expand_includes(source, source_path=path, include_stack=(() if path is None else (path,)))
    definitions: dict[str, Any] = {}
    content_form: Any | None = None
    top_level_exprs: list[Any] = []
    for form in forms:
        if _is_call(form, "define"):
            assert len(form) == 3 and isinstance(form[1], str), "`define` expects name and expr."
            definitions[form[1]] = form[2]
            continue
        if _is_call(form, "content"):
            assert content_form is None, "Encounter module can contain only one top-level `(content ...)` form."
            content_form = form
            continue
        top_level_exprs.append(form)
    assert content_form is not None, "Encounter module must contain a `(content ...)` form."
    kwargs = _keyword_args(content_form[1:], allowed={":meta", ":state", ":reacts", ":on-success", ":on-fail", ":root"})
    root_expr = _resolve_expr(kwargs.get(":root"), definitions)
    assert root_expr is not None, "Encounter content is missing required field: :root"
    module = ModuleState(root_expr=root_expr)
    _load_state_expr(_resolve_expr(kwargs.get(":state"), definitions), definitions, module)
    runtime_env = _runtime_env(definitions=definitions, store=initial_store_from_specs(module.store_specs), store_specs=module.store_specs)
    for expr in top_level_exprs:
        evaluate(expr, runtime_env)
    meta_expr = _resolve_expr(kwargs.get(":meta"), definitions)
    if meta_expr is not None:
        module.metadata = _eval_meta_expr(meta_expr, runtime_env)
    reacts_expr = _resolve_expr(kwargs.get(":reacts"), definitions)
    if reacts_expr is not None:
        _eval_reacts_expr(reacts_expr, runtime_env, module)
    module.rewards = _eval_effect_list(_resolve_expr(kwargs.get(":on-success"), definitions), runtime_env)
    module.fail_effects = _eval_effect_list(_resolve_expr(kwargs.get(":on-fail"), definitions), runtime_env)
    metadata = module.metadata or EncounterMeta(key=(path.stem if path is not None else "encounter"), title=(path.stem if path is not None else "Encounter"), description="")
    program = CompiledEncounterProgram(
        id=metadata.key,
        title=metadata.title,
        description=metadata.description,
        source_path=path,
        store_specs=dict(module.store_specs),
        clocks_by_id=dict(module.clocks_by_id),
        definitions=definitions,
        react_rules=tuple(module.react_rules),
        view_expr=root_expr,
        rewards=module.rewards,
        fail_effects=module.fail_effects,
    )
    validate_encounter_program(program)
    return program


def initial_store(program: CompiledEncounterProgram) -> dict[str, int | bool | str]:
    return initial_store_from_specs(program.store_specs)


def initial_store_from_specs(store_specs: dict[str, StoreFieldSpec]) -> dict[str, int | bool | str]:
    return {field_id: spec.initial for field_id, spec in store_specs.items()}


def render_encounter(program: CompiledEncounterProgram, store: dict[str, int | bool | str]) -> RenderedEncounter:
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    scene = evaluate(program.view_expr, env)
    assert isinstance(scene, SceneTemplate), f"Encounter view must resolve to a scene: {program.id}"
    rendered = _render_scene(program, scene, scene_path=())
    locations_by_id: dict[str, LocationNode] = {}
    parent_by_id: dict[str, str | None] = {}
    actions_by_id: dict[str, ActionDef] = {}
    actions_by_location: dict[str, tuple[str, ...]] = {}
    action_handles_by_id: dict[str, ActionHandle] = {}
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
    return RenderedEncounter(
        title=program.title,
        description=program.description,
        root=rendered,
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        action_handles_by_id=action_handles_by_id,
        shown_clock_ids_by_scene=shown_clock_ids_by_scene,
    )


def next_react_rule(program: CompiledEncounterProgram, store: dict[str, int | bool | str], blocked_sources: set[str]) -> ReactRule | None:
    for rule in program.react_rules:
        if rule.source in blocked_sources and react_rule_matches(program, store, rule):
            continue
        if react_rule_matches(program, store, rule):
            return rule
    return None


def react_rule_matches(program: CompiledEncounterProgram, store: dict[str, int | bool | str], rule: ReactRule) -> bool:
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    value = evaluate(rule.condition_expr, env)
    return truthy(_unwrap(value))


def validate_encounter_program(program: CompiledEncounterProgram) -> None:
    assert program.store_specs, f"{program.id}: encounter missing state."
    env = _runtime_env(definitions=program.definitions, store=initial_store(program), store_specs=program.store_specs)
    _validate_all_schema_forms(program, env)
    for name, expr in program.definitions.items():
        if _is_call(expr, "state"):
            continue
        try:
            value = env.lookup(name)
            _validate_template(value)
        except EncounterSchemeError as exc:
            raise EncounterSchemeError(f"{program.id}: definition `{name}` has Scheme error: {exc}") from exc
        except EncounterSchemaError as exc:
            raise EncounterSchemaError(f"{program.id}: definition `{name}` has schema error: {exc}") from exc
        except Exception as exc:
            raise EncounterSchemaError(f"{program.id}: definition `{name}` is invalid: {exc}") from exc
    snapshot = render_encounter(program, initial_store(program))
    assert snapshot.root_location.title, f"{program.id}: root scene missing title."
    for action in snapshot.actions_by_id.values():
        _assert_effects_allowed(action.effects, allowed=ENCOUNTER_ACTION_EFFECTS, context=f"{program.id}: action `{action.title}`")
        if action.check is not None:
            for outcome_name, outcome in (("ok", action.check.success), ("partial", action.check.cost), ("fail", action.check.fail)):
                _assert_effects_allowed(outcome.effects, allowed=ENCOUNTER_ACTION_EFFECTS, context=f"{program.id}: action `{action.title}` {outcome_name}")
    for rule in program.react_rules:
        _assert_effects_allowed(rule.effects, allowed=ENCOUNTER_ACTION_EFFECTS, context=f"{program.id}: react `{rule.source}`")
    for clock_id, spec in program.clocks_by_id.items():
        assert clock_id in program.store_specs, f"{program.id}: clock missing store spec: {clock_id}"
        assert spec.segments >= 1, f"{program.id}: invalid clock segments: {clock_id}"
    _validate_completion_effects(program)


def _validate_all_schema_forms(program: CompiledEncounterProgram, env: Environment) -> None:
    for name, expr in program.definitions.items():
        _validate_schema_forms(expr, env, context=f"{program.id}: definition `{name}`")
    _validate_schema_forms(program.view_expr, env, context=f"{program.id}: root scene")
    for rule in program.react_rules:
        _validate_schema_forms(rule.condition_expr, env, context=f"{program.id}: react `{rule.source}` condition")
        for effect in rule.effects:
            assert isinstance(effect, Effect), f"{program.id}: react `{rule.source}` contains non-effect value: {effect!r}"


def _validate_schema_forms(expr: Any, env: Environment, *, context: str) -> None:
    _validate_schema_forms_generic(expr, env, context=context)


def _load_state_expr(expr: Any, definitions: dict[str, Any], module: ModuleState) -> None:
    if expr is None:
        return
    assert _is_call(expr, "state"), "Encounter state must be a `(state ...)` form."
    env = _schema_env(definitions=definitions)
    for binding in expr[1:]:
        assert isinstance(binding, list) and len(binding) == 2 and isinstance(binding[0], str), "Each state binding must be `(name value)`."
        name = binding[0]
        value = evaluate(binding[1], env)
        if isinstance(value, ClockTemplate):
            spec = StoreFieldSpec(id=name, kind="clock", initial=value.initial, title=value.title, maximum=value.maximum, persist="encounter")
            module.store_specs[name] = spec
            module.clocks_by_id[name] = ProgressClockSpec(id=name, title=value.title, description=value.description, segments=value.maximum)
        else:
            assert isinstance(value, (bool, int, str)), f"Unsupported state value for {name}: {value!r}"
            module.store_specs[name] = StoreFieldSpec(id=name, kind="value", initial=value)


def _eval_meta_expr(expr: Any, env: Environment) -> EncounterMeta:
    value = evaluate(expr, env)
    assert isinstance(value, EncounterMeta), f"meta form did not produce meta: {value!r}"
    return value


def _eval_reacts_expr(expr: Any, env: Environment, module: ModuleState) -> None:
    value = evaluate(expr, env)
    items = value if isinstance(value, list) else [value]
    for index, item in enumerate(items):
        if item is None:
            continue
        assert isinstance(item, ReactTemplate), f"reacts expects react or nil, got: {item!r}"
        _validate_react_template(item)
        module.react_rules.append(ReactRule(condition_expr=item.condition_expr, effects=item.effects, source=f"react[{index}]"))


def _resolve_expr(expr: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(expr, str) and expr in definitions:
        return definitions[expr]
    return expr


def _runtime_env(*, definitions: dict[str, Any], store: dict[str, int | bool | str], store_specs: dict[str, StoreFieldSpec]) -> Environment:
    builtins = _host_values(store_specs=store_specs, store=store)
    return Environment(
        parent=base_environment(),
        values=builtins,
        lazy_values=definitions,
        resolver=lambda name: _state_resolver(name, store=store, store_specs=store_specs),
    )


def _schema_env(*, definitions: dict[str, Any]) -> Environment:
    return Environment(parent=base_environment(), values=_host_values(store_specs={}, store={}), lazy_values=definitions)


def _state_resolver(name: str, *, store: dict[str, int | bool | str], store_specs: dict[str, StoreFieldSpec]) -> Any:
    if name in store_specs:
        spec = store_specs[name]
        return StateBindingValue(name=name, spec=spec, value=store.get(name, spec.initial))
    return _MISSING


def _validate_completion_effects(program: CompiledEncounterProgram) -> None:
    for bucket_name, effects in {"on-success": program.rewards, "on-fail": program.fail_effects}.items():
        _assert_effects_allowed(effects, allowed=ENCOUNTER_COMPLETION_EFFECTS, context=f"{program.id}: {bucket_name}")
        for effect in effects:
            if effect.kind in {"set_field", "add_field", "shift_clock"}:
                assert isinstance(effect.value, str), f"{program.id}: {bucket_name} effect payload must be string"
                key, _, _ = effect.value.partition(":")
                assert key not in program.store_specs, f"{program.id}: {bucket_name} cannot target encounter-local field `{key}`"
            assert effect.kind != "end_encounter", f"{program.id}: {bucket_name} cannot contain end-encounter effect"


def _assert_effects_allowed(effects: tuple[Effect, ...], *, allowed: frozenset[str], context: str) -> None:
    for effect in effects:
        assert effect.kind in allowed, f"{context} uses disallowed effect `{effect.kind}`"


def _is_call(node: Any, name: str) -> bool:
    return isinstance(node, list) and bool(node) and node[0] == name
