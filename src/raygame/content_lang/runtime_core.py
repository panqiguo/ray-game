from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

from raygame.encounters.defs import (
    ActionHandle,
    ActionTemplate,
    CheckTemplate,
    ClockTemplate,
    EncounterMeta,
    EncounterSchemaError,
    EncounterSchemeError,
    OutcomeTemplate,
    ReactTemplate,
    RenderedAction,
    RenderedScene,
    SceneTemplate,
    StateBindingValue,
    StoreFieldSpec,
)
from raygame.encounters.lispy import Environment, SpecialFormProcedure, evaluate
from raygame.labels import lookup_input_label
from raygame.model.defs import ActionDef, CheckDef, Condition, Effect, InputRequirement, LocationNode, OutcomeDef
from raygame.model.enums import Risk, ScreenName, Suit


RISK_BY_NAME = {"low": Risk.LOW, "mid": Risk.MID, "high": Risk.HIGH}
SUIT_BY_NAME = {
    "reason": Suit.REASON,
    "force": Suit.FORCE,
    "empathy": Suit.EMPATHY,
    "instinct": Suit.INSTINCT,
}


def build_check(check: CheckTemplate) -> CheckDef:
    assert check.risk in RISK_BY_NAME, f"Unknown risk: {check.risk}"
    return CheckDef(
        suits=tuple(SUIT_BY_NAME[item] for item in check.suits),
        risk=RISK_BY_NAME[check.risk],
        success=OutcomeDef(text=check.success.text, effects=check.success.effects),
        cost=OutcomeDef(text=check.cost.text, effects=check.cost.effects),
        fail=OutcomeDef(text=check.fail.text, effects=check.fail.effects),
    )


def validate_template(value: Any) -> None:
    if isinstance(value, ActionTemplate):
        validate_action_template(value)
        return
    if isinstance(value, ReactTemplate):
        validate_react_template(value)
        return
    if isinstance(value, SceneTemplate):
        validate_scene_template(value)
        return


def validate_scene_template(scene: SceneTemplate) -> None:
    for condition in scene.conditions:
        assert isinstance(condition, Condition), f"scene contains non-condition value: {condition!r}"
    for action in scene.actions:
        validate_action_template(action)
    for child in scene.children:
        validate_scene_template(child)


def validate_action_template(action: ActionTemplate) -> None:
    for condition in action.conditions:
        assert isinstance(condition, Condition), f"action contains non-condition value: {condition!r}"
    for item in action.inputs:
        assert isinstance(item, InputRequirement), f"action contains non-input value: {item!r}"
    for effect in action.before:
        assert isinstance(effect, Effect), f"action contains non-effect before value: {effect!r}"
    for effect in action.effects:
        assert isinstance(effect, Effect), f"action contains non-effect value: {effect!r}"
    if action.check is not None:
        build_check(action.check)


def validate_react_template(react: ReactTemplate) -> None:
    for effect in react.effects:
        assert isinstance(effect, Effect), f"react contains non-effect value: {effect!r}"


def validate_schema_forms(
    expr: Any,
    env: Environment,
    *,
    context: str,
    skip_heads: frozenset[str] = frozenset(),
    allow_nil_templates: bool = False,
) -> None:
    if not isinstance(expr, list) or not expr:
        return
    head = expr[0]
    head_name = head if isinstance(head, str) else None
    try:
        if head_name in ({"quote", "lambda"} | skip_heads):
            return
        if head_name in {"scene", "node"}:
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, SceneTemplate), f"node form did not produce scene template: {value!r}"
            validate_scene_template(value)
        elif head_name == "action":
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, ActionTemplate), f"action form did not produce action template: {value!r}"
            validate_action_template(value)
        elif head_name == "check":
            value = evaluate(expr, env)
            assert isinstance(value, CheckTemplate), f"check form did not produce check template: {value!r}"
            build_check(value)
        elif head_name == "react":
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, ReactTemplate), f"react form did not produce react template: {value!r}"
            validate_react_template(value)
        elif head_name == "effect":
            value = evaluate(expr, env)
            assert isinstance(value, Effect), f"effect form did not produce effect: {value!r}"
    except EncounterSchemeError as exc:
        raise EncounterSchemeError(f"{context}: {exc}") from exc
    except EncounterSchemaError as exc:
        raise EncounterSchemaError(f"{context}: {exc}") from exc
    except Exception as exc:
        raise EncounterSchemaError(f"{context}: {exc}") from exc
    for index, item in enumerate(expr[1:]):
        validate_schema_forms(
            item,
            env,
            context=f"{context}[{index + 1}]",
            skip_heads=skip_heads,
            allow_nil_templates=allow_nil_templates,
        )


