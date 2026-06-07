from __future__ import annotations

from dataclasses import replace
from typing import Any

from sincity.encounters.defs import (
    ActionHandle,
    ActionTemplate,
    CheckTemplate,
    ClockTemplate,
    EncounterMeta,
    EncounterSchemaError,
    EncounterSchemeError,
    ObjectValue,
    OutcomeTemplate,
    ReactionFace,
    ReactionTable,
    ReactTemplate,
    RenderedAction,
    RenderedClock,
    RenderedLocation,
    RuntimeClockValue,
    LocationTemplate,
    StateBindingValue,
    StoreFieldSpec,
    TaskStepTemplate,
    TaskTemplate,
)
from sincity.encounters.lispy import Environment, Procedure, SpecialFormProcedure, StringAtom, evaluate, format_sexp, format_source_ref, source_ref, truthy
from sincity.labels import lookup_input_label
from sincity.model.defs import (
    ActionDef,
    ActionRevealDef,
    AddFieldPayload,
    CheckDef,
    CheckFactorDef,
    Condition,
    DynamicValue,
    Effect,
    FieldRef,
    InputRequirement,
    LocationDef,
    OutcomeDef,
    SetFieldPayload,
    ShiftClockPayload,
)
from sincity.model.enums import Risk, ScreenName, Suit


RISK_BY_NAME = {"low": Risk.LOW, "mid": Risk.MID, "high": Risk.HIGH}
SUIT_BY_NAME = {
    "force": Suit.FORCE,
    "violence": Suit.FORCE,
    "charm": Suit.CHARM,
    "charisma": Suit.CHARM,
    "knowledge": Suit.KNOWLEDGE,
    "reason": Suit.KNOWLEDGE,
    "sense": Suit.SENSE,
    "empathy": Suit.SENSE,
    "instinct": Suit.SENSE,
}


def build_check(check: CheckTemplate) -> CheckDef:
    assert check.risk in RISK_BY_NAME, f"Unknown risk: {check.risk}"
    suit = SUIT_BY_NAME[check.suit]
    return CheckDef(
        suit=suit,
        risk=RISK_BY_NAME[check.risk],
        success=OutcomeDef(text=check.success.text, effects=check.success.effects),
        cost=OutcomeDef(text=check.cost.text, effects=check.cost.effects),
        fail=OutcomeDef(text=check.fail.text, effects=check.fail.effects),
        factors=check.factors,
    )


def validate_template(value: Any) -> None:
    if isinstance(value, ActionTemplate):
        validate_action_template(value)
        return
    if isinstance(value, ReactTemplate):
        validate_react_template(value)
        return
    if isinstance(value, LocationTemplate):
        validate_location_template(value)
        return


def validate_location_template(location: LocationTemplate) -> None:
    assert location.title, f"location :title must not be empty; got: {location.title!r}"
    assert "/" not in location.title, f"location :title must not contain '/': {location.title}"
    for condition in location.conditions:
        assert isinstance(condition, Condition), f"location contains non-condition value: {condition!r}"
    for action in location.actions:
        validate_action_template(action)
    for child in location.children:
        validate_location_template(child)


_MODAL_EFFECTS = frozenset({"start_dialogue", "start_quick_dialogue", "start_encounter"})


def validate_action_template(action: ActionTemplate) -> None:
    assert action.title, f"action :title must not be empty; got: {action.title!r}"
    assert "/" not in action.title, f"action :title must not contain '/': {action.title}"
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
    if action.reveal is not None:
        assert action.check is None, "reveal action cannot have :check"
        assert not action.inputs, "reveal action cannot have :inputs"
        assert isinstance(action.reveal, ActionRevealDef), f"reveal must be an ActionRevealDef, got: {action.reveal!r}"
        for effect in action.before:
            assert effect.kind not in _MODAL_EFFECTS, f"reveal action cannot have modal effect: {effect.kind}"
        for effect in action.effects:
            assert effect.kind not in _MODAL_EFFECTS, f"reveal action cannot have modal effect: {effect.kind}"
    if action.button_label:
        assert action.check is None, "custom :button label is only allowed on instant/reveal actions"
        assert action.button_label.strip(), ":button must not be empty"


def validate_react_template(react: ReactTemplate) -> None:
    assert isinstance(react.condition, Procedure) and not react.condition.params, f"react condition must be a zero-argument procedure: {react.condition!r}"
    for effect in react.effects:
        assert isinstance(effect, Effect), f"react contains non-effect value: {effect!r}"


def validate_reaction_face(face: ReactionFace) -> None:
    assert 1 <= face.value <= 6, f"reaction face value must be 1..6, got: {face.value}"
    assert face.title, "reaction face title must not be empty"
    for effect in face.effects:
        assert isinstance(effect, Effect), f"reaction face contains non-effect value: {effect!r}"


