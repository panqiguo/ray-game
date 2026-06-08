from __future__ import annotations

from sincity.content import SCENARIO
from sincity.content.runtime import evaluate_world_react_effects, next_react_rule as next_world_react_rule, render_tasks, react_rule_matches as world_react_rule_matches
from sincity.encounters import MAX_REACT_STEPS, evaluate_react_rules, evaluate_reaction_die, next_react_rule, react_rule_matches
from sincity.model.enums import ScreenName
from sincity.model.state import GameState
from sincity.rules.rng import RandomSource

from sincity.game.effects import apply_effects


def _push_log(state: GameState, text: str) -> None:
    from sincity.constants import MAX_LOG_LINES
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def _push_notification(state: GameState, kind: str, title: str, body: str) -> None:
    from sincity.rules.notifications import push_notification
    push_notification(state, kind, title, body)


def _encounter(state: GameState):
    from sincity.encounters import get_encounter
    assert state.active_encounter is not None
    return get_encounter(state.active_encounter.encounter_id)


def react_non_convergence_message(kind: str, program_id: str, fired_sources: list[str]) -> str:
    recent = fired_sources[-8:]
    chain = " -> ".join(recent)
    if chain:
        return f"{kind} react did not converge: {program_id}. Recent chain: {chain}"
    return f"{kind} react did not converge: {program_id}"


def resolve_world_reacts(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    blocked_sources: set[str] = set()
    steps = 0
    fired_sources: list[str] = []
    while state.screen == ScreenName.CITY:
        blocked_sources = {
            source
            for source in blocked_sources
            if any(rule.source == source and world_react_rule_matches(SCENARIO, state, rule) for rule in SCENARIO.react_rules)
        }
        rule = next_world_react_rule(SCENARIO, state, blocked_sources)
        if rule is None:
            return
        fired_sources.append(rule.source)
        steps += 1
        assert steps <= MAX_REACT_STEPS, react_non_convergence_message("World", SCENARIO.id, fired_sources)
        effects = evaluate_world_react_effects(SCENARIO, state, rule, rng)
        apply_effects(effects, state, rng, extra_lines, resolve_encounter_reacts=False)
        if world_react_rule_matches(SCENARIO, state, rule):
            blocked_sources.add(rule.source)
        else:
            blocked_sources.discard(rule.source)


def resolve_encounter_reacts(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    if state.active_encounter is None or state.screen != ScreenName.ENCOUNTER:
        return
    encounter = _encounter(state)
    blocked_sources: set[str] = set()
    steps = 0
    fired_sources: list[str] = []
    while state.active_encounter is not None and state.screen == ScreenName.ENCOUNTER:
        blocked_sources = {
            source
            for source in blocked_sources
            if any(rule.source == source and react_rule_matches(encounter, state.active_encounter.store, rule) for rule in evaluate_react_rules(encounter, state.active_encounter.store))
        }
        rule = next_react_rule(encounter, state.active_encounter.store, blocked_sources)
        if rule is None:
            return
        fired_sources.append(rule.source)
        steps += 1
        assert steps <= MAX_REACT_STEPS, react_non_convergence_message("Encounter", encounter.id, fired_sources)
        apply_effects(rule.effects, state, rng, extra_lines, resolve_encounter_reacts=False)
        if state.active_encounter is None or state.screen != ScreenName.ENCOUNTER:
            return
        if react_rule_matches(encounter, state.active_encounter.store, rule):
            blocked_sources.add(rule.source)
        else:
            blocked_sources.discard(rule.source)


def resolve_encounter_reaction_die(state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    assert state.active_encounter is not None
    encounter = _encounter(state)
    table = evaluate_reaction_die(encounter, state.active_encounter.store)
    if table is None:
        return
    roll = rng.d6()
    face = next((item for item in table.faces if item.value == roll), None)
    if face is None:
        return
    title = f"反应骰 {roll}：{face.title}"
    _push_log(state, f"{title}。{face.description}" if face.description else f"{title}。")
    if face.title != "空" or face.description or face.effects:
        body = face.description or f"骰面 {roll}"
        _push_notification(state, "warning", title, body)
    apply_effects(face.effects, state, rng, extra_lines)


def award_completed_tasks(state: GameState) -> None:
    for task in render_tasks(SCENARIO.get_program(), state):
        if task.kind not in {"主线", "支线"} or not task.completed:
            continue
        if task.title in state.world.rewarded_tasks:
            continue
        state.world.rewarded_tasks.add(task.title)
        state.growth_points += 1
        _push_log(state, f"{task.kind}任务完成：{task.title}，获得 1 点成长。")
        _push_notification(state, "success", f"{task.kind}任务完成", f"{task.title}，获得 1 点成长。")
