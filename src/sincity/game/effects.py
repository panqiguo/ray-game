from __future__ import annotations

from sincity.content import SCENARIO
from sincity.content.runtime import evaluate_world_expr
from sincity.encounters import get_encounter, evaluate_effect_expr
from sincity.model.defs import AddFieldPayload, DynamicValue, Effect, FieldRef, SetFieldPayload, ShiftClockPayload
from sincity.model.enums import ScreenName
from sincity.model.state import GameState
from sincity.model.items import ITEMS
from sincity.game.rng import RandomSource

from sincity.game.fields import field_value


# ── Pure utilities ──────────────────────────────────────────────────

def _parse_legacy_scalar(raw: str) -> int | bool | str:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "nil":
        return ""
    try:
        return int(raw)
    except ValueError:
        return raw


def _coerce_like(current: int | bool | str, value: int | bool | str) -> int | bool | str:
    if isinstance(current, bool):
        return bool(value)
    if isinstance(current, int):
        return int(value)
    return str(value)


# ── Payload resolution ──────────────────────────────────────────────

def resolve_set_field_payload(value: object, state: GameState, rng: RandomSource) -> tuple[str, int | bool | str]:
    if isinstance(value, SetFieldPayload):
        raw = value.value
        if isinstance(raw, FieldRef):
            return value.target, field_value(state, raw.name)
        if isinstance(raw, DynamicValue):
            evaluated = evaluate_dynamic_value(state, raw, rng)
            if isinstance(evaluated, FieldRef):
                return value.target, field_value(state, evaluated.name)
            if evaluated is None:
                return value.target, ""
            assert isinstance(evaluated, (int, bool, str)), f"Unsupported dynamic set_field value: {evaluated!r}"
            return value.target, evaluated
        if raw is None:
            return value.target, ""
        assert isinstance(raw, (int, bool, str)), f"Unsupported set_field value: {raw!r}"
        return value.target, raw
    assert isinstance(value, str), f"Invalid set_field payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, _parse_legacy_scalar(raw)


def resolve_add_field_payload(value: object) -> tuple[str, int]:
    if isinstance(value, AddFieldPayload):
        return value.target, value.amount
    assert isinstance(value, str), f"Invalid add_field payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, int(raw)


def resolve_shift_clock_payload(value: object) -> tuple[str, int]:
    if isinstance(value, ShiftClockPayload):
        return value.target, value.amount
    assert isinstance(value, str), f"Invalid shift_clock payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, int(raw)


# ── Dynamic value evaluation ────────────────────────────────────────

def evaluate_dynamic_value(state: GameState, value: DynamicValue, rng: RandomSource) -> object:
    if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
        encounter = get_encounter(state.active_encounter.encounter_id)
        return evaluate_effect_expr(encounter, state.active_encounter.store, value.body, rng=rng)
    return evaluate_world_expr(SCENARIO, state, value.body, rng)


# ── Description helpers ─────────────────────────────────────────────

def describe_set_field_payload(value: object, state: GameState) -> tuple[str, str]:
    if isinstance(value, SetFieldPayload):
        raw = value.value
        if isinstance(raw, FieldRef):
            return value.target, str(field_value(state, raw.name))
        if isinstance(raw, DynamicValue):
            return value.target, "动态值"
        if raw is None:
            return value.target, "nil"
        return value.target, str(raw)
    assert isinstance(value, str), f"Invalid set_field payload: {value!r}"
    key, raw = value.split(":", 1)
    return key, raw


def _field_label(field_id: str) -> str:
    if field_id == "health":
        return "生命"
    if field_id == "stress":
        return "压力"
    if field_id == "pressure":
        return "压力"
    if field_id == "energy":
        return "精力"
    if field_id == "money":
        return "金钱"
    if field_id == "cigarettes":
        return "烟卷"
    if field_id == "force":
        return "暴力"
    if field_id == "charm":
        return "魅力"
    if field_id == "knowledge":
        return "知识"
    if field_id == "sense":
        return "敏锐"
    item = ITEMS.get(field_id)
    return item.name if item else field_id