def validate_reaction_table(table: ReactionTable) -> None:
    assert table.faces, "reaction table must contain at least one face"
    seen: set[int] = set()
    for face in table.faces:
        validate_reaction_face(face)
        assert face.value not in seen, f"duplicate reaction face: {face.value}"
        seen.add(face.value)


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
        if head_name == "location":
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, LocationTemplate), f"location form did not produce location template: {value!r}"
            validate_location_template(value)
        elif head_name == "action":
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, ActionTemplate), f"action form did not produce action template: {value!r}"
            validate_action_template(value)
        elif head_name == "reveal":
            value = evaluate(expr, env)
            assert isinstance(value, ActionRevealDef), f"reveal form did not produce ActionRevealDef: {value!r}"
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
        elif head_name == "reaction-table":
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, ReactionTable), f"reaction-table form did not produce reaction table: {value!r}"
            validate_reaction_table(value)
        elif head_name == "face":
            value = evaluate(expr, env)
            if allow_nil_templates and value is None:
                return
            assert isinstance(value, ReactionFace), f"face form did not produce reaction face: {value!r}"
            validate_reaction_face(value)
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


def validate_effect_target_symbols(expr: Any, env: Environment, *, context: str, local_symbols: frozenset[str] = frozenset()) -> None:
    try:
        _validate_effect_target_symbols(expr, env, local_symbols=local_symbols)
    except EncounterSchemeError as exc:
        raise EncounterSchemeError(f"{context}: {exc}") from exc


def _validate_effect_target_symbols(expr: Any, env: Environment, *, local_symbols: frozenset[str]) -> None:
    if not isinstance(expr, list) or not expr:
        return
    head = expr[0]
    if head == "quote":
        return
    if head == "lambda":
        assert len(expr) == 3, "`lambda` expects parameters and body."
        params = expr[1]
        assert isinstance(params, list) and all(isinstance(param, str) for param in params), "`lambda` parameters must be symbols."
        _validate_effect_target_symbols(expr[2], env, local_symbols=local_symbols | frozenset(params))
        return
    if head == "effect":
        _validate_effect_targets(expr, env, local_symbols=local_symbols)
    for item in expr:
        _validate_effect_target_symbols(item, env, local_symbols=local_symbols)


def _validate_effect_targets(expr: list[Any], env: Environment, *, local_symbols: frozenset[str]) -> None:
    if len(expr) < 2:
        return
    kind = _static_effect_kind(expr[1])
    if kind in {"set", "add"} and len(expr) >= 3:
        _validate_effect_target_expr(expr[2], env, local_symbols=local_symbols, require_clock=False)
    elif kind in {"clock+", "clock-"} and len(expr) >= 3:
        _validate_effect_target_expr(expr[2], env, local_symbols=local_symbols, require_clock=True)
    elif kind == "copy" and len(expr) >= 4:
        _validate_effect_target_expr(expr[2], env, local_symbols=local_symbols, require_clock=False)
        _validate_effect_target_expr(expr[3], env, local_symbols=local_symbols, require_clock=False)


def _static_effect_kind(expr: Any) -> str | None:
    if isinstance(expr, list) and len(expr) == 2 and expr[0] == "quote":
        raw = expr[1]
        return raw if isinstance(raw, str) else None
    if isinstance(expr, StringAtom):
        return expr.value
    return None


def _validate_effect_target_expr(expr: Any, env: Environment, *, local_symbols: frozenset[str], require_clock: bool) -> None:
    if isinstance(expr, list) and len(expr) == 2 and expr[0] == "quote":
        if require_clock:
            raise EncounterSchemeError("Clock effect targets must be clock bindings, not quoted keys.")
        return
    if isinstance(expr, StringAtom):
        return
    if not isinstance(expr, str):
        return
    if expr in local_symbols:
        return
    try:
        value = env.lookup(expr)
    except EncounterSchemeError as exc:
        raise EncounterSchemeError(
            f"Unknown effect target symbol `{expr}`. If `{expr}` is an inventory or dynamic world key, quote it as `'{expr}`."
        ) from exc
    if isinstance(value, StateBindingValue):
        if require_clock:
            if value.spec.kind != "clock":
                raise EncounterSchemeError(f"Effect target `{expr}` must be a clock binding.")
        return
    raise EncounterSchemeError(
        f"Effect target `{expr}` resolves to a non-state value. Use a state binding, a function parameter, or quote inventory/dynamic keys as `'{expr}`."
    )