def render_scene(program: Any, scene: SceneTemplate, *, scene_path: tuple[str, ...], source_index: int = 0) -> RenderedScene:
    scene_key = _hash_key(scene.title, (*scene_path, f"slot:{source_index}"), "scene")
    path = (*scene_path, scene_key)
    rendered_actions: list[RenderedAction] = []
    for source_index, action in enumerate(scene.actions):
        rendered_actions.append(_render_action(program, action, scene_path=path, source_index=source_index))
    rendered_children = tuple(render_scene(program, child, scene_path=path, source_index=index) for index, child in enumerate(scene.children))
    root = LocationNode(
        id=scene_key,
        title=scene.title,
        description=scene.description,
        position=scene.position,
        show_clock_ids=scene.shown_clock_ids,
        actions=tuple(item.action for item in rendered_actions),
        children=tuple(child.root for child in rendered_children),
        conditions=tuple(scene.conditions),
    )
    return RenderedScene(
        scene_id=scene_key,
        root=root,
        shown_clock_ids=scene.shown_clock_ids,
        actions=tuple(rendered_actions),
        children=rendered_children,
    )


def flatten_scene(
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
        flatten_scene(
            child,
            parent_id=root.id,
            locations_by_id=locations_by_id,
            parent_by_id=parent_by_id,
            actions_by_id=actions_by_id,
            actions_by_location=actions_by_location,
            action_handles_by_id=action_handles_by_id,
            shown_clock_ids_by_scene=shown_clock_ids_by_scene,
        )


def host_values(*, store_specs: dict[str, StoreFieldSpec], store: dict[str, int | bool | str]) -> dict[str, Any]:
    return {
        "clock": builtin_clock,
        "clocks": lambda *args: [item for item in args if item is not None],
        "meta": lambda *args: builtin_meta(args),
        "condition": builtin_condition,
        "has-item": builtin_has_item_condition,
        "field-at-least": builtin_field_at_least_condition,
        "field-truthy": builtin_field_truthy_condition,
        "reacts": lambda *args: [item for item in args if item is not None],
        "react": SpecialFormProcedure(builtin_react),
        "node": lambda *args: builtin_scene(args),
        "scene": lambda *args: builtin_scene(args),
        "action": lambda *args: builtin_action(args),
        "check": lambda *args: builtin_check(args),
        "outcome": lambda text, effects=None: OutcomeTemplate(text=str(text), effects=as_effect_tuple(effects)),
        "effect": lambda *args: builtin_effect(args),
        "item": builtin_item_input,
        "card": builtin_card_input,
        "clock-value": lambda value: clock_metric(value, "value"),
        "clock-max": lambda value: clock_metric(value, "maximum"),
    }


def builtin_meta(args: tuple[Any, ...]) -> EncounterMeta:
    kwargs = keyword_args(list(args), allowed={":key", ":title", ":desc"})
    key = keyword_string(kwargs, ":key", allow_symbol=True)
    title = keyword_string(kwargs, ":title")
    description = keyword_string(kwargs, ":desc", default="")
    return EncounterMeta(key=key, title=title, description=description)


def builtin_clock(*args: Any) -> ClockTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":desc", ":initial", ":max"})
    title = keyword_string(kwargs, ":title")
    description = keyword_string(kwargs, ":desc", default="")
    initial = int(unwrap(kwargs[":initial"]))
    maximum = int(unwrap(kwargs[":max"]))
    assert 0 <= initial <= maximum, "Clock initial must be within range."
    return ClockTemplate(title=title, description=description, initial=initial, maximum=maximum)


