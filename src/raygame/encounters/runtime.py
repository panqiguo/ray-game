from __future__ import annotations

import hashlib
from dataclasses import replace

from raygame.encounters.defs import (
    ActionHandle,
    ActionTemplate,
    CompiledEncounterProgram,
    ReactRule,
    RenderedAction,
    RenderedEncounter,
    RenderedScene,
    SexpNode,
    StoreFieldSpec,
)
from raygame.encounters.sexp import parse_sexp
from raygame.model.defs import ActionDef, CheckDef, Effect, LocationNode, OutcomeDef, ProgressClockSpec
from raygame.model.enums import Risk, ScreenName, Suit


MAX_REACT_STEPS = 64
REACT_EFFECT_KINDS = {"advance_encounter_clock", "damage_encounter_clock", "set_encounter_store", "finish_encounter"}
RISK_BY_NAME = {"low": Risk.LOW, "mid": Risk.MID, "high": Risk.HIGH}
SUIT_BY_NAME = {
    "reason": Suit.REASON,
    "force": Suit.FORCE,
    "empathy": Suit.EMPATHY,
    "instinct": Suit.INSTINCT,
}


def compile_encounter_program(source: str) -> CompiledEncounterProgram:
    forms = parse_sexp(source)
    assert len(forms) == 1 and isinstance(forms[0], list), "Encounter source must contain exactly one top-level form."
    root = forms[0]
    assert root and root[0] == "encounter", "Top-level form must be `(encounter ...)`."
    encounter_id = _symbol(root[1])
    title = ""
    description = ""
    rewards: tuple[Effect, ...] = ()
    fail_effects: tuple[Effect, ...] = ()
    store_specs: dict[str, StoreFieldSpec] = {}
    clocks_by_id: dict[str, ProgressClockSpec] = {}
    action_templates: dict[str, ActionTemplate] = {}
    react_rules: list[ReactRule] = []
    view_expr: SexpNode | None = None
    for item in root[2:]:
        form = _list(item)
        head = _symbol(form[0])
        if head == "title":
            title = _string(form[1])
        elif head == "desc":
            description = _string(form[1])
        elif head == "reward":
            rewards = tuple(_compile_effect(effect_form, store_specs) for effect_form in form[1:])
        elif head == "fail":
            fail_effects = tuple(_compile_effect(effect_form, store_specs) for effect_form in form[1:])
        elif head == "store":
            for spec_form in form[1:]:
                spec = _compile_store_field(_list(spec_form))
                assert spec.id not in store_specs, f"Duplicate encounter store field: {spec.id}"
                store_specs[spec.id] = spec
                if spec.kind == "clock":
                    assert isinstance(spec.initial, int) and isinstance(spec.maximum, int)
                    clocks_by_id[spec.id] = ProgressClockSpec(
                        id=spec.id,
                        title=spec.title,
                        segments=spec.maximum,
                    )
        elif head == "defs":
            for def_form in form[1:]:
                template = _compile_defaction(_list(def_form))
                assert template.name not in action_templates, f"Duplicate defaction: {template.name}"
                action_templates[template.name] = template
        elif head == "reacts":
            for index, rule_form in enumerate(form[1:]):
                rule_list = _list(rule_form)
                assert len(rule_list) >= 2, "React rule must contain condition and at least one effect."
                compiled_effects = tuple(_compile_effect(effect_form, store_specs) for effect_form in rule_list[1:])
                for effect in compiled_effects:
                    assert effect.kind in REACT_EFFECT_KINDS, (
                        f"React only supports store/finish effects, got {effect.kind} in react[{index}]"
                    )
                react_rules.append(
                    ReactRule(
                        condition=rule_list[0],
                        effects=compiled_effects,
                        source=f"react[{index}]",
                    )
                )
        elif head == "view":
            assert len(form) == 2, "`view` must wrap exactly one scene expression."
            view_expr = form[1]
        else:
            raise AssertionError(f"Unsupported encounter form: {head}")
    assert title, f"Encounter missing title: {encounter_id}"
    assert store_specs, f"Encounter missing store: {encounter_id}"
    assert view_expr is not None, f"Encounter missing view: {encounter_id}"
    return CompiledEncounterProgram(
        id=encounter_id,
        title=title,
        description=description,
        store_specs=store_specs,
        clocks_by_id=clocks_by_id,
        action_templates=action_templates,
        react_rules=tuple(react_rules),
        view_expr=view_expr,
        rewards=rewards,
        fail_effects=fail_effects,
    )