def render_location(
    program: Any,
    location: LocationTemplate,
    *,
    location_path: tuple[str, ...] = (),
    mounted_locations: dict[str, tuple[LocationTemplate, ...]] | None = None,
    mounted_actions: dict[str, tuple[ActionTemplate, ...]] | None = None,
) -> RenderedLocation:
    assert location.title, "location :title must not be empty"
    assert "/" not in location.title, f"location :title must not contain '/': {location.title}"
    location_key = location.title
    location_id = "/".join(location_path + (location_key,))

    if mounted_locations or mounted_actions:
        extra_actions = tuple(mounted_actions.get(location_id, ())) if mounted_actions else ()
        extra_children = tuple(mounted_locations.get(location_id, ())) if mounted_locations else ()
        if extra_actions or extra_children:
            location = replace(location, actions=location.actions + extra_actions, children=location.children + extra_children)

    action_keys: set[str] = set()
    for action in location.actions:
        assert action.title, "action :title must not be empty"
        assert "/" not in action.title, f"action :title must not contain '/': {action.title}"
        assert action.title not in action_keys, f"Duplicate action title under {location_id}: {action.title}"
        action_keys.add(action.title)

    child_keys: set[str] = set()
    for child in location.children:
        assert child.title, "child location :title must not be empty"
        assert "/" not in child.title, f"child location :title must not contain '/': {child.title}"
        assert child.title not in action_keys, f"Location title conflicts with action title under {location_id}: {child.title}"
        assert child.title not in child_keys, f"Duplicate child location title under {location_id}: {child.title}"
        child_keys.add(child.title)

    path = (*location_path, location_key)
    shown_clock_ids, shown_clocks, nested_clocks = _rendered_location_clocks(program, location.shown_clock_ids, location_id)
    rendered_actions: list[RenderedAction] = []
    for source_index, action in enumerate(location.actions):
        rendered_actions.append(_render_action(program, action, location_path=path, source_index=source_index))
    rendered_children = tuple(
        render_location(program, child, location_path=path, mounted_locations=mounted_locations, mounted_actions=mounted_actions)
        for child in location.children
    )
    root = LocationDef(
        id=location_id,
        title=location.title,
        description=location.description,
        position=location.position,
        show_clock_ids=shown_clock_ids,
        actions=tuple(item.action for item in rendered_actions),
        children=tuple(child.root for child in rendered_children),
        conditions=tuple(location.conditions),
    )
    return RenderedLocation(
        location_id=location_id,
        root=root,
        shown_clock_ids=shown_clock_ids,
        shown_clocks=shown_clocks,
        nested_clocks=nested_clocks,
        actions=tuple(rendered_actions),
        children=rendered_children,
    )


def flatten_location(
    rendered: RenderedLocation,
    *,
    parent_id: str | None,
    locations_by_id: dict[str, LocationDef],
    parent_by_id: dict[str, str | None],
    actions_by_id: dict[str, ActionDef],
    actions_by_location: dict[str, tuple[str, ...]],
    action_handles_by_id: dict[str, ActionHandle],
    shown_clock_ids_by_location: dict[str, tuple[str, ...]],
    shown_clocks_by_location: dict[str, tuple[RenderedClock, ...]] | None = None,
    nested_clocks_by_id: dict[str, RuntimeClockValue] | None = None,
) -> None:
    root = rendered.root
    assert root.id not in locations_by_id, f"Duplicate location title/id: {root.id}"
    locations_by_id[root.id] = root
    parent_by_id[root.id] = parent_id
    actions_by_location[root.id] = tuple(item.action.id for item in rendered.actions)
    shown_clock_ids_by_location[root.id] = rendered.shown_clock_ids
    if shown_clocks_by_location is not None:
        shown_clocks_by_location[root.id] = rendered.shown_clocks
    if nested_clocks_by_id is not None:
        nested_clocks_by_id.update(rendered.nested_clocks)
    for item in rendered.actions:
        assert item.action.id not in actions_by_id, f"Duplicate rendered action id: {item.action.id}"
        actions_by_id[item.action.id] = item.action
        action_handles_by_id[item.action.id] = item.handle
    for child in rendered.children:
        flatten_location(
            child,
            parent_id=root.id,
            locations_by_id=locations_by_id,
            parent_by_id=parent_by_id,
            actions_by_id=actions_by_id,
            actions_by_location=actions_by_location,
            action_handles_by_id=action_handles_by_id,
            shown_clock_ids_by_location=shown_clock_ids_by_location,
            shown_clocks_by_location=shown_clocks_by_location,
            nested_clocks_by_id=nested_clocks_by_id,
        )


def _rendered_location_clocks(program: Any, items: tuple[Any, ...], location_id: str) -> tuple[tuple[str, ...], tuple[RenderedClock, ...], dict[str, RuntimeClockValue]]:
    clock_ids: list[str] = []
    clocks: list[RenderedClock] = []
    nested: dict[str, RuntimeClockValue] = {}
    nested_index = 0
    for item in items:
        if isinstance(item, RuntimeClockValue):
            clock_id = f"{location_id}:nested-clock:{nested_index}"
            nested_index += 1
            clock_ids.append(clock_id)
            nested[clock_id] = item
            clocks.append(RenderedClock(id=clock_id, title=item.title, description=item.description, value=item.value, maximum=item.maximum))
        elif isinstance(item, StateBindingValue):
            assert item.spec.kind == "clock", f"Expected clock binding, got: {item.name}"
            spec = getattr(program, "clocks_by_id", {}).get(item.name)
            title = getattr(spec, "title", item.spec.title)
            description = getattr(spec, "description", "")
            maximum = getattr(spec, "segments", item.spec.maximum)
            assert maximum is not None, f"Clock binding missing maximum: {item.name}"
            raw_value = item.value.value if isinstance(item.value, RuntimeClockValue) else item.value
            clock_ids.append(item.name)
            clocks.append(RenderedClock(id=item.name, title=title, description=description, value=int(raw_value), maximum=int(maximum)))
        else:
            clock_ids.append(clock_id_for_show(item))
            spec = getattr(program, "clocks_by_id", {}).get(str(item))
            if spec is not None:
                clocks.append(RenderedClock(id=str(item), title=spec.title, description=spec.description, value=0, maximum=spec.segments))
    return tuple(clock_ids), tuple(clocks), nested