def builtin_scene(args: tuple[Any, ...]) -> SceneTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":desc", ":position", ":show-clocks", ":conditions", ":actions", ":children"})
    return SceneTemplate(
        title=keyword_string(kwargs, ":title"),
        description=keyword_string(kwargs, ":desc", default=""),
        position=position_tuple(kwargs.get(":position")),
        shown_clock_ids=tuple(clock_id(item) for item in as_list(kwargs.get(":show-clocks")) if item is not None),
        conditions=tuple(item for item in as_list(kwargs.get(":conditions")) if item is not None),
        actions=tuple(item for item in as_list(kwargs.get(":actions")) if item is not None),
        children=tuple(item for item in as_list(kwargs.get(":children")) if item is not None),
    )


def builtin_action(args: tuple[Any, ...]) -> ActionTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":desc", ":position", ":conditions", ":inputs", ":before", ":effects", ":check"})
    check = kwargs.get(":check")
    effects = as_effect_tuple(kwargs.get(":effects"))
    before = as_effect_tuple(kwargs.get(":before"))
    assert check is None or not effects, "Action cannot have both :check and :effects."
    return ActionTemplate(
        title=keyword_string(kwargs, ":title"),
        description=keyword_string(kwargs, ":desc", default=""),
        position=position_tuple(kwargs.get(":position")),
        inputs=tuple(item for item in as_list(kwargs.get(":inputs")) if item is not None),
        before=before,
        effects=effects,
        conditions=tuple(item for item in as_list(kwargs.get(":conditions")) if item is not None),
        check=check,
    )


def builtin_check(args: tuple[Any, ...]) -> CheckTemplate:
    kwargs = keyword_args(list(args), allowed={":suits", ":risk", ":ok", ":partial", ":fail"})
    suits = tuple(unwrap(item) for item in as_list(kwargs.get(":suits")))
    risk = keyword_string(kwargs, ":risk", allow_symbol=True)
    success = kwargs.get(":ok")
    cost = kwargs.get(":partial")
    fail = kwargs.get(":fail")
    assert isinstance(success, OutcomeTemplate) and isinstance(cost, OutcomeTemplate) and isinstance(fail, OutcomeTemplate), "Check outcomes must be outcome forms."
    return CheckTemplate(suits=suits, risk=risk, success=success, cost=cost, fail=fail)


def builtin_condition(kind: Any, value: Any | None = None, label: Any | None = None) -> Condition:
    return Condition(kind=str(unwrap(kind)), value=condition_value(value), label=("" if label is None else str(unwrap(label))))


def builtin_has_item_condition(key: Any, amount: Any = 1, label: Any | None = None) -> Condition:
    key_value = str(unwrap(key))
    amount_value = int(unwrap(amount))
    payload = f"{key_value}:{amount_value}"
    return Condition(kind="has_item", value=payload, label=("" if label is None else str(unwrap(label))))


def builtin_field_at_least_condition(key: Any, amount: Any, label: Any | None = None) -> Condition:
    key_value = str(unwrap(key))
    amount_value = int(unwrap(amount))
    return Condition(kind="field_at_least", value=f"{key_value}:{amount_value}", label=("" if label is None else str(unwrap(label))))


def builtin_field_truthy_condition(key: Any, label: Any | None = None) -> Condition:
    key_value = str(unwrap(key))
    return Condition(kind="field_truthy", value=key_value, label=("" if label is None else str(unwrap(label))))


