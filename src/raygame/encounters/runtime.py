from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

from raygame.model.defs import ActionDef, CheckDef, Effect, InputRequirement, LocationNode, OutcomeDef, ProgressClockSpec
from raygame.model.enums import Risk, ScreenName, Suit

from .defs import (
    ActionHandle,
    ActionTemplate,
    CheckTemplate,
    ClockTemplate,
    CompiledEncounterProgram,
    EncounterMeta,
    EncounterSchemaError,
    EncounterSchemeError,
    ModuleDeclaration,
    ModuleState,
    OutcomeTemplate,
    ReactRule,
    RenderedAction,
    RenderedEncounter,
    RenderedScene,
    SceneTemplate,
    StateBindingValue,
    StoreFieldSpec,
)
from .lispy import Environment, _MISSING, base_environment, evaluate, expand_includes


MAX_REACT_STEPS = 64
RISK_BY_NAME = {"low": Risk.LOW, "mid": Risk.MID, "high": Risk.HIGH}
SUIT_BY_NAME = {
    "reason": Suit.REASON,
    "force": Suit.FORCE,
    "empathy": Suit.EMPATHY,
    "instinct": Suit.INSTINCT,
}


def compile_encounter_program(source: str, *, source_path: str | Path | None = None) -> CompiledEncounterProgram:
    path = Path(source_path) if source_path is not None else None
    forms = expand_includes(source, source_path=path, include_stack=(() if path is None else (path,)))
    definitions: dict[str, Any] = {}
    declarations: list[ModuleDeclaration] = []
    root_expr: Any | None = None
    for form in forms:
        if _is_call(form, "define"):
            assert len(form) == 3 and isinstance(form[1], str), "`define` expects name and expr."
            definitions[form[1]] = form[2]
            continue
        if _is_call(form, "state"):
            declarations.append(ModuleDeclaration(kind="state", value=form))
            continue
        if _is_call(form, "reacts"):
            declarations.append(ModuleDeclaration(kind="reacts", value=form))
            continue
        if _is_call(form, "meta"):
            declarations.append(ModuleDeclaration(kind="meta", value=form))
            continue
        if _is_call(form, "on-success"):
            declarations.append(ModuleDeclaration(kind="on-success", value=form))
            continue
        if _is_call(form, "on-fail"):
            declarations.append(ModuleDeclaration(kind="on-fail", value=form))
            continue
        root_expr = form
    assert root_expr is not None, "Encounter module must end with a root scene expression."
    module = ModuleState(root_expr=root_expr)
    _load_state(declarations, definitions, module)
    runtime_env = _runtime_env(definitions=definitions, store=initial_store_from_specs(module.store_specs), store_specs=module.store_specs)
    for declaration in declarations:
        if declaration.kind == "meta":
            module.metadata = _eval_meta(declaration.value, runtime_env)
        elif declaration.kind == "reacts":
            _eval_reacts(declaration.value, runtime_env, module)
        elif declaration.kind == "on-success":
            module.rewards = _eval_effect_list(declaration.value[1], runtime_env)
        elif declaration.kind == "on-fail":
            module.fail_effects = _eval_effect_list(declaration.value[1], runtime_env)
    metadata = module.metadata or EncounterMeta(key=(path.stem if path is not None else "encounter"), title=(path.stem if path is not None else "Encounter"), description="")
    return CompiledEncounterProgram(
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
    return bool(_unwrap(value))


def validate_encounter_program(program: CompiledEncounterProgram) -> None:
    assert program.store_specs, f"{program.id}: encounter missing state."
    snapshot = render_encounter(program, initial_store(program))
    assert snapshot.root.root.title, f"{program.id}: root scene missing title."
    for clock_id, spec in program.clocks_by_id.items():
        assert clock_id in program.store_specs, f"{program.id}: clock missing store spec: {clock_id}"
        assert spec.segments >= 1, f"{program.id}: invalid clock segments: {clock_id}"


def _load_state(declarations: list[ModuleDeclaration], definitions: dict[str, Any], module: ModuleState) -> None:
    state_forms = [item.value for item in declarations if item.kind == "state"]
    assert len(state_forms) <= 1, "Encounter module can contain at most one state block."
    if not state_forms:
        return
    env = _schema_env(definitions=definitions)
    for binding in state_forms[0][1:]:
        assert isinstance(binding, list) and len(binding) == 2 and isinstance(binding[0], str), "Each state binding must be `(name value)`."
        name = binding[0]
        value = evaluate(binding[1], env)
        if isinstance(value, ClockTemplate):
            spec = StoreFieldSpec(id=name, kind="clock", initial=value.initial, title=value.title, maximum=value.maximum, persist=value.persist)
            module.store_specs[name] = spec
            module.clocks_by_id[name] = ProgressClockSpec(id=name, title=value.title, segments=value.maximum)
        else:
            assert isinstance(value, (bool, int, str)), f"Unsupported state value for {name}: {value!r}"
            module.store_specs[name] = StoreFieldSpec(id=name, kind="value", initial=value)


def _eval_meta(form: Any, env: Environment) -> EncounterMeta:
    kwargs = _keyword_args(form[1:])
    key = _keyword_string(_eval_keyword_values(kwargs, env, keys={":key"}), ":key", allow_symbol=True)
    title = _keyword_string(_eval_keyword_values(kwargs, env, keys={":title"}), ":title")
    description = _keyword_string(_eval_keyword_values(kwargs, env, keys={":desc"}), ":desc", default="")
    return EncounterMeta(key=key, title=title, description=description)


def _eval_reacts(form: Any, env: Environment, module: ModuleState) -> None:
    for index, item in enumerate(form[1:]):
        assert _is_call(item, "react"), "reacts only supports react forms."
        kwargs = _keyword_args(item[1:])
        condition = kwargs[":when"]
        effects = _eval_effect_list(kwargs[":then"], env)
        key_values = _eval_keyword_values(kwargs, env, keys={":key"})
        key = _keyword_string(key_values, ":key", allow_symbol=True, default=f"react[{index}]")
        module.react_rules.append(ReactRule(condition_expr=condition, effects=effects, source=key))


def _render_scene(program: CompiledEncounterProgram, scene: SceneTemplate, *, scene_path: tuple[str, ...]) -> RenderedScene:
    scene_key = scene.key or _hash_key(scene.title, scene_path, "scene")
    path = (*scene_path, scene_key)
    rendered_actions: list[RenderedAction] = []
    for source_index, action in enumerate(scene.actions):
        rendered_actions.append(_render_action(program, action, scene_path=path, source_index=source_index))
    rendered_children = tuple(_render_scene(program, child, scene_path=path) for child in scene.children)
    root = LocationNode(
        id=scene_key,
        title=scene.title,
        description=scene.description,
        actions=tuple(item.action for item in rendered_actions),
        children=tuple(child.root for child in rendered_children),
    )
    return RenderedScene(
        scene_id=scene_key,
        root=root,
        shown_clock_ids=scene.shown_clock_ids,
        actions=tuple(rendered_actions),
        children=rendered_children,
    )


def _render_action(program: CompiledEncounterProgram, action: ActionTemplate, *, scene_path: tuple[str, ...], source_index: int) -> RenderedAction:
    action_key = action.key or _hash_key(action.title, scene_path, "action")
    action_id = f"{program.id}:{'/'.join(scene_path)}:{source_index}:{action_key}"
    action_def = ActionDef(
        id=action_id,
        title=action.title,
        description=action.description,
        screen=ScreenName.ENCOUNTER,
        inputs=action.inputs,
        effects=action.before if action.check is not None else (*action.before, *action.effects),
        check=_build_check(action.check) if action.check is not None else None,
    )
    handle = ActionHandle(action_id=action_id, scene_path=scene_path, slot_index=source_index, action_key=action_key)
    return RenderedAction(handle=handle, action=replace(action_def, id=action_id))


def _build_check(check: CheckTemplate) -> CheckDef:
    assert check.risk in RISK_BY_NAME, f"Unknown risk: {check.risk}"
    return CheckDef(
        suits=tuple(SUIT_BY_NAME[item] for item in check.suits),
        risk=RISK_BY_NAME[check.risk],
        success=OutcomeDef(text=check.success.text, effects=check.success.effects),
        cost=OutcomeDef(text=check.cost.text, effects=check.cost.effects),
        fail=OutcomeDef(text=check.fail.text, effects=check.fail.effects),
    )


def _eval_effect_list(expr: Any, env: Environment) -> tuple[Effect, ...]:
    if expr is None:
        return ()
    value = evaluate(expr, env)
    if value is None:
        return ()
    if isinstance(value, Effect):
        return (value,)
    assert isinstance(value, list), f"Expected effect list, got: {value!r}"
    return tuple(item for item in value if item is not None)


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


def _host_values(*, store_specs: dict[str, StoreFieldSpec], store: dict[str, int | bool | str]) -> dict[str, Any]:
    return {
        "clock": _builtin_clock,
        "meta": lambda *args: ModuleDeclaration(kind="meta", value=args),
        "state": lambda *args: ModuleDeclaration(kind="state", value=args),
        "reacts": lambda *args: ModuleDeclaration(kind="reacts", value=args),
        "react": lambda *args: list(args),
        "on-success": lambda *args: ModuleDeclaration(kind="on-success", value=args),
        "on-fail": lambda *args: ModuleDeclaration(kind="on-fail", value=args),
        "scene": lambda *args: _builtin_scene(args),
        "action": lambda *args: _builtin_action(args),
        "check": lambda *args: _builtin_check(args),
        "outcome": lambda text, effects=None: OutcomeTemplate(text=str(text), effects=_as_effect_tuple(effects)),
        "effect": lambda *args: _builtin_effect(args),
        "resource": _builtin_resource_input,
        "item": _builtin_item_input,
        "card": _builtin_card_input,
        "clock-value": lambda value: _clock_metric(value, "value"),
        "clock-full": lambda value: _clock_metric(value, "maximum"),
        "clock-half": lambda value: (_clock_metric(value, "maximum") + 1) // 2,
    }


def _builtin_clock(*args: Any) -> ClockTemplate:
    kwargs = _keyword_args(list(args))
    title = _keyword_string(kwargs, ":title")
    initial = int(_unwrap(kwargs[":initial"]))
    maximum = int(_unwrap(kwargs[":max"]))
    persist = _keyword_string(kwargs, ":persist", allow_symbol=True, default="encounter")
    assert 0 <= initial <= maximum, "Clock initial must be within range."
    return ClockTemplate(title=title, initial=initial, maximum=maximum, persist=persist)


def _builtin_scene(args: tuple[Any, ...]) -> SceneTemplate:
    kwargs = _keyword_args(list(args))
    return SceneTemplate(
        key=_maybe_symbol(kwargs.get(":key")),
        title=_keyword_string(kwargs, ":title"),
        description=_keyword_string(kwargs, ":desc", default=""),
        shown_clock_ids=tuple(_clock_id(item) for item in _as_list(kwargs.get(":show-clocks")) if item is not None),
        actions=tuple(item for item in _as_list(kwargs.get(":actions")) if item is not None),
        children=tuple(item for item in _as_list(kwargs.get(":children")) if item is not None),
    )


def _builtin_action(args: tuple[Any, ...]) -> ActionTemplate:
    kwargs = _keyword_args(list(args))
    check = kwargs.get(":check")
    effects = _as_effect_tuple(kwargs.get(":effects"))
    before = _as_effect_tuple(kwargs.get(":before"))
    assert check is None or not effects, "Action cannot have both :check and :effects."
    return ActionTemplate(
        key=_maybe_symbol(kwargs.get(":key")),
        title=_keyword_string(kwargs, ":title"),
        description=_keyword_string(kwargs, ":desc", default=""),
        inputs=tuple(item for item in _as_list(kwargs.get(":inputs")) if item is not None),
        before=before,
        effects=effects,
        check=check,
    )


def _builtin_check(args: tuple[Any, ...]) -> CheckTemplate:
    kwargs = _keyword_args(list(args))
    suits = tuple(_unwrap(item) for item in _as_list(kwargs.get(":suits")))
    risk = _keyword_string(kwargs, ":risk", allow_symbol=True)
    success = kwargs.get(":ok")
    cost = kwargs.get(":partial")
    fail = kwargs.get(":fail")
    assert isinstance(success, OutcomeTemplate) and isinstance(cost, OutcomeTemplate) and isinstance(fail, OutcomeTemplate), "Check outcomes must be outcome forms."
    return CheckTemplate(suits=suits, risk=risk, success=success, cost=cost, fail=fail)


def _builtin_effect(args: tuple[Any, ...]) -> Effect:
    assert args, "`effect` requires a kind."
    kind = _unwrap(args[0])
    if kind == "clock+":
        target = _clock_id(args[1])
        return Effect(kind="advance_encounter_clock", value=f"{target}:{int(_unwrap(args[2]))}")
    if kind == "clock-":
        target = _clock_id(args[1])
        return Effect(kind="damage_encounter_clock", value=f"{target}:{int(_unwrap(args[2]))}")
    if kind == "set":
        target = _binding_name(args[1])
        return Effect(kind="set_encounter_store", value=f"{target}:{_effect_token(args[2])}")
    if kind == "health":
        return Effect(kind="change_health", value=int(_unwrap(args[1])))
    if kind == "stress":
        return Effect(kind="change_stress", value=int(_unwrap(args[1])))
    if kind == "resource":
        key = _unwrap(args[1])
        return Effect(kind="change_resource", value=f"{key}:{int(_unwrap(args[2]))}")
    if kind == "finish":
        return Effect(kind="finish_encounter", value=str(_unwrap(args[1])))
    if kind == "reset-hand":
        return Effect(kind="reset_hand", value=True)
    raise EncounterSchemaError(f"Unsupported encounter effect kind: {kind}")


def _builtin_resource_input(key: Any, amount: Any, label: Any | None = None) -> InputRequirement:
    key_value = str(_unwrap(key))
    return InputRequirement(kind="resource", key=key_value, amount=int(_unwrap(amount)), label=(key_value if label is None else str(_unwrap(label))), consume=True)


def _builtin_item_input(key: Any, amount: Any = 1, label: Any | None = None, consume: Any = True) -> InputRequirement:
    key_value = str(_unwrap(key))
    return InputRequirement(kind="item", key=key_value, amount=int(_unwrap(amount)), label=(key_value if label is None else str(_unwrap(label))), consume=bool(_unwrap(consume)))


def _builtin_card_input(key: Any, label: Any | None = None) -> InputRequirement:
    key_value = str(_unwrap(key))
    return InputRequirement(kind="card", key=key_value, amount=1, label=("负面牌" if key_value == "negative" else ("手牌" if label is None else str(_unwrap(label)))), consume=True)


def _clock_metric(value: Any, field: str) -> int:
    binding = _binding(value)
    assert binding.spec.kind == "clock", f"Clock operation requires a clock binding: {binding.name}"
    if field == "value":
        return int(binding.value)
    assert binding.spec.maximum is not None
    return binding.spec.maximum


def _binding(value: Any) -> StateBindingValue:
    if isinstance(value, StateBindingValue):
        return value
    raise EncounterSchemeError(f"Expected encounter state binding, got: {value!r}")


def _binding_name(value: Any) -> str:
    if isinstance(value, StateBindingValue):
        return value.name
    if isinstance(value, str):
        return value
    raise EncounterSchemeError(f"Expected encounter state binding name, got: {value!r}")


def _clock_id(value: Any) -> str:
    binding = _binding(value)
    assert binding.spec.kind == "clock", f"Expected clock binding, got: {binding.name}"
    return binding.name


def _effect_token(value: Any) -> str:
    raw = _unwrap(value)
    if raw is None:
        return "nil"
    if raw is True:
        return "true"
    if raw is False:
        return "false"
    return str(raw)


def _unwrap(value: Any) -> Any:
    return value.value if isinstance(value, StateBindingValue) else value


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    assert isinstance(value, list), f"Expected list value, got: {value!r}"
    return value


def _as_effect_tuple(value: Any) -> tuple[Effect, ...]:
    if value is None:
        return ()
    if isinstance(value, Effect):
        return (value,)
    items = _as_list(value)
    return tuple(item for item in items if item is not None)


def _keyword_args(items: list[Any]) -> dict[str, Any]:
    assert len(items) % 2 == 0, "Keyword arguments must come in pairs."
    result: dict[str, Any] = {}
    for index in range(0, len(items), 2):
        key = items[index]
        assert isinstance(key, str) and key.startswith(":"), f"Expected keyword argument, got: {key!r}"
        result[key] = items[index + 1]
    return result


def _keyword_string(kwargs: dict[str, Any], key: str, *, allow_symbol: bool = False, default: str | None = None) -> str:
    if key not in kwargs:
        assert default is not None, f"Missing required field: {key}"
        return default
    value = _unwrap(kwargs[key])
    assert isinstance(value, str), f"Field {key} must be a string/symbol, got: {value!r}"
    if not allow_symbol:
        return value
    return value


def _eval_keyword_values(kwargs: dict[str, Any], env: Environment, *, keys: set[str]) -> dict[str, Any]:
    evaluated = dict(kwargs)
    for key in keys:
        if key in evaluated:
            evaluated[key] = evaluate(evaluated[key], env)
    return evaluated


def _maybe_symbol(value: Any | None) -> str | None:
    if value is None:
        return None
    unwrapped = _unwrap(value)
    assert isinstance(unwrapped, str), f"Expected symbol/string key, got: {unwrapped!r}"
    return unwrapped


def _flatten_scene(
    rendered: RenderedScene,
    *,
    parent_id: str | None,
    locations_by_id: dict[str, LocationNode],
    parent_by_id: dict[str, str | None],
    actions_by_id: dict[str, ActionDef],
    actions_by_location: dict[str, tuple[str, ...]],
    action_handles_by_id: dict[str, ActionHandle],
    shown_clock_ids_by_scene: dict[str, tuple[str, ...]],
) -> None:
    root = rendered.root
    assert root.id not in locations_by_id, f"Duplicate rendered scene id: {root.id}"
    locations_by_id[root.id] = root
    parent_by_id[root.id] = parent_id
    actions_by_location[root.id] = tuple(item.action.id for item in rendered.actions)
    shown_clock_ids_by_scene[root.id] = rendered.shown_clock_ids
    for item in rendered.actions:
        assert item.action.id not in actions_by_id, f"Duplicate rendered action id: {item.action.id}"
        actions_by_id[item.action.id] = item.action
        action_handles_by_id[item.action.id] = item.handle
    for child in rendered.children:
        _flatten_scene(
            child,
            parent_id=root.id,
            locations_by_id=locations_by_id,
            parent_by_id=parent_by_id,
            actions_by_id=actions_by_id,
            actions_by_location=actions_by_location,
            action_handles_by_id=action_handles_by_id,
            shown_clock_ids_by_scene=shown_clock_ids_by_scene,
        )


def _hash_key(title: str, scene_path: tuple[str, ...], kind: str) -> str:
    return f"{kind}:{hashlib.sha1((title + '|' + '/'.join(scene_path)).encode('utf-8')).hexdigest()[:10]}"


def _is_call(node: Any, name: str) -> bool:
    return isinstance(node, list) and bool(node) and node[0] == name