def host_values(*, store_specs: dict[str, StoreFieldSpec], store: dict[str, Any]) -> dict[str, Any]:
    return {
        "clock": builtin_clock,
        "clocks": lambda *args: [item for item in args if item is not None],
        "var": SpecialFormProcedure(builtin_var),
        "meta": lambda *args: builtin_meta(args),
        "condition": builtin_condition,
        "has-item": builtin_has_item_condition,
        "field-at-least": builtin_field_at_least_condition,
        "field-below": builtin_field_below_condition,
        "field-equals": builtin_field_equals_condition,
        "field-truthy": builtin_field_truthy_condition,
        "react": SpecialFormProcedure(builtin_react),
        "reaction-table": lambda *args: builtin_reaction_table(args),
        "face": lambda *args: builtin_reaction_face(args),
        "world-attr": builtin_world_attr,
        "world-value": builtin_world_value,
        "world-item": builtin_world_item,
        "import-world-attr": lambda key: [binding_name(key), builtin_world_attr(key)],
        "import-world-value": lambda key, initial=False: [binding_name(key), builtin_world_value(key, initial)],
        "import-world-item": lambda key, initial=0: [binding_name(key), builtin_world_item(key, initial)],
        "task": SpecialFormProcedure(builtin_task),
        "step": SpecialFormProcedure(builtin_task_step),
        "location": lambda *args: builtin_location(args),
        "action": lambda *args: builtin_action(args),
        "reveal": lambda *args: builtin_reveal(args),
        "check": lambda *args: builtin_check(args),
        "factor": lambda *args: builtin_check_factor(args),
        "outcome": lambda *args: builtin_outcome(args),
        "effect": SpecialFormProcedure(builtin_effect),
        "effect-expr": SpecialFormProcedure(builtin_effect_expr),
        "item": builtin_item_input,
        "card": builtin_card_input,
        "console-log": builtin_log,
        "clock-value": lambda value: clock_metric(value, "value"),
        "clock-max": lambda value: clock_metric(value, "maximum"),
        "clock-shift": builtin_clock_shift,
        "clock-reset": lambda value: builtin_clock_shift(value, -clock_metric(value, "value")),
        "clock-half": lambda value: (clock_metric(value, "maximum") + 1) // 2,
        "clock-empty?": lambda value: clock_metric(value, "value") == 0,
        "clock-filled?": lambda value: clock_metric(value, "value") == clock_metric(value, "maximum"),
        "clock-partial?": lambda value: 0 < clock_metric(value, "value") < clock_metric(value, "maximum"),
        "clock-at-least-half?": lambda value: clock_metric(value, "value") >= ((clock_metric(value, "maximum") + 1) // 2),
        "set!": SpecialFormProcedure(lambda args, env: builtin_set_bang(args, env, store=store, store_specs=store_specs)),
    }


def builtin_meta(args: tuple[Any, ...]) -> EncounterMeta:
    kwargs = keyword_args(list(args), allowed={":key", ":title", ":desc"})
    key = keyword_string(kwargs, ":key", allow_symbol=True)
    title = keyword_string(kwargs, ":title")
    description = keyword_string(kwargs, ":desc", default="")
    return EncounterMeta(key=key, title=title, description=description)


def builtin_var(args: list[Any], env: Environment) -> list[Any]:
    assert len(args) == 2, "`var` expects name and value."
    key = unwrap(evaluate(args[0], env))
    assert isinstance(key, str), f"`var` name must be a symbol/string, got: {key!r}"
    return [key, args[1]]


def builtin_clock(*args: Any) -> ClockTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":desc", ":initial", ":max"})
    title = keyword_string(kwargs, ":title")
    description = keyword_string(kwargs, ":desc", default="")
    initial = int(unwrap(kwargs[":initial"]))
    maximum = int(unwrap(kwargs[":max"]))
    assert 0 <= initial <= maximum, "Clock initial must be within range."
    return ClockTemplate(title=title, description=description, initial=initial, maximum=maximum)


def builtin_outcome(args: tuple[Any, ...]) -> OutcomeTemplate:
    assert 1 <= len(args) <= 2, "outcome expects effects plus an optional description."
    first = unwrap(args[0])
    if isinstance(first, str):
        # Backward-compatible authoring form: (outcome "description" effects).
        return OutcomeTemplate(text=first, effects=as_effect_tuple(args[1] if len(args) == 2 else None))
    description = "" if len(args) == 1 else str(unwrap(args[1]))
    return OutcomeTemplate(text=description, effects=as_effect_tuple(args[0]))


