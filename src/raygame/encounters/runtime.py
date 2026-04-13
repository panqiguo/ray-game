from __future__ import annotations

import hashlib
from dataclasses import replace

from raygame.encounters.defs import (
    ActionHandle,
    ClockRef,
    CompiledEncounterProgram,
    MacroTemplate,
    ReactRule,
    RenderedAction,
    RenderedEncounter,
    RenderedScene,
    SexpNode,
    StoreFieldSpec,
    StringAtom,
)
from raygame.encounters.sexp import parse_sexp
from raygame.model.defs import ActionDef, CheckDef, Effect, LocationNode, OutcomeDef, ProgressClockSpec
from raygame.model.enums import Risk, ScreenName, Suit


MAX_REACT_STEPS = 64
RISK_BY_NAME = {"low": Risk.LOW, "mid": Risk.MID, "high": Risk.HIGH}
SUIT_BY_NAME = {
    "reason": Suit.REASON,
    "force": Suit.FORCE,
    "empathy": Suit.EMPATHY,
    "instinct": Suit.INSTINCT,
}

EXPR_KIND_BOOL = "bool"
EXPR_KIND_VALUE = "value"
EXPR_KIND_CLOCK_REF = "clock-ref"
EXPR_KIND_SCENE = "scene"
EXPR_KIND_ACTION = "action"


def compile_encounter_program(source: str) -> CompiledEncounterProgram:
    forms = parse_sexp(source)
    bindings: dict[str, SexpNode] = {}
    macros: dict[str, MacroTemplate] = {}
    last_value: CompiledEncounterProgram | None = None
    for form in forms:
        expanded = _macroexpand(form, macros)
        if _is_symbol_list(expanded, "def"):
            _eval_def(expanded, bindings)
            continue
        if _is_symbol_list(expanded, "defmacro"):
            template = _eval_defmacro(expanded)
            macros[template.name] = template
            continue
        if _is_symbol_list(expanded, "encounter"):
            last_value = _compile_encounter_form(expanded, bindings=bindings, macros=macros)
            continue
        raise AssertionError(f"Unsupported top-level form: {_form_head(expanded)}")
    assert last_value is not None, "Encounter file must evaluate to an Encounter."
    return last_value


def initial_store(program: CompiledEncounterProgram) -> dict[str, int | bool | str]:
    return {field_id: spec.initial for field_id, spec in program.store_specs.items()}


def render_encounter(program: CompiledEncounterProgram, store: dict[str, int | bool | str]) -> RenderedEncounter:
    scene = _eval_scene_expr(program, store, program.view_expr, scene_path=())
    assert scene is not None, f"Encounter view rendered no scene: {program.id}"
    locations_by_id: dict[str, LocationNode] = {}
    parent_by_id: dict[str, str | None] = {}
    actions_by_id: dict[str, ActionDef] = {}
    actions_by_location: dict[str, tuple[str, ...]] = {}
    action_handles_by_id: dict[str, ActionHandle] = {}
    shown_clock_ids_by_scene: dict[str, tuple[str, ...]] = {}
    _flatten_scene(
        scene,
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
        root=scene,
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        action_handles_by_id=action_handles_by_id,
        shown_clock_ids_by_scene=shown_clock_ids_by_scene,
    )


def next_react_rule(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    blocked_sources: set[str],
) -> ReactRule | None:
    for rule in program.react_rules:
        if rule.source in blocked_sources and react_rule_matches(program, store, rule):
            continue
        if react_rule_matches(program, store, rule):
            return rule
    return None


def react_rule_matches(program: CompiledEncounterProgram, store: dict[str, int | bool | str], rule: ReactRule) -> bool:
    return _eval_condition(program, store, rule.condition, scene_path=())


def validate_encounter_program(program: CompiledEncounterProgram) -> None:
    scene_ids: set[str] = set()
    for name, value in program.bindings.items():
        if isinstance(value, list) and value:
            head = _form_head(value)
            if head in {"scene", "if", "cond"}:
                _validate_expr(program, value, expected_kind=EXPR_KIND_SCENE, scene_ids=scene_ids, scene_path=())
            elif head in {"action", "check"}:
                _validate_expr(program, value, expected_kind=EXPR_KIND_ACTION, scene_ids=scene_ids, scene_path=())
    for rule in program.react_rules:
        _validate_expr(program, rule.condition, expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=())
    _validate_expr(program, program.view_expr, expected_kind=EXPR_KIND_SCENE, scene_ids=scene_ids, scene_path=())


