from __future__ import annotations

from raygame.constants import HAND_SIZE, MAX_LOG_LINES
from raygame.content import GROWTH_DEFS, SCENARIO
from raygame.content.cards import CARD_DEFS
from raygame.model.defs import ActionDef, Effect, InputRequirement
from raygame.model.enums import ResultType, ScreenName
from raygame.model.state import (
    ActionAssemblyState,
    ActionResolution,
    AttributeState,
    DeckState,
    GameState,
    PendingResolutionState,
    ProgressClockState,
    ResourceState,
    SelectedInputState,
    WorldState,
)
from raygame.rules.deck import draw_cards, make_starting_deck, reshuffle, start_city_day
from raygame.rules.judgment import compute_action_value, roll_result
from raygame.rules.rng import RandomSource


TRAUMA_CARD_ID = "trauma"
TRAUMA_HEALTH_STEP = 2


def _push_log(state: GameState, text: str) -> None:
    state.action_log.append(text)
    del state.action_log[:-MAX_LOG_LINES]


def start_new_run(seed: int) -> tuple[GameState, RandomSource]:
    rng = RandomSource(seed)
    deck = make_starting_deck(rng)
    world = WorldState(
        visible_locations=set(SCENARIO.initial_visible_locations),
        progress_clocks={
            clock_id: ProgressClockState(
                value=0,
                visible=clock_id in SCENARIO.initial_visible_clocks or not spec.hidden,
            )
            for clock_id, spec in SCENARIO.clocks_by_id.items()
        },
        inventory=dict(SCENARIO.initial_inventory),
    )
    state = GameState(
        deck=deck,
        attributes=AttributeState(
            health=SCENARIO.initial_health,
            max_health=10,
            stress=SCENARIO.initial_stress,
            max_stress=8,
        ),
        resources=ResourceState(
            money=SCENARIO.initial_money,
            cigarettes=SCENARIO.initial_cigarettes,
        ),
        world=world,
        screen=ScreenName.CITY,
        pending_growth_choices=list(SCENARIO.initial_growth_choices),
        growth_points=0,
        seed=seed,
    )
    sync_trauma_cards_with_health(state)
    start_city_day(state.deck, rng, HAND_SIZE)
    _push_log(state, "你从一场暴打里活了下来，但还没真正脱身。")
    return state, rng


def get_action(action_id: str) -> ActionDef:
    return SCENARIO.actions_by_id[action_id]


def get_clock_value(state: GameState, clock_id: str) -> int:
    return state.world.progress_clocks[clock_id].value


def action_is_visible(action: ActionDef, state: GameState) -> bool:
    if action.id in state.world.hidden_actions:
        return False
    location_id = location_for_action(action.id)
    if location_id is not None and not location_is_visible(location_id, state):
        return False
    return all_met(action.conditions, state)


def action_is_available(action: ActionDef, state: GameState) -> bool:
    return action_is_visible(action, state) and requirements_affordable(action.inputs, state)


def location_is_visible(location_id: str, state: GameState) -> bool:
    if location_id == SCENARIO.world_root_id:
        return True
    parent_id = SCENARIO.parent_by_id[location_id]
    if parent_id is None:
        if location_id not in state.world.visible_locations:
            return False
    else:
        if not location_is_visible(parent_id, state):
            return False
    location = SCENARIO.locations_by_id[location_id]
    return all_met(location.conditions, state)


def all_met(conditions, state: GameState) -> bool:
    return all(evaluate_condition(condition, state) for condition in conditions)


def evaluate_condition(item, state: GameState) -> bool:
    value = item.value
    if item.kind == "has_item":
        assert isinstance(value, str)
        return state.world.inventory.get(value, 0) > 0
    if item.kind == "inventory_below":
        assert isinstance(value, str)
        item_id, raw = value.split(":")
        return state.world.inventory.get(item_id, 0) < int(raw)
    if item.kind == "clock_at_least":
        assert isinstance(value, str)
        clock_id, raw = value.split(":")
        return get_clock_value(state, clock_id) >= int(raw)
    if item.kind == "clock_hidden":
        assert isinstance(value, str)
        return not state.world.progress_clocks[value].visible
    if item.kind == "location_visible":
        assert isinstance(value, str)
        return value in state.world.visible_locations
    raise AssertionError(f"Unsupported condition kind: {item.kind}")