def builtin_world_value(key: Any, initial: Any = False) -> StateBindingValue:
    name = binding_name(key)
    value = unwrap(initial)
    assert isinstance(value, (bool, int, str)), f"Unsupported world value initial for {name}: {value!r}"
    return StateBindingValue(
        name=name,
        spec=StoreFieldSpec(id=name, kind="value", initial=value, persist="world_value"),
        value=value,
    )


def builtin_world_attr(key: Any) -> StateBindingValue:
    name = binding_name(key)
    assert name in {"health", "energy", "pressure", "force", "charm", "knowledge", "sense"}, f"Unsupported world attr: {name}"
    return StateBindingValue(
        name=name,
        spec=StoreFieldSpec(id=name, kind="value", initial=0, persist="world_attr"),
        value=0,
    )


def builtin_world_item(key: Any, initial: Any = 0) -> StateBindingValue:
    name = binding_name(key)
    value = int(unwrap(initial))
    return StateBindingValue(
        name=name,
        spec=StoreFieldSpec(id=name, kind="value", initial=value, persist="world_inventory"),
        value=value,
    )


def builtin_location(args: tuple[Any, ...]) -> LocationTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":desc", ":position", ":show-clocks", ":conditions", ":actions", ":children"})
    return LocationTemplate(
        title=keyword_string(kwargs, ":title"),
        description=keyword_string(kwargs, ":desc", default=""),
        position=position_tuple(kwargs.get(":position")),
        shown_clock_ids=tuple(clock_value_for_show(item) for item in as_list(kwargs.get(":show-clocks")) if item is not None),
        conditions=tuple(item for item in as_list_or_single(kwargs.get(":conditions")) if item is not None),
        actions=tuple(item for item in as_list_or_single(kwargs.get(":actions")) if item is not None),
        children=tuple(item for item in as_list_or_single(kwargs.get(":children")) if item is not None),
    )


def builtin_reveal(args: tuple[Any, ...]) -> ActionRevealDef:
    kwargs = keyword_args(list(args), allowed={":text", ":duration", ":title"})
    text = keyword_string(kwargs, ":text")
    duration = float(unwrap(kwargs.get(":duration", 0.0)))
    title = keyword_string(kwargs, ":title", default="")
    assert text.strip(), ":reveal :text must not be empty"
    assert duration >= 0, ":reveal :duration must be non-negative"
    return ActionRevealDef(text=text, duration=duration, title=title)


def builtin_action(args: tuple[Any, ...]) -> ActionTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":desc", ":position", ":conditions", ":inputs", ":always", ":effects", ":check", ":reveal", ":button"})
    check = kwargs.get(":check")
    effects = as_effect_tuple(kwargs.get(":effects"))
    before = as_effect_tuple(kwargs.get(":always"))
    reveal = kwargs.get(":reveal")
    button = keyword_string(kwargs, ":button", default="")
    assert check is None or not effects, "Action cannot have both :check and :effects."
    assert reveal is None or check is None, "Action cannot have both :check and :reveal."
    assert reveal is None or not kwargs.get(":inputs"), "Reveal actions cannot have :inputs."
    if button:
        assert button.strip(), ":button must not be empty"
    return ActionTemplate(
        title=keyword_string(kwargs, ":title"),
        description=keyword_string(kwargs, ":desc", default=""),
        position=position_tuple(kwargs.get(":position")),
        inputs=tuple(item for item in as_list(kwargs.get(":inputs")) if item is not None),
        before=before,
        effects=effects,
        conditions=tuple(item for item in as_list(kwargs.get(":conditions")) if item is not None),
        check=check,
        reveal=reveal,
        button_label=button,
    )


def builtin_check(args: tuple[Any, ...]) -> CheckTemplate:
    kwargs = keyword_args(list(args), allowed={":suit", ":risk", ":factors", ":ok", ":partial", ":fail"})
    suit = unwrap(kwargs.get(":suit"))
    risk = keyword_string(kwargs, ":risk", allow_symbol=True)
    factors = tuple(item for item in as_list(kwargs.get(":factors")) if item is not None)
    for item in factors:
        assert isinstance(item, CheckFactorDef), f"check factor must be factor form, got: {item!r}"
    success = kwargs.get(":ok")
    cost = kwargs.get(":partial")
    fail = kwargs.get(":fail")
    assert isinstance(success, OutcomeTemplate) and isinstance(cost, OutcomeTemplate) and isinstance(fail, OutcomeTemplate), "Check outcomes must be outcome forms."
    return CheckTemplate(suit=suit, risk=risk, success=success, cost=cost, fail=fail, factors=factors)


def builtin_check_factor(args: tuple[Any, ...]) -> CheckFactorDef:
    assert args, "`factor` requires a numeric value."
    value = int(unwrap(args[0]))
    kwargs = keyword_args(list(args[1:]), allowed={":when", ":label"})
    active = True if ":when" not in kwargs else truthy(kwargs[":when"])
    label = keyword_string(kwargs, ":label", default="")
    assert label.strip(), "`factor` requires :label."
    return CheckFactorDef(value=value, label=label, active=active, source=kwargs.get(":when"))


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


