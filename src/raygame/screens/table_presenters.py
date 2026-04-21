from __future__ import annotations

from dataclasses import dataclass

from raygame.model.defs import ActionDef, InputRequirement, LocationNode
from raygame.model.enums import ResultType, RISK_LABELS, SUIT_LABELS
from raygame.model.state import GameState, PendingResolutionState
from raygame.rules import (
    action_can_accept_selected_input,
    action_is_available,
    action_is_visible,
    action_ready_to_execute,
    action_slot_ready,
    location_is_available,
    location_is_visible,
    slot_effective_value,
)
from raygame.rules.judgment import RESULT_TABLE, clamp_action_value

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
        metadata = (suits, RISK_LABELS[action.check.risk])
    return PresentedActionCard(
        action=action,
        card=TableCardModel(
            title=action.title,
            body=action.description,
            labels=action_corner_labels(action),
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
    if action.check is not None:
        slots.append(
            ActionSlotModel(
                key="check",
                label="精神槽位",
                filled=action_slot_ready(state, action, check_slot=True),
                receptive=available and (not locked) and action_can_accept_selected_input(state, action, check_slot=True),
                disabled=not available,
                slot_kind="check",
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
    if action.check is None and not action.inputs and executable:
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
        value = slot_effective_value(state, state.assembly.slotted_card_id, action.check)
        return ActionAttachmentModel(
            mode="preview",
            title=f"状态档 {value}",
            row=RESULT_TABLE[clamp_action_value(value)],
            value=value,
            can_execute=action_ready_to_execute(action, state),
        )
    if action.check is not None:
        return ActionAttachmentModel(
            mode="hint",
            title="先从下方选一个精神槽位，再把它放进卡槽。",
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