def builtin_react(args: list[Any], env: Environment) -> ReactTemplate:
    kwargs = keyword_args(list(args), allowed={":when", ":then"})
    condition = freeze_react_expr(kwargs[":when"], env)
    effects = eval_effect_list(kwargs[":then"], env)
    return ReactTemplate(condition_expr=condition, effects=effects)


def freeze_react_expr(expr: Any, env: Environment) -> Any:
    if isinstance(expr, list):
        if not expr:
            return []
        if expr[0] == "quote":
            return expr
        return [freeze_react_expr(item, env) for item in expr]
    if isinstance(expr, str):
        if expr.startswith(":"):
            return expr
        try:
            value = env.lookup(expr)
        except EncounterSchemeError:
            return expr
        if isinstance(value, StateBindingValue):
            return value.name
        if isinstance(value, (bool, int)):
            return value
        if isinstance(value, str):
            return ["quote", value]
    return expr


def builtin_effect(args: tuple[Any, ...]) -> Effect:
    assert args, "`effect` requires a kind."
    kind = unwrap(args[0])
    kind_aliases = {
        "start-dialogue": "start_dialogue",
        "start_dialogue": "start_dialogue",
        "start-quick-dialogue": "start_quick_dialogue",
        "start_quick_dialogue": "start_quick_dialogue",
    }
    if kind in kind_aliases:
        return Effect(kind=kind_aliases[kind], value=str(unwrap(args[1])))
    if kind in {"clock+", "clock-"}:
        target = clock_id(args[1])
        delta = int(unwrap(args[2]))
        if kind == "clock-":
            delta = -delta
        return Effect(kind="shift_clock", value=f"{target}:{delta}")
    if kind == "set":
        target = binding_name(args[1])
        return Effect(kind="set_field", value=f"{target}:{effect_token(args[2])}")
    if kind == "add":
        target = binding_name(args[1])
        return Effect(kind="add_field", value=f"{target}:{int(unwrap(args[2]))}")
    if kind == "health":
        return Effect(kind="add_field", value=f"health:{int(unwrap(args[1]))}")
    if kind == "stress":
        return Effect(kind="add_field", value=f"stress:{int(unwrap(args[1]))}")
    if kind == "start-encounter":
        return Effect(kind="start_encounter", value=str(unwrap(args[1])))
    if kind == "end-encounter":
        return Effect(kind="end_encounter", value=str(unwrap(args[1])))
    if kind == "advance-day":
        return Effect(kind="advance_day", value=True)
    if kind == "end-game":
        assert len(args) == 1, "`end-game` does not take parameters."
        return Effect(kind="end_game", value=True)
    if kind == "reset-hand":
        return Effect(kind="reset_hand", value=True)
    raise EncounterSchemaError(f"Unsupported encounter effect kind: {kind}")


def builtin_item_input(key: Any, amount: Any = 1, label: Any | None = None) -> InputRequirement:
    key_value = str(unwrap(key))
    resolved_label = lookup_input_label(key_value) if label is None else str(unwrap(label))
    return InputRequirement(kind="item", key=key_value, amount=int(unwrap(amount)), label=resolved_label, consume=True)


def builtin_card_input(key: Any, label: Any | None = None) -> InputRequirement:
    key_value = str(unwrap(key))
    return InputRequirement(kind="card", key=key_value, amount=1, label=("负面牌" if key_value == "negative" else ("手牌" if label is None else str(unwrap(label)))), consume=True)


def eval_effect_list(expr: Any, env: Environment) -> tuple[Effect, ...]:
    if expr is None:
        return ()
    value = evaluate(expr, env)
    if value is None:
        return ()
    if isinstance(value, Effect):
        return (value,)
    assert isinstance(value, list), f"Expected effect list, got: {value!r}"
    return tuple(item for item in value if item is not None)