def builtin_field_below_condition(key: Any, amount: Any, label: Any | None = None) -> Condition:
    key_value = str(unwrap(key))
    amount_value = int(unwrap(amount))
    return Condition(kind="field_below", value=f"{key_value}:{amount_value}", label=("" if label is None else str(unwrap(label))))


def builtin_field_equals_condition(key: Any, expected: Any, label: Any | None = None) -> Condition:
    key_value = str(unwrap(key))
    expected_value = effect_token(expected)
    return Condition(kind="field_equals", value=f"{key_value}:{expected_value}", label=("" if label is None else str(unwrap(label))))


def builtin_field_truthy_condition(key: Any, label: Any | None = None) -> Condition:
    key_value = str(unwrap(key))
    return Condition(kind="field_truthy", value=key_value, label=("" if label is None else str(unwrap(label))))


def builtin_react(args: list[Any], env: Environment) -> ReactTemplate:
    kwargs = keyword_args(list(args), allowed={":when", ":then"})
    condition = Procedure(params=(), body=normalize_react_condition_body(kwargs[":when"], env), env=env)
    effects_expr = kwargs[":then"]
    effects = eval_effect_list(effects_expr, env)
    ref = source_ref(args)
    location = format_source_ref(ref)
    when_summary = format_sexp(kwargs[":when"], max_length=120)
    source = f"{location} when={when_summary}" if location else f"when={when_summary}"
    return ReactTemplate(condition=condition, effects=effects, effects_expr=effects_expr, source=source)


def builtin_reaction_table(args: tuple[Any, ...]) -> ReactionTable:
    faces = tuple(item for item in args if item is not None)
    table = ReactionTable(faces=faces)
    validate_reaction_table(table)
    return table


def builtin_reaction_face(args: tuple[Any, ...]) -> ReactionFace:
    assert len(args) >= 2, "face expects value and title."
    value = int(unwrap(args[0]))
    title = str(unwrap(args[1]))
    description = ""
    effect_start = 2
    if len(args) >= 3 and not isinstance(args[2], Effect):
        description = str(unwrap(args[2]))
        effect_start = 3
    effects = tuple(item for item in args[effect_start:] if item is not None)
    face = ReactionFace(value=value, title=title, description=description, effects=effects)
    validate_reaction_face(face)
    return face


def builtin_effect_expr(args: list[Any], env: Environment) -> Effect:
    assert args, "`effect-expr` requires a body."
    raw_body: Any = args[0] if len(args) == 1 else ["begin", *args]

    def is_local_symbol(name: str) -> bool:
        curr = env
        while curr is not None:
            if name in curr.values:
                if curr.parent is None or curr.parent.parent is None:
                    return False
                return True
            curr = curr.parent
        return False

    def resolve_bound_symbols(expr: Any) -> Any:
        if isinstance(expr, list):
            if not expr:
                return []
            head = expr[0]
            if head == "quote":
                return expr
            if head == "lambda":
                assert len(expr) >= 3, "`lambda` needs a body."
                params = expr[1]
                resolved_body = [resolve_bound_symbols(item) for item in expr[2:]]
                return ["lambda", params, *resolved_body]
            if head in {"let", "let*"}:
                assert len(expr) >= 3 and isinstance(expr[1], list), f"`{head}` expects bindings and body."
                bindings = expr[1]
                resolved_bindings = []
                for binding in bindings:
                    assert isinstance(binding, list) and len(binding) == 2
                    resolved_bindings.append([binding[0], resolve_bound_symbols(binding[1])])
                resolved_body = [resolve_bound_symbols(item) for item in expr[2:]]
                return [head, resolved_bindings, *resolved_body]
            return [resolve_bound_symbols(item) for item in expr]

        if isinstance(expr, str) and not expr.startswith(":"):
            if is_local_symbol(expr):
                return env.lookup(expr)

        return expr

    body = resolve_bound_symbols(raw_body)
    return Effect(kind="expr", value=body)


def builtin_set_bang(args: list[Any], env: Environment, *, store: dict[str, Any], store_specs: dict[str, StoreFieldSpec]) -> Any:
    assert len(args) == 2 and isinstance(args[0], str), "`set!` expects a state field and value expression."
    target = args[0]
    assert target in store_specs, f"`set!` target must be an encounter state field: {target}"
    spec = store_specs[target]
    value = runtime_value(evaluate(args[1], env))
    if spec.kind == "clock":
        assert isinstance(value, RuntimeClockValue), f"`set!` clock field `{target}` expects a clock value, got: {value!r}"
        value = value.value
    store[target] = value
    return value


def builtin_task(args: list[Any], env: Environment) -> TaskTemplate:
    kwargs = keyword_args(list(args), allowed={":kind", ":title", ":desc", ":active", ":completed", ":failed", ":steps"})
    steps = evaluate(kwargs.get(":steps", []), env)
    return TaskTemplate(
        kind=str(unwrap(evaluate(kwargs[":kind"], env))),
        title=normalize_react_condition_body(kwargs[":title"], env),
        description=normalize_react_condition_body(kwargs.get(":desc", ["quote", ""]), env),
        active=Procedure(params=(), body=normalize_react_condition_body(kwargs.get(":active", False), env), env=env),
        completed=Procedure(params=(), body=normalize_react_condition_body(kwargs.get(":completed", False), env), env=env),
        failed=Procedure(params=(), body=normalize_react_condition_body(kwargs.get(":failed", False), env), env=env),
        steps=tuple(item for item in as_list(steps) if item is not None),
    )


