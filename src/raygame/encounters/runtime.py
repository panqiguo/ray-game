from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from raygame.encounters.defs import (
    ActionHandle,
    ClockRef,
    CompiledEncounterProgram,
    EncounterCompileError,
    MacroTemplate,
    ReactRule,
    RenderedAction,
    RenderedEncounter,
    RenderedScene,
    SexpNode,
    StoreSlotRef,
    StoreFieldSpec,
    StringAtom,
)
from raygame.encounters.sexp import parse_sexp
from raygame.model.defs import ActionDef, CheckDef, Effect, InputRequirement, LocationNode, OutcomeDef, ProgressClockSpec
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


def compile_encounter_program(source: str, *, source_path: str | Path | None = None) -> CompiledEncounterProgram:
    try:
        return _compile_encounter_program_impl(source, source_path=Path(source_path) if source_path is not None else None)
    except EncounterCompileError:
        raise
    except AssertionError as exc:
        raise EncounterCompileError(str(exc)) from exc


def _compile_encounter_program_impl(source: str, *, source_path: Path | None) -> CompiledEncounterProgram:
    forms = _load_module_forms(source, source_path=source_path, include_stack=())
    bindings: dict[str, SexpNode] = {}
    macros: dict[str, MacroTemplate] = {}
    last_value: CompiledEncounterProgram | None = None
    for form in forms:
        expanded = _macroexpand(form, macros)
        if _is_symbol_list(expanded, "include"):
            raise AssertionError("`include` is only valid before macro expansion flattening.")
        if _is_symbol_list(expanded, "def"):
            _eval_def(expanded, bindings)
            continue
        if _is_symbol_list(expanded, "defmacro"):
            template = _eval_defmacro(expanded)
            macros[template.name] = template
            continue
        if _is_symbol_list(expanded, "encounter"):
            assert last_value is None, "Encounter file must evaluate to exactly one encounter after includes are expanded."
            last_value = _compile_encounter_form(expanded, bindings=bindings, macros=macros)
            continue
        raise AssertionError(f"Unsupported top-level form: {_form_head(expanded)}")
    assert last_value is not None, "Encounter file must evaluate to an Encounter."
    return last_value


def _load_module_forms(source: str, *, source_path: Path | None, include_stack: tuple[Path, ...]) -> list[SexpNode]:
    forms = parse_sexp(source)
    expanded: list[SexpNode] = []
    for index, form in enumerate(forms):
        if _is_symbol_list(form, "include"):
            include_items = _list(form)
            assert len(include_items) == 2, "`include` expects exactly one path string."
            assert source_path is not None, "`include` requires the encounter to be loaded from a file path."
            include_node = include_items[1]
            assert isinstance(include_node, StringAtom), "`include` path must be a string literal."
            include_path = (source_path.parent / include_node.value).resolve()
            assert include_path.exists(), f"Included encounter file does not exist: {include_node.value}"
            assert include_path not in include_stack, f"Cyclic include detected: {include_path}"
            include_source = include_path.read_text(encoding="utf-8")
            include_forms = _load_module_forms(include_source, source_path=include_path, include_stack=(*include_stack, include_path))
            expanded.extend(include_forms)
            continue
        expanded.append(form)
    return expanded


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
    try:
        _validate_encounter_program_impl(program)
    except EncounterCompileError:
        raise
    except AssertionError as exc:
        raise EncounterCompileError(f"{program.id}: {exc}") from exc


def _validate_encounter_program_impl(program: CompiledEncounterProgram) -> None:
    scene_ids: set[str] = set()
    for name, value in program.bindings.items():
        if isinstance(value, list) and value:
            head = _form_head(value)
            if head == "action":
                _validate_expr(program, value, expected_kind=EXPR_KIND_ACTION, scene_ids=scene_ids, scene_path=(), context=f"binding {name}")
    for index, rule in enumerate(program.react_rules):
        _validate_expr(program, rule.condition, expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=(), context=f"reacts[{index}].condition")
    _validate_expr(program, program.view_expr, expected_kind=EXPR_KIND_SCENE, scene_ids=scene_ids, scene_path=(), context="view")


