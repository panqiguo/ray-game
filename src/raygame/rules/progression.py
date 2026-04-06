from __future__ import annotations

from raygame.constants import HAND_SIZE, MAX_LOG_LINES, MISSION_PUSH_THROUGH_DRAW
from raygame.content import CITY_ACTIONS, GROWTH_DEFS, MISSION_ACTIONS
from raygame.content.cards import CARD_DEFS
from raygame.model.defs import ActionCostDef, ActionMethodDef, ActionPointDef, OutcomeDef
from raygame.model.enums import AreaName, ResultType, ScreenName, Suit
from raygame.model.state import ActionResolution, GameState

from .conditions import all_met
from .deck import discard_card, draw_cards, make_starting_deck, start_city_day, start_mission_hand
from .effects import apply_effects
from .ending_rules import determine_ending
from .judgment import compute_action_value, roll_result
from .rng import RandomSource


def _push_log(state: GameState, text: str) -> None:
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def action_is_available(action: ActionPointDef, state: GameState) -> bool:
    if not action_is_visible(action, state):
        return False
    if not action_costs_affordable(action, state):
        return False
    if action.special == "push_through":
        return not state.deck.hand and state.deck.push_through_count < 3
    return True


def action_is_visible(action: ActionPointDef, state: GameState) -> bool:
    if not all_met(action.conditions, state):
        return False
    if state.screen == ScreenName.CITY and f"city_done:{action.id}:{state.day}" in state.flags:
        return False
    if state.screen == ScreenName.CITY:
        if action.id == "buy_cigarettes" and state.resources.money < 10:
            return False
        if action.id == "bandage" and (
            state.resources.money < 15 or not _has_negative_family(state, "physical")
        ):
            return False
        if action.id == "clear_mind" and not _has_negative_family(state, "mental"):
            return False
        if action.id == "drink_out" and not _has_any_negative(state):
            return False
    if state.screen == ScreenName.MISSION and action.area is not None:
        if action.area != state.mission.current_area:
            return False
    if action.id in state.mission.completed_actions:
        return False
    if action.id == "evidence" and not state.mission.evidence_unlocked:
        return False
    if action.id == "crow" and not (state.mission.boss_resolution or state.mission.freezer_shortcut):
        return False
    if action.special == "enter_mission" and not can_enter_mission(state):
        return False
    return True


def action_costs_affordable(action: ActionPointDef, state: GameState) -> bool:
    for cost in action.costs:
        if cost.kind == "resource":
            if getattr(state.resources, cost.key) < cost.amount:
                return False
        elif cost.kind == "item":
            if cost.key not in state.items:
                return False
        else:
            raise AssertionError(f"Unsupported cost kind {cost.kind}")
    return True


def cost_token(cost: ActionCostDef) -> str:
    return f"{cost.kind}:{cost.key}"


def cost_is_prepared(state: GameState, cost: ActionCostDef) -> bool:
    return cost_token(cost) in state.prepared_costs


def toggle_prepared_cost(state: GameState, action: ActionPointDef, cost: ActionCostDef) -> None:
    token = cost_token(cost)
    if token in state.prepared_costs:
        state.prepared_costs.remove(token)
        return
    assert action_costs_affordable(action, state), f"Action cost is not affordable: {action.id}"
    state.prepared_costs.add(token)


def action_costs_ready(action: ActionPointDef, state: GameState) -> bool:
    return all(cost_is_prepared(state, cost) for cost in action.costs)


def action_selection_ready(action: ActionPointDef, state: GameState) -> bool:
    if action.special != "mission_smoke":
        return True
    if state.selected_card_id is None or state.selected_card_id not in state.deck.hand:
        return False
    return CARD_DEFS[state.selected_card_id].is_negative


def action_ready_to_execute(action: ActionPointDef, state: GameState) -> bool:
    return action_is_visible(action, state) and action_costs_ready(action, state) and action_selection_ready(action, state)


def method_is_available(method: ActionMethodDef, state: GameState) -> bool:
    if not all_met(tuple(condition for condition in method.conditions if condition.kind != "if_clue_reduce"), state):
        return False
    return True


def effective_difficulty(method: ActionMethodDef, state: GameState) -> int:
    difficulty = method.difficulty
    if method.id == "guard_instinct" and "clue_c" in state.clues:
        difficulty -= 1
    if state.screen == ScreenName.MISSION and state.mission.lights_off and state.mission.current_area == AreaName.FREEZER:
        difficulty -= 1
    return max(1, difficulty)


def start_new_run(seed: int) -> tuple[GameState, RandomSource]:
    rng = RandomSource(seed)
    deck = make_starting_deck(rng)
    state = GameState(deck=deck, seed=seed)
    state.pending_growth_choices = ["calm_habit", "casebook", "paranoid_reason"]
    state.growth_points = 1
    start_city_day(state.deck, rng, HAND_SIZE)
    _push_log(state, f"雨夜开局。Seed={seed}")
    return state, rng


