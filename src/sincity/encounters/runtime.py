from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from typing import Any

from sincity.content_lang.module_runtime import (
    bind_runtime_definition as _bind_runtime_definition,
    collect_top_level_definitions as _collect_top_level_definitions,
    resolve_definition_ref as _resolve_definition_ref,
    schema_definition_values as _schema_definition_values,
)
from sincity.content.runtime import _assert_cycle_start_expr_allowed
from sincity.content_lang.runtime_core import (
    build_check as _build_check,
    eval_react_condition as _eval_react_condition,
    eval_effect_list as _eval_effect_list,
    flatten_location as _flatten_location,
    host_values as _host_values,
    keyword_args as _keyword_args,
    render_location as _render_location,
    runtime_value as _runtime_value,
    unwrap as _unwrap,
    validate_action_template as _validate_action_template,
    validate_effect_target_symbols as _validate_effect_target_symbols_generic,
    validate_reaction_table as _validate_reaction_table,
    validate_react_template as _validate_react_template,
    validate_schema_forms as _validate_schema_forms_generic,
    validate_location_template as _validate_location_template,
    validate_template as _validate_template,
)
from sincity.model.defs import ActionDef, AddFieldPayload, Effect, LocationDef, ProgressClockSpec, SetFieldPayload, ShiftClockPayload

from .defs import (
    ActionHandle,
    ClockTemplate,
    CompiledEncounterProgram,
    EncounterMeta,
    EncounterSchemaError,
    EncounterSchemeError,
    LocationTemplate,
    ModuleState,
    ObjectValue,
    ReactRule,
    ReactionTable,
    ReactTemplate,
    RenderedEncounter,
    RuntimeClockValue,
    StateBindingValue,
    StoreFieldSpec,
)
from .lispy import Environment, Procedure, _MISSING, base_environment, desugar_define_form, evaluate, expand_includes, truthy


MAX_REACT_STEPS = 64
ENCOUNTER_ACTION_EFFECTS = frozenset({
    "set_field",
    "add_field",
    "copy_field",
    "shift_clock",
    "expr",
    "advance_cycle",
    "start_dialogue",
    "start_quick_dialogue",
    "end_encounter",
})
ENCOUNTER_COMPLETION_EFFECTS = frozenset({
    "set_field",
    "add_field",
    "shift_clock",
    "expr",
    "advance_cycle",
    "end_game",
    "start_encounter",
    "start_dialogue",
    "start_quick_dialogue",
})
ENCOUNTER_CYCLE_EFFECTS = frozenset({
    "set_field",
    "add_field",
    "copy_field",
    "shift_clock",
    "clock+",
    "clock-",
    "expr",
    "start_dialogue",
    "start_quick_dialogue",
    "end_encounter",
})


def compile_encounter_program(source: str, *, source_path: str | Path | None = None) -> CompiledEncounterProgram:
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
        if _is_call(form, "content"):
            assert content_form is None, "Encounter module can contain only one top-level `(content ...)` form."
            content_form = form
            continue
    assert content_form is not None, "Encounter module must contain a `(content ...)` form."
    kwargs = _keyword_args(content_form[1:], allowed={":meta", ":vars", ":reacts", ":reaction-die", ":on-success", ":on-fail", ":on-cycle-start", ":root"})
    root_expr = kwargs.get(":root")
    assert root_expr is not None, "Encounter content is missing required field: :root"
    module = ModuleState(root_expr=root_expr)
    _load_state_expr(_resolve_expr(kwargs.get(":vars"), raw_definitions), raw_definitions, module)
    definitions = _collect_top_level_definitions(forms)
    # Phase 6: evaluate definitions once at compile time
    initial_store = initial_store_from_specs(module.store_specs)
    builtins = _host_values(store_specs=module.store_specs, store=initial_store)
    eval_env = Environment(
        parent=base_environment(),
        values={**builtins, **_schema_definition_values(definitions)},
        resolver=lambda name: _state_resolver(name, store=initial_store, store_specs=module.store_specs),
    )
    definition_values: dict[str, Any] = {}
    for name, expr in definitions.items():
        value = evaluate(expr, eval_env)
        eval_env.values[name] = value
        definition_values[name] = value
    validation_env = _runtime_env(definitions=definition_values, store=initial_store, store_specs=module.store_specs)
    meta_expr = kwargs.get(":meta")
    if meta_expr is not None:
        module.metadata = _eval_meta_expr(meta_expr, validation_env)
    reacts_expr = kwargs.get(":reacts")
    if reacts_expr is not None:
        _eval_reacts_expr(reacts_expr, validation_env, module)
    reaction_die_expr = _reaction_die_body(kwargs.get(":reaction-die"))
    rewards_expr = kwargs.get(":on-success")
    fail_effects_expr = kwargs.get(":on-fail")
    cycle_start_effects_expr = kwargs.get(":on-cycle-start")
    module.rewards = _eval_effect_list(rewards_expr, validation_env)
    module.fail_effects = _eval_effect_list(fail_effects_expr, validation_env)
    module.cycle_start_effects = _eval_effect_list(cycle_start_effects_expr, validation_env)
    metadata = module.metadata or EncounterMeta(key=(path.stem if path is not None else "encounter"), title=(path.stem if path is not None else "Encounter"), description="")
    program = CompiledEncounterProgram(
        id=metadata.key,
        title=metadata.title,
        description=metadata.description,
        source_path=path,
        store_specs=dict(module.store_specs),
        clocks_by_id=dict(module.clocks_by_id),
        definitions=definition_values,
        react_rules=tuple(module.react_rules),
        view_expr=root_expr,
        rewards=module.rewards,
        fail_effects=module.fail_effects,
        cycle_start_effects=module.cycle_start_effects,
        reacts_expr=reacts_expr,
        rewards_expr=rewards_expr,
        fail_effects_expr=fail_effects_expr,
        cycle_start_effects_expr=cycle_start_effects_expr,
        reaction_die_expr=reaction_die_expr,
    )
    validate_encounter_program(program)
    return program