def initial_store(program: CompiledEncounterProgram) -> dict[str, int | bool | str]:
    return {field_id: spec.initial for field_id, spec in program.store_specs.items()}


def render_encounter(program: CompiledEncounterProgram, store: dict[str, int | bool | str]) -> RenderedEncounter:
    scene = _eval_scene_expr(
        program,
        store,
        program.view_expr,
        scene_path=(),
    )
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


def apply_reacts(program: CompiledEncounterProgram, store: dict[str, int | bool | str]) -> tuple[dict[str, int | bool | str], str | None]:
    working = dict(store)
    steps = 0
    while True:
        fired = False
        for rule in program.react_rules:
            if not _eval_condition(program, working, rule.condition):
                continue
            next_store = _apply_store_effects(program, working, rule.effects)
            outcome = _extract_finish(rule.effects)
            if outcome is not None:
                return next_store, outcome
            if next_store != working:
                working = next_store
                steps += 1
                assert steps <= MAX_REACT_STEPS, f"Encounter react did not converge: {program.id}"
                fired = True
                break
        if not fired:
            return working, None


def _compile_store_field(form: list[SexpNode]) -> StoreFieldSpec:
    head = _symbol(form[0])
    if head == "clock":
        field_id = _symbol(form[1])
        title = _string(form[2])
        initial = _int(form[3])
        maximum = _int(form[4])
        assert 0 <= initial <= maximum, f"Clock initial out of range: {field_id}"
        return StoreFieldSpec(id=field_id, kind="clock", initial=initial, title=title, maximum=maximum)
    if head == "flag":
        return StoreFieldSpec(id=_symbol(form[1]), kind="flag", initial=_bool(form[2]))
    if head == "value":
        return StoreFieldSpec(id=_symbol(form[1]), kind="value", initial=_atom_value(form[2]))
    raise AssertionError(f"Unsupported store form: {head}")


def _compile_defaction(form: list[SexpNode]) -> ActionTemplate:
    assert _symbol(form[0]) == "defaction", "Expected defaction."
    signature = form[1]
    if isinstance(signature, list):
        name = _symbol(signature[0])
        params = tuple(_symbol(item) for item in signature[1:])
    else:
        name = _symbol(signature)
        params = ()
    assert len(form) == 3, "defaction must contain exactly one body."
    body = form[2]
    return ActionTemplate(name=name, params=params, body=body)


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
    if head == "reset_hand":
        return Effect(kind="reset_hand", value=True)
    if head == "set":
        field_id = _symbol(items[1])
        assert field_id in store_specs, f"Unknown encounter store field: {field_id}"
        return Effect(kind="set_encounter_store", value=f"{field_id}:{_effect_value_token(items[2])}")
    if head == "finish":
        return Effect(kind="finish_encounter", value=_symbol(items[1]))
    raise AssertionError(f"Unsupported encounter effect: {head}")


def _effect_value_token(node: SexpNode) -> str:
    value = _atom_value(node)
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
    if isinstance(expr, list):
        head = _symbol(expr[0])
        if head == "scene":
            return _build_scene(program, store, expr, scene_path=scene_path)
        if head == "cond":
            for clause in expr[1:]:
                pair = _list(clause)
                if (isinstance(pair[0], str) and pair[0] == "else") or _eval_condition(program, store, pair[0]):
                    return _eval_scene_expr(program, store, pair[1], scene_path=scene_path)
            return None
        if head == "if":
            if _eval_condition(program, store, expr[1]):
                return _eval_scene_expr(program, store, expr[2], scene_path=scene_path)
            if len(expr) >= 4:
                return _eval_scene_expr(program, store, expr[3], scene_path=scene_path)
            return None
    raise AssertionError(f"Unsupported scene expression: {expr}")


def _build_scene(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    form: list[SexpNode],
    *,
    scene_path: tuple[str, ...],
) -> RenderedScene:
    scene_id = _symbol(form[1])
    title = _string(form[2])
    description = _string(form[3])
    shown_clock_ids: tuple[str, ...] = ()
    rendered_actions: list[RenderedAction] = []
    rendered_children: list[RenderedScene] = []
    path = (*scene_path, scene_id)
    for section in form[4:]:
        section_items = _list(section)
        head = _symbol(section_items[0])
        if head == "show_clocks":
            shown_clock_ids = tuple(_symbol(item) for item in section_items[1:])
        elif head == "actions":
            for source_index, item in enumerate(section_items[1:]):
                rendered = _eval_action_expr(
                    program,
                    store,
                    item,
                    scene_path=path,
                    source_index=source_index,
                )
                if rendered is not None:
                    rendered_actions.append(rendered)
        elif head == "children":
            for child_expr in section_items[1:]:
                child = _eval_scene_expr(program, store, child_expr, scene_path=path)
                if child is not None:
                    rendered_children.append(child)
        else:
            raise AssertionError(f"Unsupported scene section: {head}")
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