def _eval_def(form: list[SexpNode], bindings: dict[str, SexpNode]) -> None:
    assert len(form) == 3, "`def` expects exactly two arguments."
    name = _symbol(form[1])
    bindings[name] = form[2]


def _eval_defmacro(form: list[SexpNode]) -> MacroTemplate:
    if len(form) == 4:
        name = _symbol(form[1])
        params = tuple(_symbol(item) for item in _list(form[2]))
        body = form[3]
        return MacroTemplate(name=name, params=params, body=body)
    assert len(form) == 3, "`defmacro` expects `(defmacro name (params...) body)` or `(defmacro (name params...) body)`."
    signature = _list(form[1])
    assert signature, "`defmacro` signature must be non-empty."
    name = _symbol(signature[0])
    params = tuple(_symbol(item) for item in signature[1:])
    body = form[2]
    return MacroTemplate(name=name, params=params, body=body)


def _compile_encounter_form(
    form: list[SexpNode],
    *,
    bindings: dict[str, SexpNode],
    macros: dict[str, MacroTemplate],
) -> CompiledEncounterProgram:
    field_forms = _expand_encounter_fields(form[1:], macros)
    encounter_id = ""
    title = ""
    description = ""
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()
    store_specs: dict[str, StoreFieldSpec] = {}
    clocks_by_id: dict[str, ProgressClockSpec] = {}
    react_rules: list[ReactRule] = []
    view_expr: SexpNode | None = None
    for field in field_forms:
        items = _list(field)
        head = _symbol(items[0])
        if head == "id":
            encounter_id = _static_symbol(items[1], bindings)
        elif head == "title":
            title = _static_string(items[1], bindings)
        elif head == "desc":
            description = _static_string(items[1], bindings)
        elif head == "reward":
            rewards = tuple(_compile_effect(effect_form, store_specs) for effect_form in items[1:])
        elif head == "fail":
            fail_effects = tuple(_compile_effect(effect_form, store_specs) for effect_form in items[1:])
        elif head == "store":
            for spec_form in items[1:]:
                spec = _compile_store_field(_list(spec_form), bindings)
                assert spec.id not in store_specs, f"Duplicate encounter store field: {spec.id}"
                store_specs[spec.id] = spec
                if spec.kind == "clock":
                    assert isinstance(spec.initial, int) and isinstance(spec.maximum, int)
                    clocks_by_id[spec.id] = ProgressClockSpec(id=spec.id, title=spec.title, segments=spec.maximum)
        elif head == "reacts":
            for index, rule_form in enumerate(items[1:]):
                rule_items = _list(rule_form)
                assert len(rule_items) >= 2, "React rule must contain condition and at least one effect."
                react_rules.append(
                    ReactRule(
                        condition=rule_items[0],
                        effects=tuple(_compile_effect(effect_form, store_specs) for effect_form in rule_items[1:]),
                        source=f"react[{index}]",
                    )
                )
        elif head == "view":
            assert len(items) == 2, "`view` expects exactly one scene expression."
            view_expr = items[1]
        else:
            raise AssertionError(f"Unsupported encounter field: {head}")
    assert encounter_id, "Encounter missing id."
    assert title, f"Encounter missing title: {encounter_id or '<unknown>'}"
    assert store_specs, f"Encounter missing store: {encounter_id}"
    assert view_expr is not None, f"Encounter missing view: {encounter_id}"
    return CompiledEncounterProgram(
        id=encounter_id,
        title=title,
        description=description,
        store_specs=store_specs,
        clocks_by_id=clocks_by_id,
        bindings=dict(bindings),
        macros=dict(macros),
        react_rules=tuple(react_rules),
        view_expr=view_expr,
        rewards=rewards,
        fail_effects=fail_effects,
    )


def _expand_encounter_fields(forms: list[SexpNode], macros: dict[str, MacroTemplate]) -> list[SexpNode]:
    expanded_fields: list[SexpNode] = []
    for form in forms:
        expanded = _macroexpand(form, macros)
        if isinstance(expanded, list) and expanded and _form_head(expanded) == "quote":
            expanded_fields.append(expanded)
            continue
        if isinstance(expanded, list) and expanded and isinstance(expanded[0], list):
            expanded_fields.extend(_list(item) for item in expanded)
            continue
        expanded_fields.append(expanded)
    return expanded_fields