def initial_store(program: CompiledEncounterProgram) -> dict[str, Any]:
    return initial_store_from_specs(program.store_specs)


def initial_store_from_specs(store_specs: dict[str, StoreFieldSpec]) -> dict[str, Any]:
    return {field_id: deepcopy(spec.initial) for field_id, spec in store_specs.items()}


def render_encounter(program: CompiledEncounterProgram, store: dict[str, Any]) -> RenderedEncounter:
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    location = evaluate(program.view_expr, env)
    assert isinstance(location, LocationTemplate), f"Encounter view must resolve to a location: {program.id}"
    rendered = _render_location(program, location, location_path=())
    locations_by_id: dict[str, LocationDef] = {}
    parent_by_id: dict[str, str | None] = {}
    actions_by_id: dict[str, ActionDef] = {}
    actions_by_location: dict[str, tuple[str, ...]] = {}
    action_handles_by_id: dict[str, ActionHandle] = {}
    shown_clock_ids_by_location: dict[str, tuple[str, ...]] = {}
    shown_clocks_by_location: dict[str, tuple[Any, ...]] = {}
    nested_clocks_by_id: dict[str, Any] = {}
    _flatten_location(
        rendered,
        parent_id=None,
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        action_handles_by_id=action_handles_by_id,
        shown_clock_ids_by_location=shown_clock_ids_by_location,
        shown_clocks_by_location=shown_clocks_by_location,
        nested_clocks_by_id=nested_clocks_by_id,
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
        shown_clock_ids_by_location=shown_clock_ids_by_location,
        shown_clocks_by_location=shown_clocks_by_location,
        nested_clocks_by_id=nested_clocks_by_id,
    )


def next_react_rule(program: CompiledEncounterProgram, store: dict[str, Any], blocked_sources: set[str]) -> ReactRule | None:
    for rule in evaluate_react_rules(program, store):
        if rule.source in blocked_sources and react_rule_matches(program, store, rule):
            continue
        if react_rule_matches(program, store, rule):
            return rule
    return None


def react_rule_matches(program: CompiledEncounterProgram, store: dict[str, Any], rule: ReactRule) -> bool:
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    value = _eval_react_condition(rule.condition, env)
    return truthy(_unwrap(value))


def evaluate_reaction_die(program: CompiledEncounterProgram, store: dict[str, Any]) -> ReactionTable | None:
    if program.reaction_die_expr is None:
        return None
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    value = evaluate(program.reaction_die_expr, env)
    if value is None or value is False:
        return None
    assert isinstance(value, ReactionTable), f"{program.id}: reaction-die must return reaction-table or nil, got: {value!r}"
    _validate_reaction_table(value)
    return value