def _eval_action_expr(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    expr: SexpNode,
    *,
    scene_path: tuple[str, ...],
    source_index: int,
) -> RenderedAction | None:
    if isinstance(expr, list) and expr and _symbol(expr[0]) == "if":
        if _eval_condition(program, store, expr[1]):
            return _eval_action_expr(program, store, expr[2], scene_path=scene_path, source_index=source_index)
        if len(expr) >= 4:
            return _eval_action_expr(program, store, expr[3], scene_path=scene_path, source_index=source_index)
        return None
    action_key, action_form = _resolve_action_form(program, expr)
    action_def = _compile_action_form(program, action_form, action_key=action_key, scene_path=scene_path, source_index=source_index)
    action_id = f"{program.id}:{'/'.join(scene_path)}:{source_index}:{action_key}"
    handle = ActionHandle(
        action_id=action_id,
        scene_path=scene_path,
        slot_index=source_index,
        action_key=action_key,
    )
    return RenderedAction(
        handle=handle,
        action=replace(action_def, id=action_id),
    )


def _resolve_action_form(program: CompiledEncounterProgram, expr: SexpNode) -> tuple[str, SexpNode]:
    if isinstance(expr, str):
        assert expr in program.action_templates, f"Unknown defaction: {expr}"
        template = program.action_templates[expr]
        return f"def:{expr}", template.body
    items = _list(expr)
    head = _symbol(items[0])
    if head in {"action", "check"}:
        digest = hashlib.sha1(repr(items).encode("utf-8")).hexdigest()[:10]
        return f"inline:{head}:{digest}", items
    assert head in program.action_templates, f"Unknown action expression: {head}"
    template = program.action_templates[head]
    assert len(items) - 1 == len(template.params), f"Wrong arity for defaction {head}: {len(items) - 1}"
    bindings = {param: _atom_value(arg) for param, arg in zip(template.params, items[1:], strict=True)}
    body = _substitute(template.body, bindings)
    return f"def:{head}", body


def _substitute(node: SexpNode, bindings: dict[str, int | bool | str]) -> SexpNode:
    if isinstance(node, list):
        return [_substitute(item, bindings) for item in node]
    if isinstance(node, str) and node in bindings:
        return bindings[node]
    return node


def _compile_action_form(
    program: CompiledEncounterProgram,
    form: SexpNode,
    *,
    action_key: str,
    scene_path: tuple[str, ...],
    source_index: int,
) -> ActionDef:
    items = _list(form)
    head = _symbol(items[0])
    action_id = f"{program.id}:{'/'.join(scene_path)}:{source_index}:{action_key}"
    if head == "action":
        title = _string(items[1])
        description = _string(items[2])
        effects = ()
        for part in items[3:]:
            part_items = _list(part)
            if _symbol(part_items[0]) == "do":
                effects = tuple(_compile_effect(effect_form, program.store_specs) for effect_form in part_items[1:])
            else:
                raise AssertionError(f"Unsupported action section: {_symbol(part_items[0])}")
        return ActionDef(
            id=action_id,
            title=title,
            description=description,
            screen=ScreenName.ENCOUNTER,
            effects=effects,
        )
    assert head == "check", f"Unsupported action form: {head}"
    title = _string(items[1])
    description = _string(items[2])
    suits: tuple[Suit, ...] = ()
    risk: Risk | None = None
    base_effects: tuple[Effect, ...] = ()
    outcomes: dict[str, OutcomeDef] = {}
    for part in items[3:]:
        part_items = _list(part)
        section = _symbol(part_items[0])
        if section == "do":
            base_effects = tuple(_compile_effect(effect_form, program.store_specs) for effect_form in part_items[1:])
        elif section == "suits":
            suits = tuple(SUIT_BY_NAME[_symbol(item)] for item in part_items[1:])
        elif section == "risk":
            risk = RISK_BY_NAME[_symbol(part_items[1])]
        elif section in {"ok", "partial", "fail"}:
            text = _string(part_items[1])
            effects = tuple(_compile_effect(effect_form, program.store_specs) for effect_form in part_items[2:])
            key = {"ok": "success", "partial": "cost", "fail": "fail"}[section]
            outcomes[key] = OutcomeDef(text=text, effects=effects)
        else:
            raise AssertionError(f"Unsupported check section: {section}")
    assert suits, f"Check action missing suits: {title}"
    assert risk is not None, f"Check action missing risk: {title}"
    for key in ("success", "cost", "fail"):
        assert key in outcomes, f"Check action missing outcome {key}: {title}"
    return ActionDef(
        id=action_id,
        title=title,
        description=description,
        screen=ScreenName.ENCOUNTER,
        effects=base_effects,
        check=CheckDef(
            suits=suits,
            risk=risk,
            success=outcomes["success"],
            cost=outcomes["cost"],
            fail=outcomes["fail"],
        ),
    )


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