def perform_free_action(state: GameState, rng: RandomSource, action: ActionPointDef) -> None:
    assert action_ready_to_execute(action, state), f"Action is not ready: {action.id}"
    _consume_action_costs(state, action)
    if action.special:
        _perform_special_action(state, rng, action)
        _clear_selection(state)
        _check_run_fail(state)
        return
    apply_effects(action.free_effects, state)
    if state.screen == ScreenName.CITY and action.free_completes:
        state.flags.add(f"city_done:{action.id}:{state.day}")
    _push_log(state, f"{action.title}: {action.free_text}")
    _clear_selection(state)
    _check_run_fail(state)


def perform_action(state: GameState, rng: RandomSource, action: ActionPointDef, method: ActionMethodDef, card_id: str, wildcard: Suit | None = None) -> None:
    discard_card(state.deck, card_id)
    temp_method = ActionMethodDef(
        id=method.id,
        title=method.title,
        suits=method.suits,
        difficulty=effective_difficulty(method, state),
        risk=method.risk,
        success=method.success,
        cost=method.cost,
        fail=method.fail,
        description=method.description,
        conditions=method.conditions,
        bonus=method.bonus,
    )
    value = compute_action_value(card_id, temp_method, wildcard_suit=wildcard)
    die_roll = rng.d6()
    result = roll_result(value, die_roll)
    outcome: OutcomeDef
    if result == ResultType.SUCCESS:
        outcome = method.success
    elif result == ResultType.COST:
        outcome = method.cost
    else:
        outcome = method.fail
    apply_effects(outcome.effects, state)
    if outcome.completes and state.screen == ScreenName.MISSION:
        state.mission.completed_actions.add(action.id)
        _advance_area_if_ready(state)
    if outcome.completes and state.screen == ScreenName.CITY:
        state.flags.add(f"city_done:{action.id}:{state.day}")
    text = outcome.available_text or outcome.text
    state.last_resolution = ActionResolution(
        action_id=action.id,
        method_id=method.id,
        card_id=card_id,
        result=result,
        die_roll=die_roll,
        value=value,
        text=text,
    )
    _push_log(state, f"{action.title}/{method.title}: {text}")
    _clear_selection(state)
    _check_run_fail(state)


def _advance_area_if_ready(state: GameState) -> None:
    if state.mission.current_area == AreaName.PERIMETER:
        if "fence" in state.mission.completed_actions and ("guard" in state.mission.completed_actions or state.mission.skipped_guard):
            state.mission.current_area = AreaName.CORRIDOR
            _push_log(state, "你穿过外围，走廊的冷气迎面压过来。")
    elif state.mission.current_area == AreaName.CORRIDOR:
        if "dog" in state.mission.completed_actions and "control_room" in state.mission.completed_actions:
            state.mission.current_area = AreaName.FREEZER
            _push_log(state, "走廊尽头的冷库门缓缓敞开。")
    elif state.mission.current_area == AreaName.FREEZER:
        if state.mission.crow_rescued and (state.mission.boss_resolution or state.mission.freezer_shortcut):
            finish_run(state)


def _check_run_fail(state: GameState) -> None:
    if state.resources.health <= 0 or "run_failed" in state.flags:
        finish_run(state)
    if state.clocks.alarm >= state.clocks.alarm_max:
        state.flags.add("run_failed")
        _push_log(state, "警报满了，冷库里的脚步从四面围了上来。")
        finish_run(state)


def _clear_selection(state: GameState) -> None:
    state.selected_action_id = None
    state.selected_method_id = None
    state.selected_card_id = None
    state.prepared_costs.clear()
    state.modal.kind = ""
    state.modal.primary_id = None


def _consume_action_costs(state: GameState, action: ActionPointDef) -> None:
    for cost in action.costs:
        token = cost_token(cost)
        assert token in state.prepared_costs, f"Unprepared cost for action {action.id}: {token}"
        if cost.kind == "resource":
            current = getattr(state.resources, cost.key)
            assert current >= cost.amount, f"Insufficient resource {cost.key}"
            setattr(state.resources, cost.key, current - cost.amount)
        elif cost.kind == "item":
            assert cost.key in state.items, f"Missing item {cost.key}"
            state.items.remove(cost.key)
        else:
            raise AssertionError(f"Unsupported cost kind {cost.kind}")


