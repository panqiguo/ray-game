from __future__ import annotations

from dataclasses import dataclass

from sincity.model.defs import ActionDef, InputRequirement, LocationNode
from sincity.model.enums import ResultType, RISK_LABELS, SUIT_LABELS
from sincity.model.state import GameState, PendingResolutionState
from sincity.rules import (
    action_can_accept_selected_input,
    action_requires_energy_slot,
    action_is_available,
    action_is_visible,
    action_ready_to_execute,
    action_slot_ready,
    first_usable_energy_slot,
    location_is_available,
    location_is_visible,
    slot_effective_value,
    slot_value_breakdown,
)
from sincity.rules.judgment import RESULT_TABLE, clamp_action_value

from .ui_cards import ACTION_CARD, TABLE_CARD, TableCardModel
from .ui_tags import action_corner_labels, location_status_labels


@dataclass(frozen=True)
class PresentedLocationCard:
    location_id: str
    location: LocationNode
    card: TableCardModel
    position: tuple[int, int] | None = None


@dataclass(frozen=True)
class ActionSlotModel:
    key: str
    label: str
    filled: bool
    receptive: bool
    disabled: bool
    slot_kind: str
    requirement: InputRequirement | None = None


@dataclass(frozen=True)
class ActionAttachmentModel:
    mode: str
    title: str
    hint: str = ""
    row: tuple[ResultType, ...] = ()
    value: int | None = None
    result_text: str = ""
    effect_text: str = ""
    can_execute: bool = False


@dataclass(frozen=True)
class PresentedActionCard:
    action: ActionDef
    card: TableCardModel
    slots: tuple[ActionSlotModel, ...]
    attachment: ActionAttachmentModel | None
    position: tuple[int, int] | None = None


def is_resolving(state: GameState) -> bool:
    return state.pending_resolution is not None and not state.pending_resolution.settled


def present_location_cards(
    state: GameState,
    content,
    location_ids: tuple[str, ...],
) -> tuple[PresentedLocationCard, ...]:
    cards: list[PresentedLocationCard] = []
    for location_id in location_ids:
        location = content.locations_by_id[location_id]
        if not location_is_visible(location_id, state):
            continue
        clock_ids = getattr(content, "location_clock_ids", {}).get(location_id, ())
        cards.append(
            PresentedLocationCard(
                location_id=location_id,
                location=location,
                position=location.position,
                card=TableCardModel(
                    title=location.title,
                    body=location.description,
                    labels=location_status_labels(location_id, location, state),
                    clock_ids=clock_ids,
                    active=state.modal.kind == "location" and state.modal.primary_id == location_id,
                    disabled=is_resolving(state) or not location_is_available(location_id, state),
                    style=TABLE_CARD,
                ),
            )
        )
    return tuple(cards)


def present_action_cards_for_location(
    state: GameState,
    content,
    location: LocationNode,
) -> tuple[PresentedActionCard, ...]:
    return tuple(
        present_action_card(state, content.actions_by_id[action_id])
        for action_id in content.actions_by_location[location.id]
        if action_is_visible(content.actions_by_id[action_id], state)
    )


def present_action_card(state: GameState, action: ActionDef) -> PresentedActionCard:
    active = state.assembly.action_id == action.id
    available = action_is_available(action, state)
    pending = state.pending_resolution if state.pending_resolution and state.pending_resolution.resolution.action_id == action.id else None
    metadata: tuple[str, ...] = ()
    if action.check is not None:
        suits = "通用" if not action.check.suits else " / ".join(SUIT_LABELS[suit] for suit in action.check.suits)
        metadata = (suits, RISK_LABELS[action.check.risk], *_check_value_tags(state, action))
    return PresentedActionCard(
        action=action,
        card=TableCardModel(
            title=action.title,
            body=action.description,
            labels=action_corner_labels(action, state),
            clock_ids=(),
            active=active,
            disabled=not available,
            style=ACTION_CARD,
            metadata=metadata,
            interactive=False,
        ),
        slots=_present_action_slots(state, action, pending is not None),
        attachment=_present_action_attachment(state, action, pending),
        position=action.position,
    )