def requirements_affordable(inputs: tuple[InputRequirement, ...], state: GameState) -> bool:
    for requirement in inputs:
        if requirement.kind == "card":
            if requirement.key == "any" and not state.deck.hand:
                return False
            if requirement.key == "negative" and not any(CARD_DEFS[card_id].is_negative for card_id in state.deck.hand):
                return False
        elif requirement.kind == "resource":
            if getattr(state.resources, requirement.key) < requirement.amount:
                return False
        elif requirement.kind == "item":
            if state.world.inventory.get(requirement.key, 0) < requirement.amount:
                return False
        else:
            raise AssertionError(f"Unsupported input kind: {requirement.kind}")
    return True


def open_action(state: GameState, action_id: str, modal_kind: str = "action") -> None:
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    state.assembly = ActionAssemblyState(action_id=action_id)
    state.selected_input = SelectedInputState()
    state.modal.kind = modal_kind
    state.modal.primary_id = action_id


def open_modal(state: GameState, kind: str, primary_id: str | None = None) -> None:
    dismiss_pending_resolution(state)
    state.modal.kind = kind
    state.modal.primary_id = primary_id
    state.modal.return_kind = ""
    state.modal.return_primary_id = None
    if kind == "location" and primary_id is not None:
        state.world.fresh_locations.discard(primary_id)
    if kind != "action":
        clear_assembly(state)
        clear_selected_input(state)


def open_overlay(state: GameState, kind: str, primary_id: str | None = None) -> None:
    dismiss_pending_resolution(state)
    assert state.modal.kind, "overlay requires an active base modal"
    state.modal.return_kind = state.modal.kind
    state.modal.return_primary_id = state.modal.primary_id
    state.modal.kind = kind
    state.modal.primary_id = primary_id


def clear_assembly(state: GameState) -> None:
    state.assembly = ActionAssemblyState()


def clear_selected_input(state: GameState) -> None:
    state.selected_input = SelectedInputState()


def close_modal(state: GameState) -> None:
    dismiss_pending_resolution(state)
    if state.modal.return_kind:
        state.modal.kind = state.modal.return_kind
        state.modal.primary_id = state.modal.return_primary_id
        state.modal.return_kind = ""
        state.modal.return_primary_id = None
        return
    state.modal.kind = ""
    state.modal.primary_id = None
    clear_assembly(state)
    clear_selected_input(state)


def select_card_input(state: GameState, card_id: str) -> None:
    if state.selected_input.kind == "card" and state.selected_input.key == card_id:
        clear_selected_input(state)
        return
    state.selected_input = SelectedInputState(kind="card", key=card_id)


def select_resource_input(state: GameState, key: str) -> None:
    if state.selected_input.kind == "resource" and state.selected_input.key == key:
        clear_selected_input(state)
        return
    state.selected_input = SelectedInputState(kind="resource", key=key)


def select_item_input(state: GameState, key: str) -> None:
    if state.selected_input.kind == "item" and state.selected_input.key == key:
        clear_selected_input(state)
        return
    state.selected_input = SelectedInputState(kind="item", key=key)


def focus_action(state: GameState, action_id: str) -> None:
    if state.assembly.action_id == action_id:
        return
    state.assembly = ActionAssemblyState(action_id=action_id)


def action_slot_ready(state: GameState, action: ActionDef, requirement: InputRequirement | None = None, *, check_slot: bool = False) -> bool:
    if state.assembly.action_id != action.id:
        return False
    if check_slot:
        return state.assembly.slotted_card_id is not None
    assert requirement is not None
    return requirement_is_slotted(state, requirement)


def action_can_accept_selected_input(state: GameState, action: ActionDef, requirement: InputRequirement | None = None, *, check_slot: bool = False) -> bool:
    selected = state.selected_input
    if not selected.kind:
        return False
    if check_slot:
        return selected.kind == "card" and selected.key in state.deck.hand
    assert requirement is not None
    if requirement.kind == "resource":
        return selected.kind == "resource" and selected.key == requirement.key and getattr(state.resources, requirement.key) >= requirement.amount
    if requirement.kind == "item":
        return selected.kind == "item" and selected.key == requirement.key and state.world.inventory.get(requirement.key, 0) >= requirement.amount
    if requirement.kind == "card":
        if selected.kind != "card" or selected.key not in state.deck.hand:
            return False
        return requirement.key != "negative" or CARD_DEFS[selected.key].is_negative
    return False


