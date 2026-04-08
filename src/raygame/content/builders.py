from __future__ import annotations

from dataclasses import dataclass

from raygame.model.defs import (
    ActionDef,
    CheckDef,
    ClockThreshold,
    CompiledScenario,
    Condition,
    Effect,
    InputRequirement,
    LocationNode,
    OutcomeDef,
    ProgressClockDisplay,
    ProgressClockSpec,
    ScenarioDef,
)
from raygame.model.enums import Risk, ScreenName, Suit


@dataclass(frozen=True)
class ActionBundle:
    action: ActionDef
    clocks: tuple[ProgressClockSpec, ...] = ()


def condition(kind: str, value: str | int | bool | tuple[str, ...] | None = None) -> Condition:
    return Condition(kind=kind, value=value)


def effect(kind: str, value: str | int | bool | tuple[str, ...] | None = None) -> Effect:
    return Effect(kind=kind, value=value)


def outcome(text: str, *effects_: Effect, completes: bool = True) -> OutcomeDef:
    return OutcomeDef(text=text, effects=tuple(effects_), completes=completes)


def check(
    *,
    suits: tuple[Suit, ...],
    difficulty: int,
    risk: Risk,
    success: OutcomeDef,
    cost: OutcomeDef,
    fail: OutcomeDef,
) -> CheckDef:
    return CheckDef(suits=suits, difficulty=difficulty, risk=risk, success=success, cost=cost, fail=fail)


def resource(key: str, amount: int, label: str = "") -> InputRequirement:
    return InputRequirement(kind="resource", key=key, amount=amount, label=label or key, consume=True)


def item_input(key: str, amount: int = 1, label: str = "", *, consume: bool = True) -> InputRequirement:
    return InputRequirement(kind="item", key=key, amount=amount, label=label or key, consume=consume)


def any_card(label: str = "手牌") -> InputRequirement:
    return InputRequirement(kind="card", key="any", amount=1, label=label, consume=True)


def negative_card(label: str = "负面牌") -> InputRequirement:
    return InputRequirement(kind="card", key="negative", amount=1, label=label, consume=True)


def threshold(at: int, *effects_: Effect) -> ClockThreshold:
    return ClockThreshold(at=at, effects=tuple(effects_))


def display_auto() -> ProgressClockDisplay:
    return ProgressClockDisplay(scope="auto")


def display_global() -> ProgressClockDisplay:
    return ProgressClockDisplay(scope="global")


def display_location(location_id: str) -> ProgressClockDisplay:
    return ProgressClockDisplay(scope="location", anchor_id=location_id)


def display_action(action_id: str) -> ProgressClockDisplay:
    return ProgressClockDisplay(scope="action", anchor_id=action_id)


def clock(
    *,
    id: str,
    title: str,
    segments: int,
    thresholds: tuple[ClockThreshold, ...] = (),
    tags: tuple[str, ...] = (),
    hidden: bool = False,
    display: ProgressClockDisplay | None = None,
) -> ProgressClockSpec:
    return ProgressClockSpec(
        id=id,
        title=title,
        segments=segments,
        thresholds=thresholds,
        tags=tags,
        hidden=hidden,
        display=display or display_auto(),
    )


def action(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    check: CheckDef | None = None,
    inputs: tuple[InputRequirement, ...] = (),
    effects: tuple[Effect, ...] = (),
    conditions: tuple[Condition, ...] = (),
    linked_clock_ids: tuple[str, ...] = (),
) -> ActionDef:
    return ActionDef(
        id=id,
        title=title,
        description=description,
        screen=screen,
        check=check,
        inputs=inputs,
        effects=effects,
        conditions=conditions,
        linked_clock_ids=linked_clock_ids,
    )


def location(
    *,
    id: str,
    title: str,
    description: str,
    position: tuple[int, int] | None = None,
    actions: tuple[ActionDef | ActionBundle, ...] = (),
    children: tuple[LocationNode, ...] = (),
    conditions: tuple[Condition, ...] = (),
) -> tuple[LocationNode, tuple[ProgressClockSpec, ...]]:
    action_defs: list[ActionDef] = []
    clocks: list[ProgressClockSpec] = []
    for entry in actions:
        if isinstance(entry, ActionBundle):
            action_defs.append(entry.action)
            clocks.extend(entry.clocks)
        else:
            action_defs.append(entry)
    return (
        LocationNode(
            id=id,
            title=title,
            description=description,
            position=position,
            actions=tuple(action_defs),
            children=children,
            conditions=conditions,
        ),
        tuple(clocks),
    )