def _present_action_slots(state: GameState, action: ActionDef, has_pending: bool) -> tuple[ActionSlotModel, ...]:
    locked = state.pending_resolution is not None and not has_pending
    available = action_is_available(action, state)
    executable = action.check is not None or bool(action.effects)
    slots: list[ActionSlotModel] = []
    if action_requires_energy_slot(action):
        slots.append(
            ActionSlotModel(
                key="check",
                label="行动卡",
                filled=action_slot_ready(state, action, energy_slot=True),
                receptive=available and (not locked) and first_usable_energy_slot(state, action) is not None,
                disabled=not available,
                slot_kind="energy",
            )
        )
    for requirement in action.inputs:
        slots.append(
            ActionSlotModel(
                key=f"{requirement.kind}:{requirement.key}",
                label=_slot_label(requirement),
                filled=action_slot_ready(state, action, requirement),
                receptive=available and (not locked) and action_can_accept_selected_input(state, action, requirement),
                disabled=not available,
                slot_kind="requirement",
                requirement=requirement,
            )
        )
    if action.check is None and not action_requires_energy_slot(action) and not action.inputs and executable:
        slots.append(
            ActionSlotModel(
                key="auto",
                label="自动就绪",
                filled=state.assembly.action_id == action.id,
                receptive=available and (not state.assembly.action_id == action.id) and (not locked),
                disabled=not available,
                slot_kind="auto",
            )
        )
    return tuple(slots)


def _present_action_attachment(
    state: GameState,
    action: ActionDef,
    pending: PendingResolutionState | None,
) -> ActionAttachmentModel | None:
    if pending is not None:
        resolution = pending.resolution
        row = RESULT_TABLE[clamp_action_value(resolution.value)] if resolution.value is not None else ()
        return ActionAttachmentModel(
            mode="pending" if not pending.settled else "settled",
            title="判定中" if resolution.result is not None and resolution.value is not None else "执行中",
            hint="结果会在这张卡下面落定。" if not pending.settled else "",
            row=row,
            value=resolution.value,
            result_text=resolution.text if pending.settled else "",
            effect_text=" | ".join(resolution.effect_lines[:2]) if pending.settled and resolution.effect_lines else "",
        )
    if state.assembly.action_id != action.id:
        return None
    if action.check is None and not action.effects:
        return None
    if action.check is not None and state.assembly.slotted_card_id is not None:
        breakdown = slot_value_breakdown(state, state.assembly.slotted_card_id, action.check)
        value = breakdown.total
        return ActionAttachmentModel(
            mode="preview",
            title=f"状态档 {value}",
            hint=_format_value_breakdown(breakdown),
            row=RESULT_TABLE[clamp_action_value(value)],
            value=value,
            can_execute=action_ready_to_execute(action, state),
        )
    if action.check is not None:
        return ActionAttachmentModel(
            mode="hint",
            title="先放入一张行动卡。",
            can_execute=False,
        )
    return ActionAttachmentModel(
        mode="preview",
        title="条件已满足后即可执行。",
        can_execute=action_ready_to_execute(action, state),
    )


def _slot_label(requirement: InputRequirement) -> str:
    label = requirement.label or requirement.key
    if requirement.kind == "item" and requirement.amount > 1:
        return f"{label} {requirement.amount}"
    return label


def _check_value_tags(state: GameState, action: ActionDef) -> tuple[str, ...]:
    if action.check is None:
        return ()
    labels: list[str] = []
    owner_id = "cole"
    values = state.deck.spirit_values
    for suit in action.check.suits:
        key = suit.value
        value = values.get(key, 0) if owner_id == "cole" else 0
        if value != 0:
            labels.append(f"{SUIT_LABELS[suit]} +{value}" if value > 0 else f"{SUIT_LABELS[suit]} {value}")
    for modifier in action.check.modifiers:
        if modifier.active and modifier.value != 0:
            labels.append(f"{modifier.label} +{modifier.value}" if modifier.value > 0 else f"{modifier.label} {modifier.value}")
    return tuple(labels)


def _format_value_breakdown(breakdown) -> str:
    chunks = [f"卡牌 {breakdown.base}"]
    for part in breakdown.parts:
        chunks.append(f"{part.label} +{part.value}" if part.value > 0 else f"{part.label} {part.value}")
    return " · ".join(chunks)