def evaluate_react_rules(program: CompiledEncounterProgram, store: dict[str, Any]) -> tuple[ReactRule, ...]:
    if program.reacts_expr is None:
        return ()
    module = ModuleState()
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    _eval_reacts_expr(program.reacts_expr, env, module)
    return tuple(module.react_rules)


def evaluate_cycle_start_effects(program: CompiledEncounterProgram, store: dict[str, Any], rng: Any | None = None) -> tuple[Effect, ...]:
    if program.cycle_start_effects_expr is None:
        return ()
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs, extra_values=_random_values(rng))
    return _eval_effect_list(program.cycle_start_effects_expr, env)


def evaluate_success_effects(program: CompiledEncounterProgram, store: dict[str, Any]) -> tuple[Effect, ...]:
    if program.rewards_expr is None:
        return ()
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    return _eval_effect_list(program.rewards_expr, env)


def evaluate_fail_effects(program: CompiledEncounterProgram, store: dict[str, Any]) -> tuple[Effect, ...]:
    if program.fail_effects_expr is None:
        return ()
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs)
    return _eval_effect_list(program.fail_effects_expr, env)


def evaluate_effect_expr(program: CompiledEncounterProgram, store: dict[str, Any], expr: Any, *, action_log: Any | None = None, rng: Any | None = None) -> Any:
    extra_values = {}
    if action_log is not None:
        extra_values["action-log!"] = action_log
    extra_values.update(_random_values(rng))
    env = _runtime_env(definitions=program.definitions, store=store, store_specs=program.store_specs, extra_values=extra_values)
    return evaluate(expr, env)


def validate_encounter_program(program: CompiledEncounterProgram) -> None:
    assert program.store_specs, f"{program.id}: encounter missing state."
    env = _runtime_env(definitions=program.definitions, store=initial_store(program), store_specs=program.store_specs)
    _validate_all_effect_target_symbols(program, env)
    _validate_all_schema_forms(program, env)
    for name, value in program.definitions.items():
        try:
            _validate_template(value)
        except EncounterSchemeError as exc:
            raise EncounterSchemeError(f"{program.id}: definition `{name}` has Scheme error: {exc}") from exc
        except EncounterSchemaError as exc:
            raise EncounterSchemaError(f"{program.id}: definition `{name}` has schema error: {exc}") from exc
        except Exception as exc:
            raise EncounterSchemaError(f"{program.id}: definition `{name}` is invalid: {exc}") from exc
    snapshot = render_encounter(program, initial_store(program))
    assert snapshot.root_location.title, f"{program.id}: root location missing title."
    for action in snapshot.actions_by_id.values():
        _assert_effects_allowed(action.effects, allowed=ENCOUNTER_ACTION_EFFECTS, context=f"{program.id}: action `{action.title}`")
        if action.check is not None:
            for outcome_name, outcome in (("ok", action.check.success), ("partial", action.check.cost), ("fail", action.check.fail)):
                _assert_effects_allowed(outcome.effects, allowed=ENCOUNTER_ACTION_EFFECTS, context=f"{program.id}: action `{action.title}` {outcome_name}")
    for rule in program.react_rules:
        _assert_effects_allowed(rule.effects, allowed=ENCOUNTER_ACTION_EFFECTS, context=f"{program.id}: react `{rule.source}`")
    if program.reaction_die_expr is not None:
        _validate_schema_forms(program.reaction_die_expr, env, context=f"{program.id}: reaction-die")
    if program.cycle_start_effects_expr is not None:
        _validate_schema_forms(program.cycle_start_effects_expr, env, context=f"{program.id}: on-cycle-start")
    if program.rewards_expr is not None:
        _validate_schema_forms(program.rewards_expr, env, context=f"{program.id}: on-success")
    if program.fail_effects_expr is not None:
        _validate_schema_forms(program.fail_effects_expr, env, context=f"{program.id}: on-fail")
        table = evaluate_reaction_die(program, initial_store(program))
        if table is not None:
            for face in table.faces:
                _assert_effects_allowed(face.effects, allowed=ENCOUNTER_CYCLE_EFFECTS, context=f"{program.id}: reaction face `{face.title}`")
    _assert_effects_allowed(program.cycle_start_effects, allowed=ENCOUNTER_CYCLE_EFFECTS, context=f"{program.id}: on-cycle-start")
    if program.cycle_start_effects_expr is not None:
        _assert_cycle_start_expr_allowed(program.cycle_start_effects_expr, allowed=ENCOUNTER_CYCLE_EFFECTS, context=f"{program.id}: on-cycle-start")
    for clock_id, spec in program.clocks_by_id.items():
        assert clock_id in program.store_specs, f"{program.id}: clock missing store spec: {clock_id}"
        assert spec.segments >= 1, f"{program.id}: invalid clock segments: {clock_id}"
    _validate_completion_effects(program)