def _eval_def(form: list[SexpNode], bindings: dict[str, SexpNode]) -> None:
    assert len(form) == 3, "`def` expects exactly two arguments."
    name = _identifier(form[1])
    bindings[name] = form[2]


def _eval_defmacro(form: list[SexpNode]) -> MacroTemplate:
    if len(form) == 4:
        name = _identifier(form[1])
        params = tuple(_identifier(item) for item in _list(form[2]))
        body = form[3]
        return MacroTemplate(name=name, params=params, body=body)
    assert len(form) == 3, "`defmacro` expects `(defmacro name (params...) body)` or `(defmacro (name params...) body)`."
    signature = _list(form[1])
    assert signature, "`defmacro` signature must be non-empty."
    name = _identifier(signature[0])
    params = tuple(_identifier(item) for item in signature[1:])
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
    for index, field in enumerate(field_forms):
        try:
            items = _list(field)
            head = _identifier(items[0])
            if head == "id":
                encounter_id = _identifier_or_bound_symbol(items[1], bindings)
            elif head == "title":
                title = _static_string(items[1], bindings)
            elif head == "desc":
                description = _static_string(items[1], bindings)
            elif head == "reward":
                rewards = tuple(_compile_effect(effect_form, store_specs, bindings) for effect_form in items[1:])
            elif head == "fail":
                fail_effects = tuple(_compile_effect(effect_form, store_specs, bindings) for effect_form in items[1:])
            elif head == "store":
                for spec_index, spec_form in enumerate(items[1:]):
                    try:
                        spec = _compile_store_field(_list(spec_form), bindings)
                        assert spec.id not in store_specs, f"Duplicate encounter store field: {spec.id}"
                        store_specs[spec.id] = spec
                        if spec.kind == "clock":
                            assert isinstance(spec.initial, int) and isinstance(spec.maximum, int)
                            clocks_by_id[spec.id] = ProgressClockSpec(id=spec.id, title=spec.title, segments=spec.maximum)
                    except AssertionError as exc:
                        raise EncounterCompileError(f"encounter.store[{spec_index}]: {exc}") from exc
            elif head == "reacts":
                for react_index, rule_form in enumerate(items[1:]):
                    try:
                        rule_items = _list(rule_form)
                        assert len(rule_items) >= 2, "React rule must contain condition and at least one effect."
                        react_rules.append(
                            ReactRule(
                                condition=rule_items[0],
                                effects=tuple(_compile_effect(effect_form, store_specs, bindings) for effect_form in rule_items[1:]),
                                source=f"react[{react_index}]",
                            )
                        )
                    except AssertionError as exc:
                        raise EncounterCompileError(f"encounter.reacts[{react_index}]: {exc}") from exc
            elif head == "view":
                assert len(items) == 2, "`view` expects exactly one scene expression."
                view_expr = items[1]
            else:
                raise AssertionError(f"Unsupported encounter field: {head}")
        except EncounterCompileError:
            raise
        except AssertionError as exc:
            raise EncounterCompileError(f"encounter.field[{index}]: {exc}") from exc
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
    assert len(form) == 2, "Each store binding must be `(name expr)`."
    field_id = _identifier(form[0])
    return _compile_store_value(field_id, form[1], bindings)


def _compile_store_value(field_id: str, expr: SexpNode, bindings: dict[str, SexpNode]) -> StoreFieldSpec:
    if isinstance(expr, str) and expr in bindings:
        return _compile_store_value(field_id, bindings[expr], bindings)
    if isinstance(expr, list):
        items = _list(expr)
        head = _identifier(items[0])
        if head == "clock":
            assert len(items) == 4, "`clock` expects `(clock title initial maximum)`."
            title = _static_string(items[1], bindings)
            initial = _static_int(items[2], bindings)
            maximum = _static_int(items[3], bindings)
            assert 0 <= initial <= maximum, f"Clock initial out of range: {field_id}"
            return StoreFieldSpec(id=field_id, kind="clock", initial=initial, title=title, maximum=maximum)
    return StoreFieldSpec(id=field_id, kind="value", initial=_static_atom(expr, bindings))