def toggle_action_check_slot(state: GameState, action: ActionDef) -> None:
    if state.assembly.action_id == action.id and state.assembly.slotted_card_id is not None:
        state.assembly.slotted_card_id = None
        if not state.assembly.slotted_items and not state.assembly.slotted_resources:
            state.assembly.action_id = None
        return
    if not action_can_accept_selected_input(state, action, check_slot=True):
        return
    focus_action(state, action.id)
    state.assembly.slotted_card_id = state.selected_input.key
    clear_selected_input(state)


def toggle_action_requirement_slot(state: GameState, action: ActionDef, requirement: InputRequirement) -> None:
    if state.assembly.action_id == action.id and requirement_is_slotted(state, requirement):
        if requirement.kind == "resource":
            state.assembly.slotted_resources.pop(requirement.key, None)
        elif requirement.kind == "item":
            state.assembly.slotted_items.pop(requirement.key, None)
        elif requirement.kind == "card":
            state.assembly.slotted_card_id = None
        if not state.assembly.slotted_items and not state.assembly.slotted_resources and state.assembly.slotted_card_id is None:
            state.assembly.action_id = None
        return
    if not action_can_accept_selected_input(state, action, requirement):
        return
    focus_action(state, action.id)
    if requirement.kind == "resource":
        state.assembly.slotted_resources[requirement.key] = requirement.amount
    elif requirement.kind == "item":
        state.assembly.slotted_items[requirement.key] = requirement.amount
    elif requirement.kind == "card":
        state.assembly.slotted_card_id = state.selected_input.key
    clear_selected_input(state)


def slot_card(state: GameState, card_id: str) -> None:
    action = current_action(state)
    if action is None:
        return
    requirement = next((item for item in action.inputs if item.kind == "card"), None)
    if requirement is None and action.check is None:
        return
    if requirement is not None and requirement.key == "negative" and not CARD_DEFS[card_id].is_negative:
        return
    state.assembly.slotted_card_id = None if state.assembly.slotted_card_id == card_id else card_id


def toggle_requirement_input(state: GameState, requirement: InputRequirement) -> None:
    action = current_action(state)
    if action is None:
        return
    if requirement.kind == "resource":
        if state.assembly.slotted_resources.get(requirement.key, 0) >= requirement.amount:
            state.assembly.slotted_resources.pop(requirement.key, None)
        elif getattr(state.resources, requirement.key) >= requirement.amount:
            state.assembly.slotted_resources[requirement.key] = requirement.amount
    elif requirement.kind == "item":
        if state.assembly.slotted_items.get(requirement.key, 0) >= requirement.amount:
            state.assembly.slotted_items.pop(requirement.key, None)
        elif state.world.inventory.get(requirement.key, 0) >= requirement.amount:
            state.assembly.slotted_items[requirement.key] = requirement.amount


def requirement_is_slotted(state: GameState, requirement: InputRequirement) -> bool:
    if requirement.kind == "card":
        if requirement.key == "negative":
            return state.assembly.slotted_card_id is not None and CARD_DEFS[state.assembly.slotted_card_id].is_negative
        return state.assembly.slotted_card_id is not None
    if requirement.kind == "resource":
        return state.assembly.slotted_resources.get(requirement.key, 0) >= requirement.amount
    if requirement.kind == "item":
        return state.assembly.slotted_items.get(requirement.key, 0) >= requirement.amount
    raise AssertionError(f"Unsupported requirement kind: {requirement.kind}")


def action_ready_to_execute(action: ActionDef, state: GameState) -> bool:
    if not action_is_available(action, state):
        return False
    for requirement in action.inputs:
        if not requirement_is_slotted(state, requirement):
            return False
    if action.check is not None and state.assembly.slotted_card_id is None:
        return False
    return True


def current_action(state: GameState) -> ActionDef | None:
    return get_action(state.assembly.action_id) if state.assembly.action_id else None