def clock_metric(value: Any, field: str) -> int:
    bound = binding(value)
    assert bound.spec.kind == "clock", f"Clock operation requires a clock binding: {bound.name}"
    if field == "value":
        return int(bound.value)
    assert bound.spec.maximum is not None
    return bound.spec.maximum


def binding(value: Any) -> StateBindingValue:
    if isinstance(value, StateBindingValue):
        return value
    raise EncounterSchemeError(f"Expected encounter state binding, got: {value!r}")


def binding_name(value: Any) -> str:
    if isinstance(value, StateBindingValue):
        return value.name
    if isinstance(value, str):
        return value
    raise EncounterSchemeError(f"Expected encounter state binding name, got: {value!r}")


def clock_id(value: Any) -> str:
    bound = binding(value)
    assert bound.spec.kind == "clock", f"Expected clock binding, got: {bound.name}"
    return bound.name


def effect_token(value: Any) -> str:
    raw = unwrap(value)
    if raw is None:
        return "nil"
    if raw is True:
        return "true"
    if raw is False:
        return "false"
    return str(raw)


def condition_value(value: Any | None) -> Any:
    if value is None:
        return None
    raw = unwrap(value)
    if isinstance(raw, list):
        return tuple(raw)
    return raw


def unwrap(value: Any) -> Any:
    return value.value if isinstance(value, StateBindingValue) else value


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    assert isinstance(value, list), f"Expected list value, got: {value!r}"
    return value


def as_effect_tuple(value: Any) -> tuple[Effect, ...]:
    if value is None:
        return ()
    if isinstance(value, Effect):
        return (value,)
    items = as_list(value)
    return tuple(item for item in items if item is not None)


def position_tuple(value: Any) -> tuple[int, int] | None:
    if value is None:
        return None
    raw = as_list(value)
    assert len(raw) == 2, f"Position must be a list of two numbers, got: {raw!r}"
    return (int(unwrap(raw[0])), int(unwrap(raw[1])))


def keyword_args(items: list[Any], *, allowed: set[str]) -> dict[str, Any]:
    assert len(items) % 2 == 0, "Keyword arguments must come in pairs."
    result: dict[str, Any] = {}
    for index in range(0, len(items), 2):
        key = items[index]
        assert isinstance(key, str) and key.startswith(":"), f"Expected keyword argument, got: {key!r}"
        assert key in allowed, f"Unsupported keyword: {key}"
        assert key not in result, f"Duplicate keyword: {key}"
        result[key] = items[index + 1]
    return result


def keyword_string(kwargs: dict[str, Any], key: str, *, allow_symbol: bool = False, default: str | None = None) -> str:
    if key not in kwargs:
        assert default is not None, f"Missing required field: {key}"
        return default
    value = unwrap(kwargs[key])
    assert isinstance(value, str), f"Field {key} must be a string/symbol, got: {value!r}"
    if not allow_symbol:
        return value
    return value


def _render_action(program: Any, action: ActionTemplate, *, scene_path: tuple[str, ...], source_index: int) -> RenderedAction:
    action_key = _hash_key(action.title, scene_path, "action")
    action_id = f"{program.id}:{'/'.join(scene_path)}:{source_index}:{action_key}"
    action_def = ActionDef(
        id=action_id,
        title=action.title,
        description=action.description,
        screen=getattr(program, "screen", ScreenName.ENCOUNTER),
        position=action.position,
        inputs=action.inputs,
        effects=action.before if action.check is not None else (*action.before, *action.effects),
        conditions=tuple(action.conditions),
        check=build_check(action.check) if action.check is not None else None,
    )
    handle = ActionHandle(action_id=action_id, scene_path=scene_path, slot_index=source_index, action_key=action_key)
    return RenderedAction(handle=handle, action=replace(action_def, id=action_id))


def _hash_key(title: str, scene_path: tuple[str, ...], kind: str) -> str:
    return f"{kind}:{hashlib.sha1((title + '|' + '/'.join(scene_path)).encode('utf-8')).hexdigest()[:10]}"