def _validate_all_schema_forms(program: CompiledEncounterProgram, env: Environment) -> None:
    _validate_schema_forms(program.view_expr, env, context=f"{program.id}: root location")
    if program.reaction_die_expr is not None:
        _validate_schema_forms(program.reaction_die_expr, env, context=f"{program.id}: reaction-die")
    for rule in program.react_rules:
        assert isinstance(rule.condition, Procedure) and not rule.condition.params, f"{program.id}: react `{rule.source}` condition must be a zero-argument procedure"
        _validate_schema_forms(rule.condition.body, env, context=f"{program.id}: react `{rule.source}` condition")
        for effect in rule.effects:
            assert isinstance(effect, Effect), f"{program.id}: react `{rule.source}` contains non-effect value: {effect!r}"


def _validate_all_effect_target_symbols(program: CompiledEncounterProgram, env: Environment) -> None:
    for name, value in program.definitions.items():
        if isinstance(value, Procedure):
            _validate_effect_target_symbols_generic(value.body, env, context=f"{program.id}: definition `{name}`", local_symbols=frozenset(value.params))
    _validate_effect_target_symbols_generic(program.view_expr, env, context=f"{program.id}: root location")
    if program.reaction_die_expr is not None:
        _validate_effect_target_symbols_generic(program.reaction_die_expr, env, context=f"{program.id}: reaction-die")
    if program.cycle_start_effects_expr is not None:
        _validate_effect_target_symbols_generic(program.cycle_start_effects_expr, env, context=f"{program.id}: on-cycle-start")
    if program.rewards_expr is not None:
        _validate_effect_target_symbols_generic(program.rewards_expr, env, context=f"{program.id}: on-success")
    if program.fail_effects_expr is not None:
        _validate_effect_target_symbols_generic(program.fail_effects_expr, env, context=f"{program.id}: on-fail")


def _validate_schema_forms(expr: Any, env: Environment, *, context: str) -> None:
    _validate_schema_forms_generic(expr, env, context=context)


def _load_state_expr(expr: Any, definitions: dict[str, Any], module: ModuleState) -> None:
    if expr is None:
        return
    env = _schema_env(definitions=definitions)
    value = evaluate(expr, env)
    assert isinstance(value, list), f"Encounter :vars must evaluate to a list of var bindings, got: {value!r}"
    for binding in _expand_state_bindings(value, env):
        name, raw_value = binding
        value = raw_value if isinstance(raw_value, (ClockTemplate, StateBindingValue)) else evaluate(raw_value, env)
        if isinstance(value, ClockTemplate):
            spec = StoreFieldSpec(id=name, kind="clock", initial=value.initial, title=value.title, maximum=value.maximum, persist="encounter")
            module.store_specs[name] = spec
            module.clocks_by_id[name] = ProgressClockSpec(id=name, title=value.title, description=value.description, segments=value.maximum, initial=value.initial)
        elif isinstance(value, StateBindingValue):
            assert value.name == name, f"Imported state binding `{name}` must use the same source key."
            assert value.spec.persist in {"world_attr", "world_value", "world_inventory"}, f"Unsupported imported state binding for {name}: {value.spec.persist}"
            module.store_specs[name] = value.spec
        else:
            value = _runtime_value(value)
            assert isinstance(value, (bool, int, str, list, ObjectValue)), f"Unsupported state value for {name}: {value!r}"
            module.store_specs[name] = StoreFieldSpec(id=name, kind="value", initial=value)


def _expand_state_bindings(items: list[Any], env: Environment) -> list[tuple[str, Any]]:
    result: list[tuple[str, Any]] = []
    for item in items:
        assert isinstance(item, list) and len(item) == 2 and isinstance(item[0], str), \
            f":vars must be a list of var bindings, got: {item!r}"
        result.append((item[0], item[1]))
    names: set[str] = set()
    for name, _value in result:
        assert name not in names, f"Duplicate state binding: {name}"
        names.add(name)
    return result


def _eval_meta_expr(expr: Any, env: Environment) -> EncounterMeta:
    value = evaluate(expr, env)
    assert isinstance(value, EncounterMeta), f"meta form did not produce meta: {value!r}"
    return value