def _eval_condition(program: CompiledEncounterProgram, store: dict[str, int | bool | str], expr: SexpNode) -> bool:
    items = _list(expr)
    head = _symbol(items[0])
    if head == "and":
        return all(_eval_condition(program, store, item) for item in items[1:])
    if head == "or":
        return any(_eval_condition(program, store, item) for item in items[1:])
    if head == "not":
        return not _eval_condition(program, store, items[1])
    if head == "=":
        return _eval_value(store, items[1]) == _eval_value(store, items[2])
    if head == "<":
        return _eval_value(store, items[1]) < _eval_value(store, items[2])
    if head == "<=":
        return _eval_value(store, items[1]) <= _eval_value(store, items[2])
    if head == ">":
        return _eval_value(store, items[1]) > _eval_value(store, items[2])
    if head == ">=":
        return _eval_value(store, items[1]) >= _eval_value(store, items[2])
    raise AssertionError(f"Unsupported condition expression: {head}")


def _eval_value(store: dict[str, int | bool | str], node: SexpNode) -> int | bool | str:
    value = _atom_value(node)
    if isinstance(value, str) and value in store:
        return store[value]
    return value


def _apply_store_effects(
    program: CompiledEncounterProgram,
    store: dict[str, int | bool | str],
    effects: tuple[Effect, ...],
) -> dict[str, int | bool | str]:
    updated = dict(store)
    for effect in effects:
        if effect.kind == "advance_encounter_clock":
            clock_id, raw = _split_effect_value(effect)
            assert isinstance(updated[clock_id], int)
            spec = program.store_specs[clock_id]
            assert spec.maximum is not None
            updated[clock_id] = min(spec.maximum, int(updated[clock_id]) + int(raw))
        elif effect.kind == "damage_encounter_clock":
            clock_id, raw = _split_effect_value(effect)
            assert isinstance(updated[clock_id], int)
            updated[clock_id] = max(0, int(updated[clock_id]) - int(raw))
        elif effect.kind == "set_encounter_store":
            key, raw = _split_effect_value(effect)
            current = updated[key]
            updated[key] = _coerce_store_value(raw, current)
        elif effect.kind == "finish_encounter":
            continue
    return updated


def validate_encounter_program(program: CompiledEncounterProgram) -> None:
    scene_ids: set[str] = set()
    for template in program.action_templates.values():
        _validate_template(template)
    for rule in program.react_rules:
        _validate_condition_expr(program, rule.condition)
        for effect in rule.effects:
            assert effect.kind in REACT_EFFECT_KINDS, f"Invalid react effect kind: {effect.kind}"
    _validate_scene_expr(program, program.view_expr, scene_ids=scene_ids, scene_path=())


def _extract_finish(effects: tuple[Effect, ...]) -> str | None:
    for effect in effects:
        if effect.kind == "finish_encounter":
            assert isinstance(effect.value, str)
            return effect.value
    return None


def _split_effect_value(effect: Effect) -> tuple[str, str]:
    assert isinstance(effect.value, str)
    key, raw = effect.value.split(":", 1)
    return key, raw


def _coerce_store_value(raw: str, current: int | bool | str) -> int | bool | str:
    if isinstance(current, bool):
        assert raw in {"true", "false"}, f"Invalid bool store value: {raw}"
        return raw == "true"
    if isinstance(current, int):
        return int(raw)
    return raw


def _validate_template(template: ActionTemplate) -> None:
    body = _list(template.body)
    head = _symbol(body[0])
    assert head in {"action", "check"}, f"defaction body must be action/check: {template.name}"