def perform_current_action(state: GameState, rng: RandomSource) -> None:
    action = current_action(state)
    assert action is not None
    assert action_ready_to_execute(action, state), f"Action not ready: {action.id}"
    location_id = location_for_action(action.id)
    _consume_inputs(state, action)
    if action.check is None:
        resolution = ActionResolution(
            action_id=action.id,
            card_id=state.assembly.slotted_card_id,
            result=None,
            die_roll=None,
            value=None,
            text=action.description,
            effect_lines=_describe_effects(action.effects, action.id),
        )
        state.pending_resolution = PendingResolutionState(
            resolution=resolution,
            effects=action.effects,
            log_text=f"{action.title}: {action.description}",
            location_id=location_id or "",
        )
    else:
        card_id = state.assembly.slotted_card_id
        assert card_id is not None
        _consume_slotted_card(state)
        value = compute_action_value(card_id, action.check)
        die_roll = rng.d6()
        result = roll_result(value, die_roll)
        if result == ResultType.SUCCESS:
            outcome = action.check.success
        elif result == ResultType.COST:
            outcome = action.check.cost
        else:
            outcome = action.check.fail
        resolved_effects = action.effects + outcome.effects
        effect_lines = _describe_effects(resolved_effects, action.id)
        resolution = ActionResolution(
            action_id=action.id,
            card_id=card_id,
            result=result,
            die_roll=die_roll,
            value=value,
            text=_compose_resolution_text(result, effect_lines, outcome.text),
            effect_lines=effect_lines,
        )
        state.pending_resolution = PendingResolutionState(
            resolution=resolution,
            effects=resolved_effects,
            log_text=f"{action.title}: {_compose_resolution_text(result, effect_lines, outcome.text)}",
            location_id=location_id or "",
        )
    clear_selected_input(state)


def advance_pending_resolution(state: GameState, rng: RandomSource, dt: float) -> None:
    pending = state.pending_resolution
    if pending is None:
        return
    if not pending.settled:
        pending.progress = min(1.0, pending.progress + dt / 0.7)
        if pending.progress >= 1.0:
            extra_lines = _apply_effects(pending.effects, state, rng)
            if extra_lines:
                merged = list(pending.resolution.effect_lines)
                for line in extra_lines:
                    if line not in merged:
                        merged.append(line)
                pending.resolution.effect_lines = tuple(merged[:6])
            _push_log(state, pending.log_text)
            state.last_resolution = pending.resolution
            _check_endings(state)
            if state.modal.kind == "location" and state.modal.primary_id is not None and not location_is_visible(state.modal.primary_id, state):
                close_modal(state)
            pending.settled = True
        return


def dismiss_pending_resolution(state: GameState) -> None:
    pending = state.pending_resolution
    if pending is None:
        return
    if pending.settled and state.assembly.action_id == pending.resolution.action_id:
        clear_assembly(state)
    state.pending_resolution = None


def _consume_inputs(state: GameState, action: ActionDef) -> None:
    for requirement in action.inputs:
        assert requirement_is_slotted(state, requirement), f"Requirement not slotted: {requirement}"
        if requirement.kind == "resource":
            setattr(state.resources, requirement.key, getattr(state.resources, requirement.key) - requirement.amount)
        elif requirement.kind == "item" and requirement.consume:
            state.world.inventory[requirement.key] -= requirement.amount
            if state.world.inventory[requirement.key] <= 0:
                state.world.inventory.pop(requirement.key, None)


def _consume_slotted_card(state: GameState) -> None:
    card_id = state.assembly.slotted_card_id
    if card_id is None:
        return
    if card_id in state.deck.hand:
        state.deck.hand.remove(card_id)
        state.deck.discard_pile.append(card_id)


def _apply_effects(effects: tuple[Effect, ...], state: GameState, rng: RandomSource, extra_lines: list[str] | None = None) -> tuple[str, ...]:
    derived: list[str] = [] if extra_lines is None else extra_lines
    for item in effects:
        _apply_effect(item, state, rng, derived)
    return tuple(derived)