def _compile_store_field(form: list[SexpNode], bindings: dict[str, SexpNode]) -> StoreFieldSpec:
    head = _symbol(form[0])
    if head == "clock":
        field_id = _symbol(form[1])
        title = _static_string(form[2], bindings)
        initial = _static_int(form[3], bindings)
        maximum = _static_int(form[4], bindings)
        assert 0 <= initial <= maximum, f"Clock initial out of range: {field_id}"
        return StoreFieldSpec(id=field_id, kind="clock", initial=initial, title=title, maximum=maximum)
    if head == "flag":
        return StoreFieldSpec(id=_symbol(form[1]), kind="flag", initial=_static_bool(form[2], bindings))
    if head == "value":
        return StoreFieldSpec(id=_symbol(form[1]), kind="value", initial=_static_atom(form[2], bindings))
    raise AssertionError(f"Unsupported store form: {head}")


def _compile_effect(form: SexpNode, store_specs: dict[str, StoreFieldSpec]) -> Effect:
    items = _list(form)
    head = _symbol(items[0])
    if head in store_specs and store_specs[head].kind == "clock":
        delta = _signed_int(items[1])
        if delta >= 0:
            return Effect(kind="advance_encounter_clock", value=f"{head}:{delta}")
        return Effect(kind="damage_encounter_clock", value=f"{head}:{-delta}")
    if head == "health":
        return Effect(kind="change_health", value=_signed_int(items[1]))
    if head == "stress":
        return Effect(kind="change_stress", value=_signed_int(items[1]))
    if head == "money":
        return Effect(kind="change_resource", value=f"money:{_signed_int(items[1])}")
    if head == "reset-hand":
        return Effect(kind="reset_hand", value=True)
    if head == "set":
        field_id = _symbol(items[1])
        assert field_id in store_specs, f"Unknown encounter store field: {field_id}"
        return Effect(kind="set_encounter_store", value=f"{field_id}:{_effect_value_token(items[2])}")
    if head == "finish":
        return Effect(kind="finish_encounter", value=_symbol_or_literal(items[1]))
    raise AssertionError(f"Unsupported encounter effect: {head}")


def _effect_value_token(node: SexpNode) -> str:
    value = _atom_value(node)
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _eval_scene_expr(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    expr: SexpNode,
    *,
    scene_path: tuple[str, ...],
) -> RenderedScene | None:
    value = _eval_expr(program, store, expr, expected_kind=EXPR_KIND_SCENE, scene_path=scene_path)
    if value is None:
        return None
    assert isinstance(value, RenderedScene), f"Scene expression must resolve to scene or nil: {expr!r}"
    return value


def _eval_action_expr(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    expr: SexpNode,
    *,
    scene_path: tuple[str, ...],
    source_index: int,
) -> RenderedAction | None:
    value = _eval_expr(program, store, expr, expected_kind=EXPR_KIND_ACTION, scene_path=scene_path, source_index=source_index)
    if value is None:
        return None
    assert isinstance(value, RenderedAction), f"Action expression must resolve to action or nil: {expr!r}"
    return value