def scenario(
    *,
    id: str,
    title: str,
    screen: ScreenName,
    roots: tuple[LocationNode, ...],
    clocks: tuple[ProgressClockSpec, ...],
    initial_visible_locations: tuple[str, ...],
    initial_visible_clocks: tuple[str, ...],
    initial_health: int,
    initial_stress: int,
    initial_money: int,
    initial_cigarettes: int,
    initial_inventory: dict[str, int] | None = None,
    initial_growth_choices: tuple[str, ...] = (),
) -> ScenarioDef:
    return ScenarioDef(
        id=id,
        title=title,
        screen=screen,
        roots=roots,
        clocks=clocks,
        initial_visible_locations=initial_visible_locations,
        initial_visible_clocks=initial_visible_clocks,
        initial_health=initial_health,
        initial_stress=initial_stress,
        initial_money=initial_money,
        initial_cigarettes=initial_cigarettes,
        initial_inventory=initial_inventory or {},
        initial_growth_choices=initial_growth_choices,
    )


def single_use_action(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    check: CheckDef | None = None,
    inputs: tuple[InputRequirement, ...] = (),
    effects: tuple[Effect, ...] = (),
    conditions: tuple[Condition, ...] = (),
) -> ActionBundle:
    return ActionBundle(
        action=action(
            id=id,
            title=title,
            description=description,
            screen=screen,
            check=check,
            inputs=inputs,
            effects=effects + (effect("hide_action", id),),
            conditions=conditions,
        ),
    )


def limited_use_action(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    uses: int,
    check: CheckDef | None = None,
    inputs: tuple[InputRequirement, ...] = (),
    effects: tuple[Effect, ...] = (),
    conditions: tuple[Condition, ...] = (),
) -> ActionBundle:
    clock_id = f"{id}_uses"
    return ActionBundle(
        action=action(
            id=id,
            title=title,
            description=description,
            screen=screen,
            check=check,
            inputs=inputs,
            effects=effects + (effect("advance_clock", f"{clock_id}:1"),),
            conditions=conditions,
            linked_clock_ids=(clock_id,),
        ),
        clocks=(
            clock(
                id=clock_id,
                title=title,
                segments=uses,
                thresholds=(threshold(uses, effect("hide_action", id)),),
                tags=("action_use",),
                hidden=True,
                display=display_action(id),
            ),
        ),
    )


def explore_action(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    clock_id: str,
    clock_title: str,
    segments: int,
    check: CheckDef,
    thresholds: tuple[ClockThreshold, ...],
    conditions: tuple[Condition, ...] = (),
) -> ActionBundle:
    return ActionBundle(
        action=action(
            id=id,
            title=title,
            description=description,
            screen=screen,
            check=check,
            effects=(effect("advance_clock", f"{clock_id}:1"),),
            conditions=conditions,
            linked_clock_ids=(clock_id,),
        ),
        clocks=(
            clock(
                id=clock_id,
                title=clock_title,
                segments=segments,
                thresholds=thresholds,
                tags=("explore",),
                display=display_auto(),
            ),
        ),
    )


def rest_action(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    inputs: tuple[InputRequirement, ...] = (),
    effects: tuple[Effect, ...] = (),
    conditions: tuple[Condition, ...] = (),
) -> ActionDef:
    return action(
        id=id,
        title=title,
        description=description,
        screen=screen,
        inputs=inputs,
        effects=effects + (
            effect("reset_hand", True),
            effect("advance_clock", "pursuit:1"),
            effect("advance_day", True),
        ),
        conditions=conditions,
        linked_clock_ids=("pursuit",),
    )


def delivery_action(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    inputs: tuple[InputRequirement, ...],
    effects: tuple[Effect, ...],
    conditions: tuple[Condition, ...] = (),
) -> ActionDef:
    return action(
        id=id,
        title=title,
        description=description,
        screen=screen,
        inputs=inputs,
        effects=effects,
        conditions=conditions,
    )


def shop_purchase(
    *,
    id: str,
    title: str,
    description: str,
    screen: ScreenName,
    price: int,
    item_id: str,
    item_label: str,
    single_use: bool = True,
) -> ActionDef | ActionBundle:
    base = dict(
        id=id,
        title=title,
        description=description,
        screen=screen,
        inputs=(resource("money", price, "金币"),),
        effects=(effect("give_item", f"{item_id}:1"),),
        conditions=(condition("inventory_below", f"{item_id}:1"),),
    )
    if single_use:
        return single_use_action(**base)
    return action(**base)