def describe_effects(effects: tuple[Effect, ...], action_id: str, state: GameState) -> tuple[str, ...]:
    lines: list[str] = []
    encounter = get_encounter(state.active_encounter.encounter_id) if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None else None
    for item in effects:
        value = item.value
        if item.kind == "set_field":
            key, raw = describe_set_field_payload(value, state)
            lines.append(f"{_field_label(key)} = {raw}")
        elif item.kind == "add_field":
            key, amount = resolve_add_field_payload(value)
            lines.append(f"{_field_label(key)} {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "copy_field":
            assert isinstance(value, str)
            target, source = value.split(":", 1)
            lines.append(f"{_field_label(target)} = {_field_label(source)}")
        elif item.kind == "shift_clock":
            key, amount = resolve_shift_clock_payload(value)
            title = encounter.clocks_by_id[key].title if encounter is not None and key in encounter.clocks_by_id else SCENARIO.clocks_by_id.get(key, None).title if key in SCENARIO.clocks_by_id else key
            lines.append(f"{title} {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_health":
            amount = int(value)
            lines.append(f"生命 {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_energy":
            amount = int(value)
            lines.append(f"精力 {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "advance_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            spec = SCENARIO.clocks_by_id[key]
            if "action_use" in spec.tags:
                continue
            lines.append(f"{spec.title} +{raw}")
        elif item.kind == "advance_encounter_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            title = encounter.clocks_by_id[key].title if encounter is not None else key
            lines.append(f"{title} +{raw}")
        elif item.kind == "damage_encounter_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            title = encounter.clocks_by_id[key].title if encounter is not None else key
            lines.append(f"{title} -{raw}")
        elif item.kind == "set_encounter_store":
            continue
        elif item.kind == "end_encounter":
            lines.append("任务结束")
        elif item.kind == "start_encounter":
            assert isinstance(value, str)
            target = get_encounter(value)
            lines.append(f"进入任务：{target.title}")
        elif item.kind == "start_dialogue":
            from sincity.dialogues import get_dialogue
            assert isinstance(value, str)
            target = get_dialogue(value)
            lines.append(f"进入对话：{target.title}")
        elif item.kind == "advance_cycle":
            if state.screen == ScreenName.CITY:
                lines.append("进入新的一天，精力 -1")
            else:
                lines.append("进入新的行动周期，精力 -1")
        elif item.kind == "mount_location":
            assert isinstance(value, (list, tuple)) and len(value) == 2
            lines.append(f"新增地点：{value[0]}/{value[1].title}")
        elif item.kind == "mount_action":
            assert isinstance(value, (list, tuple)) and len(value) == 2
            lines.append(f"新增行动：{value[0]}/{value[1].title}")
        elif item.kind == "unmount_location":
            assert isinstance(value, (list, tuple)) and len(value) == 2
            lines.append(f"移除地点：{value[0]}/{value[1]}")
        elif item.kind == "unmount_action":
            assert isinstance(value, (list, tuple)) and len(value) == 2
            lines.append(f"移除行动：{value[0]}/{value[1]}")
        elif item.kind == "end_game":
            if isinstance(value, tuple):
                lines.append(str(value[0]))
            else:
                lines.append("游戏结束")
        elif item.kind == "upgrade_spirit_value":
            assert isinstance(value, str)
            spirit, raw = value.split(":", 1)
            lines.append(f"{_field_label(spirit)} +{raw}")
        elif item.kind == "add_spirit_slot":
            assert isinstance(value, str)
            lines.append(f"{_field_label(value)} 获得额外槽位")
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
    return tuple(deduped[:4])


# ── Effect execution ────────────────────────────────────────────────

def _push_log(state: GameState, message: str) -> None:
    from sincity.game.dialogues import _push_log as _pl
    _pl(state, message)


def _mark_content_dirty(state: GameState) -> None:
    from sincity.game.fields import _mark_content_dirty as _mcd
    _mcd(state)


def _field_value(state: GameState, key: str) -> int | bool | str:
    from sincity.game.fields import field_value as _fv
    return _fv(state, key)


def _set_field(state: GameState, key: str, value: int | bool | str, extra_lines: list[str]) -> None:
    from sincity.game.fields import set_field as _sf
    return _sf(state, key, value, extra_lines)


def _add_field(state: GameState, key: str, amount: int, extra_lines: list[str]) -> None:
    from sincity.game.fields import add_field as _af
    return _af(state, key, amount, extra_lines)


def apply_effect(item: Effect, state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    from sincity.game.clocks import shift_clock, advance_cycle
    from sincity.game.dialogues import start_dialogue, start_quick_dialogue
    from sincity.game.encounters import start_encounter as _game_start_encounter, finish_encounter
    from sincity.game.fields import (
        change_actor_pressure,
        change_energy,
        change_health,
    )
    from sincity.game.fields import add_spirit_slot, upgrade_spirit_value

    value = item.value
    if item.kind == "set_field":
        key, parsed = resolve_set_field_payload(value, state, rng)
        _set_field(state, key, parsed, extra_lines)
        return
    if item.kind == "add_field":
        key, amount = resolve_add_field_payload(value)
        _add_field(state, key, amount, extra_lines)
        return
    if item.kind == "copy_field":
        assert isinstance(value, str)
        target, source = value.split(":", 1)
        _set_field(state, target, _field_value(state, source), extra_lines)
        return
    if item.kind == "shift_clock":
        key, amount = resolve_shift_clock_payload(value)
        shift_clock(state, key, amount, extra_lines)
        return
    if item.kind == "change_health":
        change_health(state, int(value), extra_lines)
        return
    if item.kind == "change_energy":
        change_energy(state, int(value), extra_lines)
        return
    if item.kind == "advance_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        shift_clock(state, key, int(raw), extra_lines)
        return
    if item.kind == "advance_encounter_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        shift_clock(state, key, int(raw), extra_lines)
        return
    if item.kind == "damage_encounter_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        shift_clock(state, key, -int(raw), extra_lines)
        return
    if item.kind == "set_encounter_store":
        assert isinstance(value, str)
        key, raw = value.split(":", 1)
        parsed: int | bool | str
        if raw == "true":
            parsed = True
        elif raw == "false":
            parsed = False
        else:
            try:
                parsed = int(raw)
            except ValueError:
                parsed = raw
        _set_field(state, key, parsed, extra_lines)
        return
    if item.kind == "start_encounter":
        assert isinstance(value, str)
        start_encounter(state, value)
        return
    if item.kind == "start_dialogue":
        assert isinstance(value, str)
        start_dialogue(state, value)
        return
    if item.kind == "start_quick_dialogue":
        assert isinstance(value, str)
        start_quick_dialogue(state, value)
        return
    if item.kind == "expr":
        assert state.active_encounter is not None, "Dynamic effect expressions are only supported inside encounters."
        def action_log(message: object) -> None:
            _push_log(state, str(message))
        from sincity.encounters import evaluate_effect_expr
        from sincity.encounters import get_encounter as _encounter
        from sincity.content.runtime import evaluate_world_expr
        result = evaluate_effect_expr(_encounter(state.active_encounter.encounter_id), state.active_encounter.store, value, action_log=action_log, rng=rng)
        if isinstance(result, Effect):
            apply_effect(result, state, rng, extra_lines)
        elif isinstance(result, list) and all(isinstance(entry, Effect) for entry in result):
            apply_effects(tuple(result), state, rng, extra_lines)
        _mark_content_dirty(state)
        return
    if item.kind == "end_encounter":
        assert isinstance(value, str)
        finish_encounter(state, value, rng, extra_lines)
        return
    if item.kind == "upgrade_spirit_value":
        assert isinstance(value, str)
        spirit, raw = value.split(":", 1)
        upgrade_spirit_value(state, spirit, int(raw), extra_lines)
        return
    if item.kind == "add_spirit_slot":
        assert isinstance(value, str)
        add_spirit_slot(state, value, extra_lines)
        return
    if item.kind == "advance_cycle":
        advance_cycle(state, rng)
        return
    if item.kind == "mount_location":
        assert isinstance(value, (list, tuple)) and len(value) == 2
        parent_path, template = value
        assert isinstance(parent_path, str)
        from sincity.encounters.defs import LocationTemplate
        assert isinstance(template, LocationTemplate)
        assert template.title, "mounted location :title must not be empty"
        assert "/" not in template.title, f"mounted location :title must not contain '/': {template.title}"
        existing = state.world.mounted_locations.setdefault(parent_path, ())
        for t in existing:
            assert t.title != template.title, f"Duplicate mounted location title under {parent_path}: {template.title}"
        for t in state.world.mounted_actions.get(parent_path, ()):
            assert t.title != template.title, f"Mounted location title conflicts with mounted action under {parent_path}: {template.title}"
        state.world.mounted_locations[parent_path] = existing + (template,)
        _mark_content_dirty(state)
        _push_log(state, f"新增地点：{parent_path}/{template.title}")
        return
    if item.kind == "mount_action":
        assert isinstance(value, (list, tuple)) and len(value) == 2
        parent_path, template = value
        assert isinstance(parent_path, str)
        from sincity.encounters.defs import ActionTemplate
        assert isinstance(template, ActionTemplate)
        assert template.title, "mounted action :title must not be empty"
        assert "/" not in template.title, f"mounted action :title must not contain '/': {template.title}"
        existing = state.world.mounted_actions.setdefault(parent_path, ())
        for t in existing:
            assert t.title != template.title, f"Duplicate mounted action title under {parent_path}: {template.title}"
        for t in state.world.mounted_locations.get(parent_path, ()):
            assert t.title != template.title, f"Mounted action title conflicts with mounted location under {parent_path}: {template.title}"
        state.world.mounted_actions[parent_path] = existing + (template,)
        _mark_content_dirty(state)
        _push_log(state, f"新增行动：{parent_path}/{template.title}")
        return
    if item.kind == "unmount_location":
        assert isinstance(value, (list, tuple)) and len(value) == 2
        parent_path, location_title = value
        assert isinstance(parent_path, str) and isinstance(location_title, str)
        existing = state.world.mounted_locations.get(parent_path, ())
        state.world.mounted_locations[parent_path] = tuple(t for t in existing if t.title != location_title)
        if not state.world.mounted_locations[parent_path]:
            del state.world.mounted_locations[parent_path]
        _mark_content_dirty(state)
        _push_log(state, f"移除地点：{parent_path}/{location_title}")
        return
    if item.kind == "unmount_action":
        assert isinstance(value, (list, tuple)) and len(value) == 2
        parent_path, action_title = value
        assert isinstance(parent_path, str) and isinstance(action_title, str)
        existing = state.world.mounted_actions.get(parent_path, ())
        state.world.mounted_actions[parent_path] = tuple(t for t in existing if t.title != action_title)
        if not state.world.mounted_actions[parent_path]:
            del state.world.mounted_actions[parent_path]
        _mark_content_dirty(state)
        _push_log(state, f"移除行动：{parent_path}/{action_title}")
        return
    if item.kind == "end_game":
        if isinstance(value, tuple):
            _push_log(state, str(value[0]))
            from sincity.game.dialogues import end_game
            end_game(state, value[0], value[1] if len(value) > 1 else None)
        else:
            assert isinstance(value, str)
            _push_log(state, value)
            from sincity.game.dialogues import end_game
            end_game(state, value)
        return
    if item.kind == "change_actor_pressure":
        assert isinstance(value, str)
        actor_id, raw = value.split(":", 1)
        change_actor_pressure(state, actor_id, int(raw), extra_lines)
        return
    raise ValueError(f"Unknown effect kind: {item.kind}")


def apply_effects(
    effects: tuple[Effect, ...],
    state: GameState,
    rng: RandomSource,
    extra_lines: list[str] | None = None,
    *,
    resolve_encounter_reacts: bool = True,
) -> tuple[str, ...]:
    from sincity.game.reacts import resolve_world_reacts, resolve_encounter_reacts, award_completed_tasks
    derived: list[str] = [] if extra_lines is None else extra_lines
    for item in effects:
        apply_effect(item, state, rng, derived)
    if resolve_encounter_reacts:
        if state.screen == ScreenName.ENCOUNTER and state.active_encounter is not None:
            resolve_encounter_reacts(state, rng, derived)
        elif state.screen == ScreenName.CITY:
            resolve_world_reacts(state, rng, derived)
    award_completed_tasks(state)
    return tuple(derived)