def _perform_special_action(state: GameState, rng: RandomSource, action: ActionPointDef) -> None:
    if action.special == "city_smoke":
        state.resources.stress = max(0, state.resources.stress - 2)
        state.deck.discard_pile.append("fatigue")
        _push_log(state, "烟卷压住了焦躁，但疲惫会在之后找上你。")
        return
    if action.special == "mission_smoke":
        assert state.selected_card_id is not None
        assert state.selected_card_id in state.deck.hand
        assert CARD_DEFS[state.selected_card_id].is_negative
        discard_card(state.deck, state.selected_card_id)
        draw_cards(state.deck, rng, len(state.deck.hand) + 1)
        state.resources.stress = min(state.resources.max_stress, state.resources.stress + 1)
        _push_log(state, "烟雾散开，你把一张负面牌从手里扔掉了。")
        return
    if action.special == "end_day":
        end_day(state, rng)
        return
    if action.special == "enter_mission":
        enter_mission(state, rng)
        return
    if action.special == "push_through":
        push_through(state, rng)
        return
    raise AssertionError(f"Unsupported special action {action.special}")


def end_day(state: GameState, rng: RandomSource) -> None:
    if "enable_casebook" in state.flags and state.selected_card_id in state.deck.hand:
        from .deck import choose_casebook_card

        choose_casebook_card(state.deck, state.selected_card_id)
    while state.deck.hand:
        state.deck.discard_pile.append(state.deck.hand.pop())
    if state.clocks.freeze_crow_time_once:
        state.clocks.freeze_crow_time_once = False
        _push_log(state, "你替乌鸦多争到了一天。")
    else:
        state.clocks.crow_time = max(0, state.clocks.crow_time - 1)
    if "hungover" in state.flags:
        hand_size = HAND_SIZE - 1
        state.flags.remove("hungover")
    else:
        hand_size = HAND_SIZE
    if state.clocks.crow_time <= 0 and state.day >= 3:
        _push_log(state, "乌鸦的时间已经归零。你只能赌自己还赶得上。")
    state.day += 1
    if state.day == 3 and not state.unlocked_growths:
        state.pending_growth_choices = [gid for gid in state.pending_growth_choices if gid not in state.unlocked_growths]
    start_city_day(state.deck, rng, hand_size)
    _push_log(state, f"第 {state.day} 天开始。")
    _clear_selection(state)


def can_enter_mission(state: GameState) -> bool:
    return "clue_a" in state.clues or state.day >= 3


def enter_mission(state: GameState, rng: RandomSource) -> None:
    assert can_enter_mission(state), "Mission is locked"
    state.screen = ScreenName.MISSION
    state.mission.current_area = AreaName.PERIMETER
    state.mission.completed_actions.clear()
    state.clocks.alarm = 0
    start_mission_hand(state.deck, rng)
    _push_log(state, "屠宰场的大门在雨里发黑。")
    if state.clocks.heat >= 4:
        state.clocks.alarm = 1
        _push_log(state, "Heat 太高，外围已经有人提高了警觉。")


def push_through(state: GameState, rng: RandomSource) -> None:
    assert state.screen == ScreenName.MISSION
    assert not state.deck.hand
    assert state.deck.push_through_count < len(MISSION_PUSH_THROUGH_DRAW)
    stress_cost = 2 + state.deck.push_through_count
    draw_amount = MISSION_PUSH_THROUGH_DRAW[state.deck.push_through_count]
    state.deck.push_through_count += 1
    state.resources.stress = min(state.resources.max_stress, state.resources.stress + stress_cost)
    if state.resources.stress >= state.resources.max_stress:
        state.resources.stress = max(0, state.resources.max_stress - 2)
        state.deck.discard_pile.append("panic")
    draw_cards(state.deck, rng, draw_amount)
    _push_log(state, f"你硬撑了一次，抽 {draw_amount} 张，Stress +{stress_cost}。")


def claim_growth(state: GameState, growth_id: str) -> None:
    assert state.growth_points > 0, "No growth points available"
    growth = GROWTH_DEFS[growth_id]
    apply_effects(growth.effects, state)
    state.unlocked_growths.add(growth_id)
    state.growth_points -= 1
    state.pending_growth_choices = []
    state.modal.kind = ""
    state.modal.primary_id = None
    _push_log(state, f"成长解锁：{growth.title}")


def finish_run(state: GameState) -> None:
    ending_id, title, body = determine_ending(state)
    state.ending_id = ending_id
    state.ending_title = title
    state.ending_body = body
    state.screen = ScreenName.ENDING


def _has_negative_family(state: GameState, family: str) -> bool:
    from raygame.content.cards import CARD_DEFS

    for pile in (state.deck.hand, state.deck.draw_pile, state.deck.discard_pile):
        for card_id in pile:
            card = CARD_DEFS[card_id]
            if card.is_negative and card.negative_family == family:
                return True
    return False


def _has_any_negative(state: GameState) -> bool:
    return _has_negative_family(state, "physical") or _has_negative_family(state, "mental")