def _apply_effect(item: Effect, state: GameState, rng: RandomSource, extra_lines: list[str]) -> None:
    value = item.value
    if item.kind == "change_health":
        change_health(state, int(value), extra_lines)
        return
    if item.kind == "change_stress":
        change_stress(state, int(value), extra_lines)
        return
    if item.kind == "change_resource":
        assert isinstance(value, str)
        key, raw = value.split(":")
        setattr(state.resources, key, getattr(state.resources, key) + int(raw))
        return
    if item.kind == "give_item":
        assert isinstance(value, str)
        key, raw = value.split(":")
        state.world.inventory[key] = state.world.inventory.get(key, 0) + int(raw)
        return
    if item.kind == "remove_item":
        assert isinstance(value, str)
        key, raw = value.split(":")
        current = state.world.inventory.get(key, 0)
        next_value = max(0, current - int(raw))
        if next_value == 0:
            state.world.inventory.pop(key, None)
        else:
            state.world.inventory[key] = next_value
        return
    if item.kind == "advance_clock":
        assert isinstance(value, str)
        key, raw = value.split(":")
        advance_clock(state, key, int(raw), extra_lines)
        return
    if item.kind == "reveal_location":
        assert isinstance(value, str)
        if value not in state.world.visible_locations:
            state.world.fresh_locations.add(value)
            _push_log(state, f"发现了新的地点：{SCENARIO.locations_by_id[value].title}")
            extra_lines.append(f"发现地点：{SCENARIO.locations_by_id[value].title}")
        state.world.visible_locations.add(value)
        return
    if item.kind == "hide_location":
        assert isinstance(value, str)
        state.world.visible_locations.discard(value)
        return
    if item.kind == "hide_action":
        assert isinstance(value, str)
        state.world.hidden_actions.add(value)
        return
    if item.kind == "show_clock":
        assert isinstance(value, str)
        state.world.progress_clocks[value].visible = True
        return
    if item.kind == "hide_clock":
        assert isinstance(value, str)
        state.world.progress_clocks[value].visible = False
        return
    if item.kind == "reset_hand":
        reset_hand(state, rng)
        return
    if item.kind == "advance_day":
        state.day += 1
        return
    if item.kind == "end_run":
        assert isinstance(value, str)
        if value == "caught":
            state.ending_id = value
            state.ending_title = "被追上了"
            state.ending_body = "你每晚都在争时间，但脚步声终究还是追上了你。"
        else:
            state.ending_id = value
            state.ending_title = "离开这里"
            state.ending_body = "钥匙终于发动了这辆车。你不知道前方是不是更好，但至少已经离开了这里。"
        state.screen = ScreenName.ENDING
        return
    raise AssertionError(f"Unsupported effect kind: {item.kind}")


def reset_hand(state: GameState, rng: RandomSource) -> None:
    while state.deck.hand:
        state.deck.discard_pile.append(state.deck.hand.pop())
    draw_cards(state.deck, rng, HAND_SIZE)


def advance_clock(state: GameState, clock_id: str, amount: int = 1, extra_lines: list[str] | None = None) -> None:
    spec = SCENARIO.clocks_by_id[clock_id]
    clock_state = state.world.progress_clocks[clock_id]
    before = clock_state.value
    clock_state.value = min(spec.segments, clock_state.value + amount)
    clock_state.visible = True
    for threshold in spec.thresholds:
        if before < threshold.at <= clock_state.value:
            _apply_effects(threshold.effects, state, RandomSource(state.seed), extra_lines)