def builtin_task_step(args: list[Any], env: Environment) -> TaskStepTemplate:
    kwargs = keyword_args(list(args), allowed={":title", ":completed"})
    return TaskStepTemplate(
        title=normalize_react_condition_body(kwargs[":title"], env),
        completed=Procedure(params=(), body=normalize_react_condition_body(kwargs.get(":completed", False), env), env=env),
    )


def normalize_react_condition_body(expr: Any, env: Environment) -> Any:
    if isinstance(expr, list):
        if not expr:
            return []
        if expr[0] == "quote":
            return expr
        return [normalize_react_condition_body(item, env) for item in expr]
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


def eval_react_condition(condition: Any, env: Environment) -> Any:
    assert isinstance(condition, Procedure) and not condition.params, f"react condition must be a zero-argument procedure: {condition!r}"
    return evaluate(condition.body, env)


def builtin_effect(args: list[Any], env: Environment) -> Effect:
    assert args, "`effect` requires a kind."
    kind = unwrap(evaluate(args[0], env))
    if kind == "start-dialogue":
        return Effect(kind="start_dialogue", value=str(unwrap(evaluate(args[1], env))))
    if kind == "start-quick-dialogue":
        return Effect(kind="start_quick_dialogue", value=str(unwrap(evaluate(args[1], env))))
    if kind == "upgrade-spirit-value":
        return Effect(kind="upgrade_spirit_value", value=f"{str(unwrap(evaluate(args[1], env)))}:{int(unwrap(evaluate(args[2], env)))}")
    if kind == "add-spirit-slot":
        return Effect(kind="add_spirit_slot", value=str(unwrap(evaluate(args[1], env))))
    if kind in {"clock+", "clock-"}:
        target = clock_id(evaluate(args[1], env))
        delta = int(unwrap(evaluate(args[2], env)))
        if kind == "clock-":
            delta = -delta
        return Effect(kind="shift_clock", value=ShiftClockPayload(target=target, amount=delta))
    if kind == "set":
        target = binding_name(evaluate(args[1], env))
        return Effect(kind="set_field", value=SetFieldPayload(target=target, value=effect_value_expr(args[2], env)))
    if kind == "add":
        target = binding_name(evaluate(args[1], env))
        return Effect(kind="add_field", value=AddFieldPayload(target=target, amount=int(unwrap(evaluate(args[2], env)))))
    if kind == "copy":
        target = binding_name(evaluate(args[1], env))
        source = binding_name(evaluate(args[2], env))
        return Effect(kind="set_field", value=SetFieldPayload(target=target, value=FieldRef(source)))
    if kind == "start-encounter":
        return Effect(kind="start_encounter", value=str(unwrap(evaluate(args[1], env))))
    if kind == "end-encounter":
        return Effect(kind="end_encounter", value=str(unwrap(evaluate(args[1], env))))
    if kind == "advance-cycle":
        return Effect(kind="advance_cycle", value=True)
    if kind == "mount-location":
        value = evaluate(args[1], env)
        assert isinstance(value, (list, tuple)) and len(value) == 2, "mount-location expects (parent_path location)"
        parent_path, template = value
        assert isinstance(parent_path, str) and parent_path, "mount-location parent_path must be a non-empty string"
        assert isinstance(template, LocationTemplate), "mount-location second argument must be a location form"
        return Effect(kind="mount_location", value=(parent_path, template))
    if kind == "unmount-location":
        value = evaluate(args[1], env)
        assert isinstance(value, (list, tuple)) and len(value) == 2, "unmount-location expects (parent_path title)"
        parent_path, child_title = value
        assert isinstance(parent_path, str) and parent_path, "unmount-location parent_path must be a non-empty string"
        assert isinstance(child_title, str) and child_title, "unmount-location title must be a non-empty string"
        return Effect(kind="unmount_location", value=(parent_path, child_title))
    if kind == "mount-action":
        value = evaluate(args[1], env)
        assert isinstance(value, (list, tuple)) and len(value) == 2, "mount-action expects (parent_path action)"
        parent_path, template = value
        assert isinstance(parent_path, str) and parent_path, "mount-action parent_path must be a non-empty string"
        assert isinstance(template, ActionTemplate), "mount-action second argument must be an action form"
        return Effect(kind="mount_action", value=(parent_path, template))
    if kind == "unmount-action":
        value = evaluate(args[1], env)
        assert isinstance(value, (list, tuple)) and len(value) == 2, "unmount-action expects (parent_path title)"
        parent_path, child_title = value
        assert isinstance(parent_path, str) and parent_path, "unmount-action parent_path must be a non-empty string"
        assert isinstance(child_title, str) and child_title, "unmount-action title must be a non-empty string"
        return Effect(kind="unmount_action", value=(parent_path, child_title))
    if kind == "end-game":
        assert len(args) in {1, 3}, "`end-game` takes zero parameters, or title and body."
        if len(args) == 3:
            return Effect(kind="end_game", value=(str(unwrap(evaluate(args[1], env))), str(unwrap(evaluate(args[2], env)))))
        return Effect(kind="end_game", value=True)
    raise EncounterSchemaError(f"Unsupported encounter effect kind: {kind}")