def _eval_expr(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    expr: SexpNode,
    *,
    expected_kind: str,
    scene_path: tuple[str, ...],
    source_index: int = 0,
) -> int | bool | str | None | ClockRef | RenderedScene | RenderedAction:
    if isinstance(expr, list):
        head = _symbol(expr[0])
        if head == "quote":
            assert len(expr) == 2, "`quote` expects exactly one argument."
            return _quoted_atom(expr[1])
        if head == "if":
            assert len(expr) == 4, "Expr if-expression must be `(if condition then else)`."
            branch = expr[2] if _eval_condition(program, store, expr[1], scene_path=scene_path) else expr[3]
            return _eval_expr(program, store, branch, expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)
        if head == "when":
            assert len(expr) == 3, "Expr when-expression must be `(when condition expr)`."
            assert expected_kind in {EXPR_KIND_CLOCK_REF, EXPR_KIND_SCENE, EXPR_KIND_ACTION}, "`when` is only valid in clock-ref/scene/action contexts."
            if _eval_condition(program, store, expr[1], scene_path=scene_path):
                return _eval_expr(program, store, expr[2], expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)
            return None
        if head == "cond":
            for clause in expr[1:]:
                clause_items = _list(clause)
                assert len(clause_items) == 2, "Each cond clause must be `(condition expr)`."
                cond_expr, body_expr = clause_items
                if (isinstance(cond_expr, str) and cond_expr == "else") or _eval_condition(program, store, cond_expr, scene_path=scene_path):
                    return _eval_expr(program, store, body_expr, expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)
            return None
        if head == "and":
            assert expected_kind == EXPR_KIND_BOOL, "`and` is only valid in bool expressions."
            return all(_eval_condition(program, store, item, scene_path=scene_path) for item in expr[1:])
        if head == "or":
            assert expected_kind == EXPR_KIND_BOOL, "`or` is only valid in bool expressions."
            return any(_eval_condition(program, store, item, scene_path=scene_path) for item in expr[1:])
        if head == "not":
            assert expected_kind == EXPR_KIND_BOOL, "`not` is only valid in bool expressions."
            assert len(expr) == 2, "`not` expects exactly one operand."
            return not _eval_condition(program, store, expr[1], scene_path=scene_path)
        if head in {"=", "<", "<=", ">", ">="}:
            assert expected_kind == EXPR_KIND_BOOL, f"`{head}` is only valid in bool expressions."
            left = _eval_value(program, store, expr[1], scene_path=scene_path)
            right = _eval_value(program, store, expr[2], scene_path=scene_path)
            if head == "=":
                return left == right
            if head == "<":
                return left < right
            if head == "<=":
                return left <= right
            if head == ">":
                return left > right
            return left >= right
        if head in {"+", "-", "min", "max"}:
            assert expected_kind == EXPR_KIND_VALUE, f"`{head}` is only valid in scalar expressions."
            numbers = [int(_eval_value(program, store, item, scene_path=scene_path)) for item in expr[1:]]
            if head == "+":
                return sum(numbers)
            if head == "-":
                assert len(numbers) >= 1, "`-` expects at least one operand."
                return numbers[0] if len(numbers) == 1 else numbers[0] - sum(numbers[1:])
            if head == "min":
                return min(numbers)
            return max(numbers)
        if head == "clock-value":
            assert expected_kind == EXPR_KIND_VALUE, "`clock-value` is only valid in value expressions."
            return _clock_current_value(program, store, _symbol(expr[1]))
        if head == "clock-full":
            assert expected_kind == EXPR_KIND_VALUE, "`clock-full` is only valid in value expressions."
            return _clock_full_value(program, _symbol(expr[1]))
        if head == "clock-half":
            assert expected_kind == EXPR_KIND_VALUE, "`clock-half` is only valid in value expressions."
            return _clock_half_value(program, _symbol(expr[1]))
        if head == "scene":
            assert expected_kind == EXPR_KIND_SCENE, "`scene` is only valid in scene contexts."
            return _build_scene(program, store, expr, scene_path=scene_path)
        if head in {"action", "check"}:
            assert expected_kind == EXPR_KIND_ACTION, f"`{head}` is only valid in action contexts."
            return _build_action(program, store, expr, scene_path=scene_path, source_index=source_index)
        raise AssertionError(f"Unsupported {expected_kind} expression: {expr}")
    if expected_kind == EXPR_KIND_CLOCK_REF:
        value = _resolve_runtime_symbol(program, store, expr, expected_kind=expected_kind, scene_path=scene_path)
        if value is None:
            return None
        if isinstance(value, ClockRef):
            return value
        raise AssertionError(f"Clock ref expression must resolve to clock ref or nil: {expr!r}")
    if expected_kind == EXPR_KIND_SCENE:
        value = _resolve_runtime_symbol(program, store, expr, expected_kind=expected_kind, scene_path=scene_path)
        if value is None:
            return None
        if isinstance(value, RenderedScene):
            return value
        raise AssertionError(f"Scene expression must resolve to scene or nil: {expr!r}")
    if expected_kind == EXPR_KIND_ACTION:
        value = _resolve_runtime_symbol(program, store, expr, expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)
        if value is None:
            return None
        if isinstance(value, RenderedAction):
            return value
        raise AssertionError(f"Action expression must resolve to action or nil: {expr!r}")
    return _resolve_runtime_symbol(program, store, expr, expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)


def _resolve_runtime_symbol(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    expr: SexpNode,
    *,
    expected_kind: str,
    scene_path: tuple[str, ...],
    source_index: int = 0,
) -> int | bool | str | None | ClockRef | RenderedScene | RenderedAction:
    if isinstance(expr, StringAtom):
        assert expected_kind == EXPR_KIND_VALUE, f"String literal is only valid in value contexts: {expr!r}"
        return expr.value
    if isinstance(expr, bool):
        assert expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}, f"Bool literal is not valid here: {expr!r}"
        return expr
    if isinstance(expr, int):
        assert expected_kind == EXPR_KIND_VALUE, f"Int literal is only valid in value contexts: {expr!r}"
        return expr
    symbol = _symbol(expr)
    if expected_kind == EXPR_KIND_CLOCK_REF:
        if symbol == "nil":
            return None
        bound = program.bindings.get(symbol)
        if bound is not None:
            return _eval_expr(program, store, bound, expected_kind=EXPR_KIND_CLOCK_REF, scene_path=scene_path, source_index=source_index)
        assert symbol in program.clocks_by_id, f"Unknown encounter clock ref: {symbol}"
        return ClockRef(symbol)
    if symbol == "nil":
        return None
    if symbol in store:
        spec = program.store_specs[symbol]
        assert expected_kind == EXPR_KIND_VALUE, f"Store symbol is only valid in value contexts: {symbol}"
        assert spec.kind != "clock", f"Clock value must be read explicitly via (clock-value {symbol})."
        return store[symbol]
    if symbol in program.bindings:
        return _eval_expr(program, store, program.bindings[symbol], expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)
    raise AssertionError(f"Unknown symbol in {expected_kind} context: {symbol}")