def change_health(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    state.attributes.health = max(0, min(state.attributes.max_health, state.attributes.health + amount))
    sync_trauma_cards_with_health(state)
    if state.attributes.health <= 0:
        state.ending_id = "collapse"
        state.ending_title = "倒下了"
        state.ending_body = "你最终还是没能撑住。"
        state.screen = ScreenName.ENDING


def change_stress(state: GameState, amount: int, extra_lines: list[str] | None = None) -> None:
    if amount <= 0:
        state.attributes.stress = max(0, state.attributes.stress + amount)
        return
    before = state.attributes.stress
    state.attributes.stress = min(state.attributes.max_stress, state.attributes.stress + amount)
    if before >= state.attributes.max_stress or state.attributes.stress >= state.attributes.max_stress:
        if extra_lines is not None:
            extra_lines.append("压力已满，生命 -1")
        change_health(state, -1, extra_lines)
        _push_log(state, "压力已经满了，身体替你付了代价。")


def sync_trauma_cards_with_health(state: GameState) -> None:
    missing = state.attributes.max_health - state.attributes.health
    target_trauma = missing // TRAUMA_HEALTH_STEP
    current = _count_card(state, TRAUMA_CARD_ID)
    if current < target_trauma:
        for _ in range(target_trauma - current):
            state.deck.draw_pile.append(TRAUMA_CARD_ID)
    elif current > target_trauma:
        _remove_specific_cards(state, TRAUMA_CARD_ID, current - target_trauma)


def _count_card(state: GameState, card_id: str) -> int:
    return sum(pile.count(card_id) for pile in (state.deck.hand, state.deck.draw_pile, state.deck.discard_pile))


def _remove_specific_cards(state: GameState, card_id: str, amount: int) -> None:
    remaining = amount
    for pile in (state.deck.draw_pile, state.deck.discard_pile, state.deck.hand):
        keep: list[str] = []
        for existing in pile:
            if remaining > 0 and existing == card_id:
                remaining -= 1
                continue
            keep.append(existing)
        pile[:] = keep
        if remaining == 0:
            return
    assert remaining == 0, f"failed to remove enough {card_id}: {remaining}"


def _check_endings(state: GameState) -> None:
    if state.screen == ScreenName.ENDING:
        return
    pursuit = state.world.progress_clocks["pursuit"]
    if pursuit.value >= SCENARIO.clocks_by_id["pursuit"].segments:
        state.ending_id = "caught"
        state.ending_title = "被追上了"
        state.ending_body = "你每晚都在争时间，但脚步声终究还是追上了你。"
        state.screen = ScreenName.ENDING


def _compose_resolution_text(result: ResultType, effect_lines: tuple[str, ...], fallback: str) -> str:
    if effect_lines:
        prefix = {
            ResultType.SUCCESS: "成功",
            ResultType.COST: "代价成功",
            ResultType.FAIL: "失败",
        }[result]
        return f"{prefix}：{'，'.join(effect_lines[:2])}"
    return fallback


def _describe_effects(effects: tuple[Effect, ...], action_id: str) -> tuple[str, ...]:
    lines: list[str] = []
    for item in effects:
        value = item.value
        if item.kind == "change_health":
            amount = int(value)
            lines.append(f"生命 {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_stress":
            amount = int(value)
            lines.append(f"压力 {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "change_resource":
            assert isinstance(value, str)
            key, raw = value.split(":")
            amount = int(raw)
            label = "金钱" if key == "money" else "烟卷"
            lines.append(f"{label} {'+' if amount >= 0 else ''}{amount}")
        elif item.kind == "give_item":
            assert isinstance(value, str)
            key, raw = value.split(":")
            label = _item_label(key)
            lines.append(f"获得 {label}" if int(raw) == 1 else f"获得 {label} x{raw}")
        elif item.kind == "remove_item":
            assert isinstance(value, str)
            key, raw = value.split(":")
            label = _item_label(key)
            lines.append(f"失去 {label}" if int(raw) == 1 else f"失去 {label} x{raw}")
        elif item.kind == "advance_clock":
            assert isinstance(value, str)
            key, raw = value.split(":")
            spec = SCENARIO.clocks_by_id[key]
            if "action_use" in spec.tags:
                continue
            lines.append(f"{spec.title} +{raw}")
        elif item.kind == "reveal_location":
            assert isinstance(value, str)
            lines.append(f"发现地点：{SCENARIO.locations_by_id[value].title}")
        elif item.kind == "hide_location":
            assert isinstance(value, str)
            lines.append(f"地点关闭：{SCENARIO.locations_by_id[value].title}")
        elif item.kind == "hide_action" and value == action_id:
            lines.append("此行动结束")
        elif item.kind == "reset_hand":
            lines.append("重抽手牌")
        elif item.kind == "advance_day":
            lines.append("进入下一天")
        elif item.kind == "end_run":
            lines.append("达成结局")
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
    return tuple(deduped[:4])


def _item_label(item_id: str) -> str:
    if item_id == "clothes":
        return "华美衣服"
    if item_id == "car_key":
        return "车钥匙"
    if item_id == "repair_case_item":
        return "任务道具"
    if item_id == "gun":
        return "枪"
    return item_id


def claim_growth(state: GameState, growth_id: str) -> None:
    growth = GROWTH_DEFS[growth_id]
    _apply_effects(growth.effects, state, RandomSource(state.seed))
    state.unlocked_growths.add(growth_id)
    state.growth_points = max(0, state.growth_points - 1)
    state.pending_growth_choices.clear()
    close_modal(state)


def location_for_action(action_id: str) -> str | None:
    for location_id, action_ids in SCENARIO.actions_by_location.items():
        if action_id in action_ids:
            return location_id
    raise AssertionError(f"Unknown action owner: {action_id}")