def _compile_effect(form: SexpNode, store_specs: dict[str, StoreFieldSpec], bindings: dict[str, SexpNode]) -> Effect:
    items = _list(form)
    head = _identifier(items[0])
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
        field_id = _identifier(items[1])
        assert field_id in store_specs, f"Unknown encounter store field: {field_id}"
        return Effect(kind="set_encounter_store", value=f"{field_id}:{_effect_value_token(items[2], bindings)}")
    if head == "finish":
        return Effect(kind="finish_encounter", value=_literal_string_or_symbol(items[1], bindings))
    raise AssertionError(f"Unsupported encounter effect: {head}")


def _effect_value_token(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    value = _literal_value(node, bindings)
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
        head = _identifier(expr[0])
        if head == "quote":
            assert len(expr) == 2, "`quote` expects exactly one argument."
            return _quoted_atom(expr[1])
        if head == "if":
            assert len(expr) == 4, "Expr if-expression must be `(if condition then else)`."
            branch = expr[2] if _eval_condition(program, store, expr[1], scene_path=scene_path) else expr[3]
            return _eval_expr(program, store, branch, expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)
        if head == "when":
            assert len(expr) == 3, "Expr when-expression must be `(when condition expr)`."
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
            return _clock_current_value(program, store, _identifier(expr[1]))
        if head == "clock-full":
            assert expected_kind == EXPR_KIND_VALUE, "`clock-full` is only valid in value expressions."
            return _clock_full_value(program, _identifier(expr[1]))
        if head == "clock-half":
            assert expected_kind == EXPR_KIND_VALUE, "`clock-half` is only valid in value expressions."
            return _clock_half_value(program, _identifier(expr[1]))
        if head == "scene":
            assert expected_kind == EXPR_KIND_SCENE, "`scene` is only valid in scene contexts."
            return _build_scene(program, store, expr, scene_path=scene_path)
        if head == "action":
            assert expected_kind == EXPR_KIND_ACTION, "`action` is only valid in action contexts."
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
    if symbol == "nil":
        return None
    looked_up = _lookup_symbol(program, symbol)
    if looked_up is None:
        hint = f"Unknown symbol: {symbol}"
        if expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}:
            hint += f". If you meant a literal symbol, write '{symbol}"
        raise AssertionError(hint)
    if isinstance(looked_up, StoreSlotRef):
        spec = program.store_specs[looked_up.id]
        if spec.kind == "clock":
            if expected_kind == EXPR_KIND_CLOCK_REF:
                return ClockRef(looked_up.id)
            raise AssertionError(
                f"Symbol `{looked_up.id}` resolved to a clock. Use it directly only where a clock ref is expected, or read its current value with `(clock-value {looked_up.id})`."
            )
        assert expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}, (
            f"Symbol `{looked_up.id}` resolved to a store slot, but this context expects {_expected_kind_label(expected_kind)}."
        )
        value = store[looked_up.id]
        if expected_kind == EXPR_KIND_BOOL:
            assert isinstance(value, bool), f"Store slot {looked_up.id} does not resolve to bool."
        return value
    if isinstance(looked_up, ClockRef):
        assert expected_kind == EXPR_KIND_CLOCK_REF, (
            f"Symbol `{looked_up.id}` resolved to a clock ref, but this context expects {_expected_kind_label(expected_kind)}."
        )
        return looked_up
    return _eval_expr(program, store, looked_up, expected_kind=expected_kind, scene_path=scene_path, source_index=source_index)