def _eval_condition(program: CompiledEncounterProgram, store: dict[str, int | bool | str], expr: SexpNode, *, scene_path: tuple[str, ...]) -> bool:
    value = _eval_expr(program, store, expr, expected_kind=EXPR_KIND_BOOL, scene_path=scene_path)
    assert isinstance(value, bool), f"Condition must resolve to bool: {expr!r}"
    return value


def _eval_value(program: CompiledEncounterProgram, store: dict[str, int | bool | str], expr: SexpNode, *, scene_path: tuple[str, ...]) -> int | bool | str:
    value = _eval_expr(program, store, expr, expected_kind=EXPR_KIND_VALUE, scene_path=scene_path)
    assert not isinstance(value, (ClockRef, RenderedScene, RenderedAction)), f"Value expression cannot resolve to object: {expr!r}"
    assert value is not None, f"Value expression cannot resolve to nil: {expr!r}"
    return value


def _build_scene(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    form: list[SexpNode],
    *,
    scene_path: tuple[str, ...],
) -> RenderedScene:
    fields = _field_map(form[1:], allowed={"id", "title", "desc", "show-clocks", "actions", "children"})
    scene_id = _static_symbol(fields["id"][0], program.bindings)
    title = _static_string(fields["title"][0], program.bindings)
    description = _static_string(fields["desc"][0], program.bindings)
    path = (*scene_path, scene_id)
    shown_clock_ids = tuple(
        clock_id.id
        for clock_id in (
            _eval_expr(program, store, item, expected_kind=EXPR_KIND_CLOCK_REF, scene_path=path)
            for item in fields.get("show-clocks", ())
        )
        if clock_id is not None
    )
    rendered_actions: list[RenderedAction] = []
    for source_index, item in enumerate(fields.get("actions", ())):
        rendered = _eval_action_expr(program, store, item, scene_path=path, source_index=source_index)
        if rendered is not None:
            rendered_actions.append(rendered)
    rendered_children: list[RenderedScene] = []
    for child_expr in fields.get("children", ()):
        child = _eval_scene_expr(program, store, child_expr, scene_path=path)
        if child is not None:
            rendered_children.append(child)
    root = LocationNode(
        id=scene_id,
        title=title,
        description=description,
        actions=tuple(item.action for item in rendered_actions),
        children=tuple(child.root for child in rendered_children),
    )
    return RenderedScene(
        scene_id=scene_id,
        root=root,
        shown_clock_ids=shown_clock_ids,
        actions=tuple(rendered_actions),
        children=tuple(rendered_children),
    )


def _build_action(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    form: list[SexpNode],
    *,
    scene_path: tuple[str, ...],
    source_index: int,
) -> RenderedAction:
    head = _symbol(form[0])
    action_key = f"inline:{head}:{hashlib.sha1(repr(form).encode('utf-8')).hexdigest()[:10]}"
    action_id = f"{program.id}:{'/'.join(scene_path)}:{source_index}:{action_key}"
    if head == "action":
        fields = _field_map(form[1:], allowed={"title", "desc", "before"})
        action_def = ActionDef(
            id=action_id,
            title=_static_string(fields["title"][0], program.bindings),
            description=_static_string(fields["desc"][0], program.bindings),
            screen=ScreenName.ENCOUNTER,
            effects=tuple(_compile_effect(effect_form, program.store_specs) for effect_form in fields.get("before", ())),
        )
    else:
        fields = _field_map(form[1:], allowed={"title", "desc", "suits", "risk", "before", "ok", "partial", "fail"})
        suits = tuple(SUIT_BY_NAME[_symbol(item)] for item in fields["suits"])
        risk_expr = fields["risk"][0]
        risk_name = _symbol_or_literal(risk_expr)
        risk = RISK_BY_NAME[risk_name]
        outcomes = {
            "success": _compile_outcome(fields["ok"], program.store_specs, program.bindings),
            "cost": _compile_outcome(fields["partial"], program.store_specs, program.bindings),
            "fail": _compile_outcome(fields["fail"], program.store_specs, program.bindings),
        }
        action_def = ActionDef(
            id=action_id,
            title=_static_string(fields["title"][0], program.bindings),
            description=_static_string(fields["desc"][0], program.bindings),
            screen=ScreenName.ENCOUNTER,
            effects=tuple(_compile_effect(effect_form, program.store_specs) for effect_form in fields.get("before", ())),
            check=CheckDef(
                suits=suits,
                risk=risk,
                success=outcomes["success"],
                cost=outcomes["cost"],
                fail=outcomes["fail"],
            ),
        )
    handle = ActionHandle(
        action_id=action_id,
        scene_path=scene_path,
        slot_index=source_index,
        action_key=action_key,
    )
    return RenderedAction(handle=handle, action=replace(action_def, id=action_id))