def _validate_scene_expr(
    program: CompiledEncounterProgram,
    expr: SexpNode,
    *,
    scene_ids: set[str],
    scene_path: tuple[str, ...],
) -> None:
    items = _list(expr)
    head = _symbol(items[0])
    if head == "scene":
        scene_id = _symbol(items[1])
        assert scene_id not in scene_ids, f"Duplicate encounter scene id: {scene_id}"
        scene_ids.add(scene_id)
        for section in items[4:]:
            section_items = _list(section)
            section_head = _symbol(section_items[0])
            if section_head == "show_clocks":
                for clock_id in section_items[1:]:
                    name = _symbol(clock_id)
                    assert name in program.clocks_by_id, f"Unknown encounter clock in show_clocks: {name}"
            elif section_head == "actions":
                for source_index, action_expr in enumerate(section_items[1:]):
                    _validate_action_expr(program, action_expr, scene_path=(*scene_path, scene_id), source_index=source_index)
            elif section_head == "children":
                for child_expr in section_items[1:]:
                    _validate_scene_expr(program, child_expr, scene_ids=scene_ids, scene_path=(*scene_path, scene_id))
            else:
                raise AssertionError(f"Unsupported scene section: {section_head}")
        return
    if head == "cond":
        for clause in items[1:]:
            pair = _list(clause)
            assert len(pair) == 2, "Each cond clause must be (condition expr)."
            if not (isinstance(pair[0], str) and pair[0] == "else"):
                _validate_condition_expr(program, pair[0])
            _validate_scene_expr(program, pair[1], scene_ids=scene_ids, scene_path=scene_path)
        return
    if head == "if":
        assert len(items) in {3, 4}, "`if` must have then or then/else branches."
        _validate_condition_expr(program, items[1])
        _validate_scene_expr(program, items[2], scene_ids=scene_ids, scene_path=scene_path)
        if len(items) == 4:
            _validate_scene_expr(program, items[3], scene_ids=scene_ids, scene_path=scene_path)
        return
    raise AssertionError(f"Unsupported scene expression: {head}")


def _validate_action_expr(
    program: CompiledEncounterProgram,
    expr: SexpNode,
    *,
    scene_path: tuple[str, ...],
    source_index: int,
) -> None:
    if isinstance(expr, list) and expr and _symbol(expr[0]) == "if":
        _validate_condition_expr(program, expr[1])
        _validate_action_expr(program, expr[2], scene_path=scene_path, source_index=source_index)
        if len(expr) >= 4:
            _validate_action_expr(program, expr[3], scene_path=scene_path, source_index=source_index)
        return
    action_key, action_form = _resolve_action_form(program, expr)
    _compile_action_form(program, action_form, action_key=action_key, scene_path=scene_path, source_index=source_index)


def _validate_condition_expr(program: CompiledEncounterProgram, expr: SexpNode) -> None:
    items = _list(expr)
    head = _symbol(items[0])
    if head in {"and", "or"}:
        for item in items[1:]:
            _validate_condition_expr(program, item)
        return
    if head == "not":
        _validate_condition_expr(program, items[1])
        return
    if head in {"=", "<", "<=", ">", ">="}:
        _validate_value_expr(program, items[1])
        _validate_value_expr(program, items[2])
        return
    raise AssertionError(f"Unsupported condition expression: {head}")


def _validate_value_expr(program: CompiledEncounterProgram, expr: SexpNode) -> None:
    if isinstance(expr, list):
        raise AssertionError(f"Unsupported value expression: {expr}")
    if isinstance(expr, str) and expr in {"true", "false"}:
        return
    if isinstance(expr, str) and expr not in program.store_specs:
        return


def _list(node: SexpNode) -> list[SexpNode]:
    assert isinstance(node, list), f"Expected list form, got: {node!r}"
    return node


def _symbol(node: SexpNode) -> str:
    assert isinstance(node, str), f"Expected symbol, got: {node!r}"
    return node


def _string(node: SexpNode) -> str:
    assert isinstance(node, str), f"Expected string, got: {node!r}"
    return node


def _int(node: SexpNode) -> int:
    assert isinstance(node, int), f"Expected int, got: {node!r}"
    return node


def _bool(node: SexpNode) -> bool:
    assert isinstance(node, bool), f"Expected bool, got: {node!r}"
    return node


def _signed_int(node: SexpNode) -> int:
    if isinstance(node, int):
        return node
    token = _symbol(node)
    if token.startswith("+") or token.startswith("-"):
        return int(token)
    return int(token)


def _atom_value(node: SexpNode) -> int | bool | str:
    if isinstance(node, (int, bool, str)):
        return node
    raise AssertionError(f"Expected atom, got: {node!r}")
