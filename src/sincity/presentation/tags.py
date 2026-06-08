from __future__ import annotations

from sincity.model.defs import ActionDef, InputRequirement
from sincity.model.items import ITEMS
from sincity.model.state import GameState


def condition_labels(conditions, state: GameState | None = None) -> tuple[str, ...]:
    labels: list[str] = []
    for item in conditions:
        from sincity.game.conditions import evaluate_condition
        if state is not None and evaluate_condition(item, state):
            continue
        if item.label:
            labels.append(item.label)
            continue
        if item.kind == "has_item" and isinstance(item.value, str):
            key, _, raw_amount = item.value.partition(":")
            amount = int(raw_amount) if raw_amount else 1
            found = ITEMS.get(key)
            title = found.name if found else key
            labels.append(f"需要 {title}" if amount == 1 else f"需要 {title} x{amount}")
        elif item.kind == "field_at_least" and isinstance(item.value, str):
            key, raw = item.value.split(":", 1)
            found = ITEMS.get(key)
            title = found.name if found else key
            labels.append(f"需要 {title} {raw}")
    return tuple(labels)


def requirement_labels(requirements: tuple[InputRequirement, ...]) -> tuple[str, ...]:
    labels: list[str] = []
    for requirement in requirements:
        if requirement.kind == "item" and not requirement.consume:
            found = ITEMS.get(requirement.key)
            label = requirement.label or (found.name if found else requirement.key)
            labels.append(f"需要 {label}")
    return tuple(labels)


def action_starts_encounter(action: ActionDef) -> bool:
    effects = list(action.effects)
    if action.check is not None:
        effects.extend(action.check.success.effects)
        effects.extend(action.check.cost.effects)
        effects.extend(action.check.fail.effects)
    return any(effect.kind == "start_encounter" for effect in effects)


def action_corner_labels(action: ActionDef, state: GameState | None = None) -> tuple[str, ...]:
    labels = list(condition_labels(action.conditions, state))
    if action_starts_encounter(action):
        labels.append("外出")
    labels.extend(requirement_labels(action.inputs))
    return tuple(labels)


def location_corner_labels(location) -> tuple[str, ...]:
    return condition_labels(location.conditions)


def location_status_labels(location_id: str, location, state: GameState) -> tuple[str, ...]:
    labels = list(location_corner_labels(location))
    if location_id in state.world.fresh_locations:
        labels.insert(0, "新")
    return tuple(labels)