def _lookup_symbol(program: CompiledEncounterProgram, symbol: str) -> SexpNode | ClockRef | StoreSlotRef | None:
    if symbol in program.bindings:
        return program.bindings[symbol]
    if symbol in program.store_specs:
        return StoreSlotRef(symbol)
    return None


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
    scene_id = _identifier_or_bound_symbol(fields["id"][0], program.bindings)
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
    head = _identifier(form[0])
    action_key = f"inline:{head}:{hashlib.sha1(repr(form).encode('utf-8')).hexdigest()[:10]}"
    action_id = f"{program.id}:{'/'.join(scene_path)}:{source_index}:{action_key}"
    fields = _field_map(form[1:], allowed={"title", "desc", "inputs", "before", "check"})
    check_block = fields.get("check")
    action_def = ActionDef(
        id=action_id,
        title=_static_string(fields["title"][0], program.bindings),
        description=_static_string(fields["desc"][0], program.bindings),
        screen=ScreenName.ENCOUNTER,
        inputs=_compile_inputs(fields.get("inputs", ()), program.bindings),
        effects=tuple(_compile_effect(effect_form, program.store_specs, program.bindings) for effect_form in fields.get("before", ())),
        check=_compile_check_block(check_block, program) if check_block else None,
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
    effects = tuple(_compile_effect(effect_form, store_specs, bindings) for effect_form in parts[1:])
    return OutcomeDef(text=text, effects=effects)


def _compile_check_block(parts: tuple[SexpNode, ...], program: CompiledEncounterProgram) -> CheckDef:
    fields = {head: tuple(items[1:]) for head, items in (
        (_identifier(_list(item)[0]), _list(item)) for item in parts
    )}
    suits = tuple(SUIT_BY_NAME[_literal_string_or_symbol(item, program.bindings)] for item in fields["suits"])
    risk_expr = fields["risk"][0]
    risk_name = _literal_string_or_symbol(risk_expr, program.bindings)
    risk = RISK_BY_NAME[risk_name]
    outcomes = {
        "success": _compile_outcome(fields["ok"], program.store_specs, program.bindings),
        "cost": _compile_outcome(fields["partial"], program.store_specs, program.bindings),
        "fail": _compile_outcome(fields["fail"], program.store_specs, program.bindings),
    }
    return CheckDef(
        suits=suits,
        risk=risk,
        success=outcomes["success"],
        cost=outcomes["cost"],
        fail=outcomes["fail"],
    )


def _compile_inputs(parts: tuple[SexpNode, ...], bindings: dict[str, SexpNode]) -> tuple[InputRequirement, ...]:
    return tuple(_compile_input(form, bindings) for form in parts)


def _compile_input(form: SexpNode, bindings: dict[str, SexpNode]) -> InputRequirement:
    items = _list(form)
    head = _identifier(items[0])
    if head == "resource":
        assert len(items) in {3, 4}, "`resource` input expects `(resource key amount [label])`."
        key = _identifier(items[1])
        amount = _static_int(items[2], bindings)
        label = _static_string(items[3], bindings) if len(items) == 4 else key
        return InputRequirement(kind="resource", key=key, amount=amount, label=label, consume=True)
    if head == "item":
        assert len(items) in {2, 3, 4, 5}, "`item` input expects `(item key [amount] [label] [consume])`."
        key = _identifier(items[1])
        amount = _static_int(items[2], bindings) if len(items) >= 3 else 1
        label = _static_string(items[3], bindings) if len(items) >= 4 else key
        consume = _static_bool(items[4], bindings) if len(items) == 5 else True
        return InputRequirement(kind="item", key=key, amount=amount, label=label, consume=consume)
    if head == "card":
        assert len(items) in {2, 3}, "`card` input expects `(card key [label])`."
        key = _identifier(items[1])
        assert key in {"any", "negative"}, f"Unsupported card input kind: {key}"
        label = _static_string(items[2], bindings) if len(items) == 3 else ("负面牌" if key == "negative" else "手牌")
        return InputRequirement(kind="card", key=key, amount=1, label=label, consume=True)
    raise AssertionError(f"Unsupported action input: {head}")


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
    context: str,
) -> None:
    try:
        if isinstance(expr, list):
            head = _symbol(expr[0])
            if head == "quote":
                assert expected_kind == EXPR_KIND_VALUE, "`quote` is only valid in value expressions."
                return
            if head == "if":
                assert len(expr) == 4, "Expr if-expression must be `(if condition then else)`."
                _validate_expr(program, expr[1], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.if-test")
                _validate_expr(program, expr[2], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.if-then")
                _validate_expr(program, expr[3], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.if-else")
                return
            if head == "when":
                assert len(expr) == 3, "Expr when-expression must be `(when condition expr)`."
                _validate_expr(program, expr[1], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.when-test")
                _validate_expr(program, expr[2], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.when-body")
                return
            if head == "cond":
                for index, clause in enumerate(expr[1:]):
                    clause_items = _list(clause)
                    assert len(clause_items) == 2, "Each cond clause must be `(condition expr)`."
                    if not (isinstance(clause_items[0], str) and clause_items[0] == "else"):
                        _validate_expr(program, clause_items[0], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.cond[{index}].test")
                    _validate_expr(program, clause_items[1], expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.cond[{index}].body")
                return
            if head in {"and", "or"}:
                assert expected_kind == EXPR_KIND_BOOL, f"`{head}` is only valid in bool expressions."
                for index, item in enumerate(expr[1:]):
                    _validate_expr(program, item, expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.{head}[{index}]")
                return
            if head == "not":
                assert expected_kind == EXPR_KIND_BOOL, "`not` is only valid in bool expressions."
                assert len(expr) == 2, "`not` expects exactly one operand."
                _validate_expr(program, expr[1], expected_kind=EXPR_KIND_BOOL, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.not")
                return
            if head in {"=", "<", "<=", ">", ">="}:
                assert expected_kind == EXPR_KIND_BOOL, f"`{head}` is only valid in bool expressions."
                assert len(expr) == 3, f"`{head}` expects exactly two operands."
                _validate_expr(program, expr[1], expected_kind=EXPR_KIND_VALUE, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.{head}.left")
                _validate_expr(program, expr[2], expected_kind=EXPR_KIND_VALUE, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.{head}.right")
                return
            if head in {"+", "-", "min", "max"}:
                assert expected_kind == EXPR_KIND_VALUE, f"`{head}` is only valid in scalar expressions."
                for index, item in enumerate(expr[1:]):
                    _validate_expr(program, item, expected_kind=EXPR_KIND_VALUE, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}.{head}[{index}]")
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
                for index, item in enumerate(fields.get("show-clocks", ())):
                    _validate_expr(program, item, expected_kind=EXPR_KIND_CLOCK_REF, scene_ids=scene_ids, scene_path=nested_path, context=f"{context}.show-clocks[{index}]")
                for index, item in enumerate(fields.get("actions", ())):
                    _validate_expr(program, item, expected_kind=EXPR_KIND_ACTION, scene_ids=scene_ids, scene_path=nested_path, context=f"{context}.actions[{index}]")
                for index, item in enumerate(fields.get("children", ())):
                    _validate_expr(program, item, expected_kind=EXPR_KIND_SCENE, scene_ids=scene_ids, scene_path=nested_path, context=f"{context}.children[{index}]")
                return
            if head == "action":
                assert expected_kind == EXPR_KIND_ACTION, "`action` is only valid in action contexts."
                _validate_action_form(program, expr, context=context)
                return
            raise AssertionError(f"Unsupported {expected_kind} expression: {expr}")
        if isinstance(expr, (int, bool, StringAtom)):
            assert expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}, f"Literal is not valid in {expected_kind} context: {expr!r}"
            return
        symbol = _symbol(expr)
        if symbol == "nil":
            assert expected_kind in {EXPR_KIND_ACTION, EXPR_KIND_SCENE, EXPR_KIND_CLOCK_REF}, "`nil` is only valid in object/clock-ref contexts."
            return
        looked_up = _lookup_symbol(program, symbol)
        if looked_up is None:
            hint = f"Unknown symbol: {symbol}"
            if expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}:
                hint += f". If you meant a literal symbol, write '{symbol}"
            raise AssertionError(hint)
        if isinstance(looked_up, StoreSlotRef):
            spec = program.store_specs[looked_up.id]
            if spec.kind == "clock":
                assert expected_kind == EXPR_KIND_CLOCK_REF, (
                    f"Symbol `{looked_up.id}` resolved to a clock. Use it directly only where a clock ref is expected, or read its current value with `(clock-value {looked_up.id})`."
                )
                return
            assert expected_kind in {EXPR_KIND_BOOL, EXPR_KIND_VALUE}, (
                f"Symbol `{looked_up.id}` resolved to a store slot, but this context expects {_expected_kind_label(expected_kind)}."
            )
            return
        if isinstance(looked_up, ClockRef):
            assert expected_kind == EXPR_KIND_CLOCK_REF, (
                f"Symbol `{looked_up.id}` resolved to a clock ref, but this context expects {_expected_kind_label(expected_kind)}."
            )
            return
        _validate_expr(program, looked_up, expected_kind=expected_kind, scene_ids=scene_ids, scene_path=scene_path, context=f"{context}->{symbol}")
        return
    except EncounterCompileError as exc:
        raise EncounterCompileError(f"{context}: {exc}") from exc
    except AssertionError as exc:
        raise EncounterCompileError(f"{context}: {exc}") from exc


def _validate_action_form(program: CompiledEncounterProgram, expr: list[SexpNode], *, context: str) -> None:
    try:
        assert _symbol(expr[0]) == "action", "Only `action` forms are valid in action contexts."
        fields = _field_map(expr[1:], allowed={"title", "desc", "inputs", "before", "check"})
        for index, input_form in enumerate(fields.get("inputs", ())):
            try:
                _compile_input(input_form, program.bindings)
            except AssertionError as exc:
                raise EncounterCompileError(f"{context}.inputs[{index}]: {exc}") from exc
        for index, effect_form in enumerate(fields.get("before", ())):
            try:
                _compile_effect(effect_form, program.store_specs, program.bindings)
            except AssertionError as exc:
                raise EncounterCompileError(f"{context}.before[{index}]: {exc}") from exc
        check_parts = fields.get("check")
        if not check_parts:
            return
        check_fields = {head: tuple(items[1:]) for head, items in (
            (_symbol(_list(item)[0]), _list(item)) for item in check_parts
        )}
        assert check_fields.get("suits"), "Check action missing suits."
        assert check_fields.get("risk"), "Check action missing risk."
        for outcome_head in ("ok", "partial", "fail"):
            assert check_fields.get(outcome_head), f"Check action missing outcome: {outcome_head}"
            assert check_fields[outcome_head], f"Outcome field cannot be empty: {outcome_head}"
            outcome_parts = check_fields[outcome_head]
            try:
                _static_string(outcome_parts[0], program.bindings)
            except AssertionError as exc:
                raise EncounterCompileError(f"{context}.check.{outcome_head}.text: {exc}") from exc
            for effect_index, effect_form in enumerate(outcome_parts[1:]):
                try:
                    _compile_effect(effect_form, program.store_specs, program.bindings)
                except AssertionError as exc:
                    raise EncounterCompileError(f"{context}.check.{outcome_head}[{effect_index}]: {exc}") from exc
    except EncounterCompileError:
        raise
    except AssertionError as exc:
        raise EncounterCompileError(f"{context}: {exc}") from exc


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


def _expected_kind_label(expected_kind: str) -> str:
    return {
        EXPR_KIND_BOOL: "a bool expression",
        EXPR_KIND_VALUE: "a value expression",
        EXPR_KIND_CLOCK_REF: "a clock ref",
        EXPR_KIND_SCENE: "a scene",
        EXPR_KIND_ACTION: "an action",
    }[expected_kind]


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


def _literal_value(node: SexpNode, bindings: dict[str, SexpNode]) -> int | bool | str | None:
    if _is_symbol_list(node, "quote"):
        return _quoted_atom(_list(node)[1])
    if isinstance(node, StringAtom):
        return node.value
    if isinstance(node, (int, bool)):
        return node
    symbol = _identifier(node)
    if symbol in bindings:
        return _literal_value(bindings[symbol], bindings)
    raise AssertionError(f"Unknown symbol literal: {symbol}. If you meant a literal symbol, write '{symbol}")


def _literal_atom(node: SexpNode, bindings: dict[str, SexpNode]) -> int | bool | str:
    value = _literal_value(node, bindings)
    assert value is not None, "nil is not valid here."
    return value


def _static_int(node: SexpNode, bindings: dict[str, SexpNode]) -> int:
    value = _literal_atom(node, bindings)
    if isinstance(value, int):
        return value
    return int(value)


def _static_bool(node: SexpNode, bindings: dict[str, SexpNode]) -> bool:
    value = _literal_atom(node, bindings)
    assert isinstance(value, bool), f"Expected bool literal, got: {value!r}"
    return value


def _static_string(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    value = _literal_atom(node, bindings)
    assert isinstance(value, str), f"Expected string literal, got: {value!r}"
    return value


def _identifier_or_bound_symbol(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    if _is_symbol_list(node, "quote"):
        value = _quoted_atom(_list(node)[1])
        assert isinstance(value, str), f"Expected quoted symbol, got: {value!r}"
        return value
    if isinstance(node, StringAtom):
        return node.value
    symbol = _identifier(node)
    if symbol in bindings:
        return _identifier_or_bound_symbol(bindings[symbol], bindings)
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


def _literal_string_or_symbol(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    if _is_symbol_list(node, "quote"):
        value = _quoted_atom(_list(node)[1])
        assert isinstance(value, str), f"Expected quoted symbol literal, got: {value!r}"
        return value
    if isinstance(node, StringAtom):
        return node.value
    symbol = _identifier(node)
    if symbol in bindings:
        value = _literal_value(bindings[symbol], bindings)
        assert isinstance(value, str), f"Expected symbol/string literal binding, got: {value!r}"
        return value
    raise AssertionError(f"Unknown symbol literal: {symbol}. If you meant a literal symbol, write '{symbol}")


def _is_symbol_list(node: SexpNode, head: str) -> bool:
    return isinstance(node, list) and bool(node) and isinstance(node[0], str) and node[0] == head


def _form_head(node: SexpNode) -> str:
    if isinstance(node, list) and node and isinstance(node[0], str):
        return node[0]
    return repr(node)


def _list(node: SexpNode) -> list[SexpNode]:
    assert isinstance(node, list), f"Expected list form, got: {node!r}"
    return node


def _identifier(node: SexpNode) -> str:
    assert isinstance(node, str) and not isinstance(node, StringAtom), f"Expected symbol, got: {node!r}"
    return node


def _static_literal(node: SexpNode, bindings: dict[str, SexpNode]) -> int | bool | str | None:
    return _literal_value(node, bindings)


def _static_atom(node: SexpNode, bindings: dict[str, SexpNode]) -> int | bool | str:
    return _literal_atom(node, bindings)


def _static_symbol(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    return _identifier_or_bound_symbol(node, bindings)


def _literal_symbol_or_string(node: SexpNode, bindings: dict[str, SexpNode]) -> str:
    return _literal_string_or_symbol(node, bindings)


def _symbol(node: SexpNode) -> str:
    return _identifier(node)


def _signed_int(node: SexpNode) -> int:
    if isinstance(node, int):
        return node
    token = _symbol(node)
    if token.startswith("+") or token.startswith("-"):
        return int(token)
    return int(token)