def compile_scenario(scenario: ScenarioDef) -> CompiledScenario:
    locations_by_id: dict[str, LocationNode] = {}
    parent_by_id: dict[str, str | None] = {}
    actions_by_id: dict[str, ActionDef] = {}
    actions_by_location: dict[str, tuple[str, ...]] = {}
    root_ids: list[str] = []

    def walk(node: LocationNode, parent_id: str | None, depth: int) -> None:
        assert depth <= 2, f"Location nesting exceeds 2: {node.id}"
        assert node.id not in locations_by_id, f"Duplicate location id {node.id}"
        locations_by_id[node.id] = node
        parent_by_id[node.id] = parent_id
        actions_by_location[node.id] = tuple(action.id for action in node.actions)
        for action_def in node.actions:
            assert action_def.id not in actions_by_id, f"Duplicate action id {action_def.id}"
            actions_by_id[action_def.id] = action_def
        for child in node.children:
            walk(child, node.id, depth + 1)

    for root in scenario.roots:
        root_ids.append(root.id)
        walk(root, None, 1)

    clocks_by_id: dict[str, ProgressClockSpec] = {}
    for spec in scenario.clocks:
        assert spec.id not in clocks_by_id, f"Duplicate clock id {spec.id}"
        clocks_by_id[spec.id] = spec

    global_clock_ids: list[str] = []
    location_clock_ids: dict[str, list[str]] = {}
    action_clock_ids: dict[str, list[str]] = {}

    for clock_id, spec in clocks_by_id.items():
        scope, anchor_id = _infer_clock_display(spec, actions_by_id, actions_by_location, parent_by_id)
        if scope == "global":
            global_clock_ids.append(clock_id)
        elif scope == "location":
            assert anchor_id is not None
            location_clock_ids.setdefault(anchor_id, []).append(clock_id)
        elif scope == "action":
            assert anchor_id is not None
            action_clock_ids.setdefault(anchor_id, []).append(clock_id)
        else:
            raise AssertionError(f"Unsupported clock display scope: {scope}")

    return CompiledScenario(
        id=scenario.id,
        title=scenario.title,
        screen=scenario.screen,
        root_location_ids=tuple(root_ids),
        locations_by_id=locations_by_id,
        parent_by_id=parent_by_id,
        actions_by_id=actions_by_id,
        actions_by_location=actions_by_location,
        clocks_by_id=clocks_by_id,
        global_clock_ids=tuple(global_clock_ids),
        location_clock_ids={key: tuple(value) for key, value in location_clock_ids.items()},
        action_clock_ids={key: tuple(value) for key, value in action_clock_ids.items()},
        initial_visible_locations=scenario.initial_visible_locations,
        initial_visible_clocks=scenario.initial_visible_clocks,
        initial_health=scenario.initial_health,
        initial_stress=scenario.initial_stress,
        initial_money=scenario.initial_money,
        initial_cigarettes=scenario.initial_cigarettes,
        initial_inventory=dict(scenario.initial_inventory),
        initial_growth_choices=scenario.initial_growth_choices,
    )


def _infer_clock_display(
    spec: ProgressClockSpec,
    actions_by_id: dict[str, ActionDef],
    actions_by_location: dict[str, tuple[str, ...]],
    parent_by_id: dict[str, str | None],
) -> tuple[str, str | None]:
    if spec.display.scope != "auto":
        return spec.display.scope, spec.display.anchor_id

    owners = [action_id for action_id, action_def in actions_by_id.items() if spec.id in action_def.linked_clock_ids]
    if not owners:
        return "global", None
    if len(owners) == 1:
        return "action", owners[0]

    action_locations: list[str] = []
    for location_id, action_ids in actions_by_location.items():
        if any(action_id in owners for action_id in action_ids):
            action_locations.append(location_id)
    unique_locations = sorted(set(action_locations))
    if len(unique_locations) == 1:
        return "location", unique_locations[0]

    common = _lowest_common_location(unique_locations, parent_by_id)
    return ("location", common) if common is not None else ("global", None)


def _lowest_common_location(location_ids: list[str], parent_by_id: dict[str, str | None]) -> str | None:
    if not location_ids:
        return None
    chains: list[list[str]] = []
    for location_id in location_ids:
        chain = [location_id]
        parent = parent_by_id[location_id]
        while parent is not None:
            chain.append(parent)
            parent = parent_by_id[parent]
        chains.append(list(reversed(chain)))
    shortest = min(len(chain) for chain in chains)
    common: str | None = None
    for index in range(shortest):
        candidate = chains[0][index]
        if all(chain[index] == candidate for chain in chains[1:]):
            common = candidate
        else:
            break
    return common