def _compile_outcome(parts: tuple[SexpNode, ...], store_specs: dict[str, StoreFieldSpec], bindings: dict[str, SexpNode]) -> OutcomeDef:
    assert parts, "Outcome field must not be empty."
    text = _static_string(parts[0], bindings)
    effects = tuple(_compile_effect(effect_form, store_specs) for effect_form in parts[1:])
    return OutcomeDef(text=text, effects=effects)


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


def _validate_expr(
    program: CompiledEncounterProgram,
    expr: SexpNode,
    *,
    expected_kind: str,
    scene_ids: set[str],
    scene_path: tuple[str, ...],
) -> None:
    if isinstance(expr, list):
        head = _symbol(expr[0])
        if head == "quote":
            assert expected_kind == EXPR_KIND_VALUE, "`quote` is only valid in value expressions."
            return
        if head == "if":
            assert len(expr) == 4, "Expr if-expression must be `(if condition then else)`."
            _validate_expr(program, expr[1], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path)
            _validate_expr(program, expr[2], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path)
            _validate_expr(program, expr[3], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head == "when":
            assert len(expr) == 3, "Expr when-expression must be `(when condition expr)`."
            assert expected_kind in {EXPR_KIND_CLOCK_REF, EXPR_KIND_SCENE, EXPR_KIND_ACTION}, "`when` is only valid in clock-ref/scene/action contexts."
            _validate_expr(program, expr[1], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path)
            _validate_expr(program, expr[2], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head == "cond":
            for clause in expr[1:]:
                clause_items = _list(clause)
                assert len(clause_items) == 2, "Each cond clause must be `(condition expr)`."
                if not (isinstance(clause_items[0], str) and clause_items[0] == "else"):
                    _validate_expr(program, clause_items[0], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path)
                _validate_expr(program, clause_items[1], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head in {"and", "or"}:
            assert expected_kind == EXPR_KIND_BOOL, f"`{head}` is only valid in bool expressions."
            for item in expr[1:]:
                _validate_expr(program, item, expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head == "not":
            assert expected_kind == EXPR_KIND_BOOL, "`not` is only valid in bool expressions."
            assert len(expr) == 2, "`not` expects exactly one operand."
            _validate_expr(program, expr[1], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head in {"=", "<", "<=", ">", ">="}:
            assert expected_kind == EXPR_KIND_BOOL, f"`{head}` is only valid in bool expressions."
            assert len(expr) == 3, f"`{head}` expects exactly two operands."
            _validate_expr(program, expr[1], expected_kind=EXPR_KIND_VALUE, scene_ids=scene_ids, scene_path=scene_path)
            _validate_expr(program, expr[2], expected_kind=EXPR_KIND_VALUE, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head in {"+", "-", "min", "max"}:
            assert expected_kind == EXPR_KIND_VALUE, f"`{head}` is only valid in scalar expressions."
            for item in expr[1:]:
                _validate_expr(program, item, expected_kind=EXPR_KIND_VALUE, scene_ids=scene_ids, scene_path=scene_path)
            return
        if head in {"clock-value", "clock-full", "clock-half"}:
            assert expected_kind == EXPR_KIND_VALUE, f"`{head}` is only valid in value expressions."
            assert len(expr) == 2, f"{head} expects exactly one clock id."
            clock_id = _symbol(expr[1])
            assert clock_id in program.clocks_by_id, f"Unknown encounter clock in value expression: {clock_id}"
            return
        if head == "scene":
            assert expected_kind == EXPR_KIND_SCENE, "`scene` is only valid in scene contexts."
            fields = _field_map(expr[1:], allowed={"id", "title", "desc", "show-clocks", "actions", "children"})
            scene_id = _static_symbol(fields["id"][0], program.bindings)
            assert scene_id not in scene_ids, f"Duplicate encounter scene id: {scene_id}"
            scene_ids.add(scene_id)
            nested_path = (*scene_path, scene_id)
            for item in fields.get("show-clocks", ()):
                _validate_expr(program, item, expected_kind=EXPR_KIND_CLOCK_REF, scene_ids=scene_ids, scene_path=nested_path)
            for item in fields.get("actions", ()):
                _validate_expr(program, item, expected_kind=EXPR_KIND_ACTION, scene_ids=scene_ids, scene_path=nested_path)
            for item in fields.get("children", ()):
                _validate_expr(program, item, expected_kind=EXPR_KIND_SCENE, scene_ids=scene_ids, scene_path=nested_path)
            return
        if head in {"action", "check"}:
            assert expected_kind == EXPR_KIND_ACTION, f"`{head}` is only valid in action contexts."
            _validate_action_form(program, expr)
            return
        raise AssertionError(f"Unsupported {expected_kind} expression: {expr}")
    if isinstance(expr, (int, bool, StringAtom)):
        assert expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}, f"Literal is not valid in {expected_kind} context: {expr!r}"
        return
    symbol = _symbol(expr)
    if expected_kind == EXPR_KIND_CLOCK_REF:
        if symbol == "nil":
            return
        if symbol in program.bindings:
            _validate_expr(program, program.bindings[symbol], expected_kind=EXPR_KIND_CLOCK_REF, scene_ids=scene_ids, scene_path=scene_path)
            return
        assert symbol in program.clocks_by_id, f"Unknown encounter clock ref: {symbol}"
        return
    if symbol == "nil":
        assert expected_kind in {EXPR_KIND_ACTION, EXPR_KIND_SCENE}, "`nil` is only valid in object/clock-ref contexts."
        return
    if symbol in program.store_specs:
        assert expected_kind == EXPR_KIND_VALUE, f"Store symbol is only valid in value contexts: {symbol}"
        spec = program.store_specs[symbol]
        assert spec.kind != "clock", f"Clock value must be read explicitly via (clock-value {symbol})."
        return
    if symbol in program.bindings:
        _validate_expr(program, program.bindings[symbol], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path)
        return
    raise AssertionError(f"Unknown symbol in {expected_kind} context: {symbol}")


def _validate_action_form(program: CompiledEncounterProgram, expr: list[SexpNode]) -> None:
    head = _symbol(expr[0])
    if head == "action":
        _field_map(expr[1:], allowed={"title", "desc", "before"})
        return
    fields = _field_map(expr[1:], allowed={"title", "desc", "suits", "risk", "before", "ok", "partial", "fail"})
    assert fields.get("suits"), "Check action missing suits."
    assert fields.get("risk"), "Check action missing risk."
    for outcome_head in ("ok", "partial", "fail"):
        assert fields.get(outcome_head), f"Check action missing outcome: {outcome_head}"
        assert fields[outcome_head], f"Outcome field cannot be empty: {outcome_head}"


def _macroexpand(node: SexpNode, macros: dict[str, MacroTemplate]) -> SexpNode:
    if not isinstance(node, list):
        return node
    if not node:
        return node
    head_node = node[0]
    if isinstance(head_node, str) and head_node in macros:
        template = macros[head_node]
        assert len(node) - 1 == len(template.params), f"Wrong arity for macro {template.name}: {len(node) - 1}"
        bindings = {param: arg for param, arg in zip(template.params, node[1:], strict=True)}
        expanded = _substitute_macro(template.body, bindings)
        if _is_symbol_list(expanded, "quote"):
            return _list(expanded)[1]
        return _macroexpand(expanded, macros)
    return [_macroexpand(item, macros) for item in node]


def _substitute_macro(node: SexpNode, bindings: dict[str, SexpNode]) -> SexpNode:
    if isinstance(node, list):
        if _is_symbol_list(node, "quote"):
            return node
        return [_substitute_macro(item, bindings) for item in node]
    if isinstance(node, str) and node in bindings:
        return bindings[node]
    return node


def _field_map(forms: list[SexpNode], *, allowed: set[str]) -> dict[str, tuple[SexpNode, ...]]:
    fields: dict[str, tuple[SexpNode, ...]] = {}
    for field in forms:
        items = _list(field)
        head = _symbol(items[0])
        assert head in allowed, f"Unsupported field: {head}"
        assert head not in fields, f"Duplicate field: {head}"
        fields[head] = tuple(items[1:])
    return fields


def _clock_full_value(program: CompiledEncounterProgram, clock_id: str) -> int:
    spec = program.store_specs[clock_id]
    assert spec.kind == "clock" and spec.maximum is not None, f"clock-full target must be a clock: {clock_id}"
    return spec.maximum


def _clock_half_value(program: CompiledEncounterProgram, clock_id: str) -> int:
    spec = program.store_specs[clock_id]
    assert spec.kind == "clock" and spec.maximum is not None, f"clock-half target must be a clock: {clock_id}"
    return (spec.maximum + 1) // 2


def _clock_current_value(program: CompiledEncounterProgram, store: dict[str, int | bool | str], clock_id: str) -> int:
    spec = program.store_specs[clock_id]
    assert spec.kind == "clock", f"clock-value target must be a clock: {clock_id}"
    value = store[clock_id]
    assert isinstance(value, int), f"clock-value must resolve to int: {clock_id}"
    return value


def _static_atom(node: SexpNode, bindings: dict[str, SexpNode]) -> int | bool | str:
    if _is_symbol_list(node, "quote"):
        return _quoted_atom(_list(node)[1])
    if isinstance(node, StringAtom):
        return node.value
    if isinstance(node, (int, bool)):
        return node
    symbol = _symbol(node)
    if symbol == "nil":
        return "nil"
    if symbol in bindings:
        return _static_atom(bindings[symbol], bindings)
    return symbol


def _static_int(node: SexpNode, bindings: dict[str, SexpNode]) -> int:
    value = _static_atom(node, bindings)
    if isinstance(value, int):
        return value
    return int(value)


def _static_bool(node: SexpNode, bindings: dict[str, SexpNode]) -> bool:
    value = _static_atom(node, bindings)
    assert isinstance(value, bool), f"Expected bool literal, got: {value!r}"
    return value


def _static_string(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    value = _static_atom(node, bindings)
    assert isinstance(value, str), f"Expected string literal, got: {value!r}"
    return value


def _static_symbol(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    if _is_symbol_list(node, "quote"):
        value = _quoted_atom(_list(node)[1])
        assert isinstance(value, str), f"Expected quoted symbol, got: {value!r}"
        return value
    if isinstance(node, StringAtom):
        return node.value
    symbol = _symbol(node)
    if symbol in bindings:
        return _static_symbol(bindings[symbol], bindings)
    return symbol


def _quoted_atom(node: SexpNode) -> int | bool | str | None:
    if isinstance(node, StringAtom):
        return node.value
    if isinstance(node, bool):
        return node
    if isinstance(node, int):
        return node
    if isinstance(node, str):
        return None if node == "nil" else node
    raise AssertionError(f"quote currently supports only atom literals, got: {node!r}")


def _symbol_or_literal(node: SexpNode) -> str:
    if _is_symbol_list(node, "quote"):
        value = _quoted_atom(_list(node)[1])
        assert isinstance(value, str), f"Expected quoted symbol literal, got: {value!r}"
        return value
    if isinstance(node, StringAtom):
        return node.value
    return _symbol(node)


def _is_symbol_list(node: SexpNode, head: str) -> bool:
    return isinstance(node, list) and bool(node) and isinstance(node[0], str) and node[0] == head


def _form_head(node: SexpNode) -> str:
    if isinstance(node, list) and node and isinstance(node[0], str):
        return node[0]
    return repr(node)


def _list(node: SexpNode) -> list[SexpNode]:
    assert isinstance(node, list), f"Expected list form, got: {node!r}"
    return node


def _symbol(node: SexpNode) -> str:
    assert isinstance(node, str) and not isinstance(node, StringAtom), f"Expected symbol, got: {node!r}"
    return node


def _signed_int(node: SexpNode) -> int:
    if isinstance(node, int):
        return node
    token = _symbol(node)
    if token.startswith("+") or token.startswith("-"):
        return int(token)
    return int(token)


def _atom_value(node: SexpNode) -> int | bool | str | None:
    if _is_symbol_list(node, "quote"):
        return _quoted_atom(_list(node)[1])
    if isinstance(node, StringAtom):
        return node.value
    if isinstance(node, bool):
        return node
    if isinstance(node, int):
        return node
    if isinstance(node, str):
        return None if node == "nil" else node
    raise AssertionError(f"Expected atom, got: {node!r}")