def _eval_reacts_expr(expr: Any, env: Environment, module: ModuleState) -> None:
    value = evaluate(expr, env)
    assert isinstance(value, list), f"Encounter :reacts must evaluate to a list of react forms, got: {value!r}"
    for index, item in enumerate(value):
        if item is None:
            continue
        assert isinstance(item, ReactTemplate), f":reacts expects react or nil, got: {item!r}"
        _validate_react_template(item)
        module.react_rules.append(ReactRule(condition=item.condition, effects=item.effects, source=f"react[{index}]", effects_expr=item.effects_expr))


def _reaction_die_body(expr: Any | None) -> Any | None:
    if expr is None:
        return None
    assert _is_call(expr, "reaction-die"), "Encounter :reaction-die must be `(reaction-die expr)`."
    assert len(expr) == 2, "`reaction-die` expects one expression."
    return expr[1]


def _resolve_expr(expr: Any, definitions: dict[str, Any]) -> Any:
    return _resolve_definition_ref(expr, definitions)


def _runtime_env(
    *,
    definitions: dict[str, Any],
    store: dict[str, Any],
    store_specs: dict[str, StoreFieldSpec],
    extra_values: dict[str, Any] | None = None,
) -> Environment:
    builtins = _host_values(store_specs=store_specs, store=store)
    env = Environment(
        parent=base_environment(),
        values={**builtins, **_schema_random_values()},
        resolver=lambda name: _state_resolver(name, store=store, store_specs=store_specs),
    )
    for name, value in definitions.items():
        env.values[name] = _bind_runtime_definition(value, env)
    if extra_values is not None:
        env.values.update(extra_values)
    return env


def _schema_env(*, definitions: dict[str, Any]) -> Environment:
    return Environment(parent=base_environment(), values={**_host_values(store_specs={}, store={}), **_schema_random_values(), **_schema_definition_values(definitions)})


def _schema_random_values() -> dict[str, Any]:
    return {
        "random-float": lambda: 0.0,
        "random-choice": lambda values: _first_random_choice(values),
    }


def _random_values(rng: Any | None) -> dict[str, Any]:
    if rng is None:
        return {}
    return {
        "random-float": rng.random_float,
        "random-choice": lambda values: rng.random_choice(tuple(values)),
    }


def _first_random_choice(values: Any) -> Any:
    assert values, "random-choice expects a non-empty list."
    return values[0]





def _state_resolver(name: str, *, store: dict[str, int | bool | str], store_specs: dict[str, StoreFieldSpec]) -> Any:
    if name in store_specs:
        spec = store_specs[name]
        value = store.get(name, spec.initial)
        if spec.kind == "clock":
            assert spec.maximum is not None, f"Clock binding missing maximum: {name}"
            value = RuntimeClockValue(title=spec.title, description="", value=int(value), maximum=spec.maximum)
        return StateBindingValue(name=name, spec=spec, value=value)
    return _MISSING


def _validate_completion_effects(program: CompiledEncounterProgram) -> None:
    for bucket_name, effects in {"on-success": program.rewards, "on-fail": program.fail_effects}.items():
        _assert_effects_allowed(effects, allowed=ENCOUNTER_COMPLETION_EFFECTS, context=f"{program.id}: {bucket_name}")
        for effect in effects:
            if effect.kind in {"set_field", "add_field", "copy_field", "shift_clock"}:
                key = _effect_target(effect)
                spec = program.store_specs.get(key)
                assert spec is None or spec.persist != "encounter", f"{program.id}: {bucket_name} cannot target encounter-local field `{key}`"
            assert effect.kind != "end_encounter", f"{program.id}: {bucket_name} cannot contain end-encounter effect"


def _effect_target(effect: Effect) -> str:
    value = effect.value
    if isinstance(value, (SetFieldPayload, AddFieldPayload, ShiftClockPayload)):
        return value.target
    assert isinstance(value, str), f"Effect `{effect.kind}` payload must be structured or string: {value!r}"
    key, _, _ = value.partition(":")
    return key


def _assert_effects_allowed(effects: tuple[Effect, ...], *, allowed: frozenset[str], context: str) -> None:
    for effect in effects:
        assert effect.kind in allowed, f"{context} uses disallowed effect `{effect.kind}`"


def _is_call(node: Any, name: str) -> bool:
    return isinstance(node, list) and bool(node) and node[0] == name