def builtin_log(*args: Any) -> None:
    parts = [str(unwrap(arg)) for arg in args]
    print("[SCM]", *parts)
    return None


def builtin_item_input(key: Any, amount: Any = 1, label: Any | None = None) -> InputRequirement:
    key_value = str(unwrap(key))
    resolved_label = lookup_input_label(key_value) if label is None else str(unwrap(label))
    return InputRequirement(kind="item", key=key_value, amount=int(unwrap(amount)), label=resolved_label, consume=True)


def builtin_card_input(key: Any, label: Any | None = None) -> InputRequirement:
    key_value = str(unwrap(key))
    return InputRequirement(kind="card", key=key_value, amount=1, label=("负面牌" if key_value == "negative" else ("精神槽位" if label is None else str(unwrap(label)))), consume=True)


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


def runtime_value(value: Any) -> Any:
    raw = unwrap(value)
    if isinstance(raw, ClockTemplate):
        return RuntimeClockValue(title=raw.title, description=raw.description, value=raw.initial, maximum=raw.maximum)
    if isinstance(raw, ObjectValue):
        return ObjectValue(fields={key: runtime_value(item) for key, item in raw.fields.items()})
    if isinstance(raw, list):
        return [runtime_value(item) for item in raw]
    return raw


def clock_metric(value: Any, field: str) -> int:
    raw = unwrap(value)
    if isinstance(raw, RuntimeClockValue):
        if field == "value":
            return raw.value
        return raw.maximum
    bound = binding(value)
    assert bound.spec.kind == "clock", f"Clock operation requires a clock binding: {bound.name}"
    if isinstance(bound.value, RuntimeClockValue):
        if field == "value":
            return bound.value.value
        return bound.value.maximum
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


def clock_value_for_show(value: Any) -> Any:
    raw = unwrap(value)
    if isinstance(raw, RuntimeClockValue):
        return raw
    bound = binding(value)
    assert bound.spec.kind == "clock", f"Expected clock binding, got: {bound.name}"
    return bound


def clock_id_for_show(value: Any) -> str:
    assert isinstance(value, str), f"Expected rendered clock id, got: {value!r}"
    return value


def effect_token(value: Any) -> str:
    raw = unwrap(value)
    if isinstance(raw, RuntimeClockValue):
        return str(raw.value)
    if raw is None:
        return "nil"
    if raw is True:
        return "true"
    if raw is False:
        return "false"
    return str(raw)


def effect_value_expr(expr: Any, env: Environment) -> str | int | bool | None | FieldRef | DynamicValue:
    if isinstance(expr, list) and expr and expr[0] != "quote":
        return DynamicValue(resolve_runtime_value_expr(expr, env))
    return effect_value(evaluate(expr, env))


def effect_value(value: Any) -> str | int | bool | None | FieldRef:
    if isinstance(value, StateBindingValue):
        return FieldRef(value.name)
    raw = unwrap(value)
    if isinstance(raw, RuntimeClockValue):
        return raw.value
    if raw is None:
        return None
    assert isinstance(raw, (str, int, bool)), f"Unsupported effect value: {raw!r}"
    return raw


def resolve_runtime_value_expr(expr: Any, env: Environment) -> Any:
    if isinstance(expr, list):
        if not expr:
            return []
        if expr[0] == "quote":
            return expr
        return [resolve_runtime_value_expr(item, env) for item in expr]
    if not isinstance(expr, str):
        return expr
    try:
        value = env.lookup(expr)
    except EncounterSchemeError:
        return expr
    if isinstance(value, StateBindingValue):
        return expr
    if isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return ["quote", value]
    return expr


def builtin_clock_shift(value: Any, amount: Any) -> RuntimeClockValue:
    raw = unwrap(value)
    assert isinstance(raw, RuntimeClockValue), f"`clock-shift` expects a nested clock value, got: {raw!r}"
    delta = int(unwrap(amount))
    next_value = max(0, min(raw.maximum, raw.value + delta))
    return RuntimeClockValue(title=raw.title, description=raw.description, value=next_value, maximum=raw.maximum)


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


def as_list_or_single(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


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


def _render_action(program: Any, action: ActionTemplate, *, location_path: tuple[str, ...], source_index: int) -> RenderedAction:
    assert action.title, "action :title must not be empty"
    assert "/" not in action.title, f"action :title must not contain '/': {action.title}"
    action_key = action.title
    action_id = "/".join(location_path + (action_key,))
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
        reveal=action.reveal,
        button_label=action.button_label,
    )
    handle = ActionHandle(action_id=action_id, location_path=location_path, slot_index=source_index, action_key=action_key)
    return RenderedAction(handle=handle, action=replace(action_def, id=action_id))
