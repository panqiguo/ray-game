from __future__ import annotations

from dataclasses import dataclass

from raygame.content import SCENARIO
from raygame.model.defs import ActionDef, InputRequirement, LocationNode
from raygame.model.enums import ResultType, RISK_LABELS, SUIT_LABELS
from raygame.model.state import GameState, PendingResolutionState
from raygame.rules import (
    action_can_accept_selected_input,
    action_is_available,
    action_is_visible,
    action_ready_to_execute,
    action_slot_ready,
    get_action,
    location_is_visible,
)
from raygame.rules.judgment import RESULT_TABLE, clamp_action_value, compute_action_value

from .ui_cards import ACTION_CARD, TABLE_CARD, WORLD_CARD, TableCardModel
from .ui_tags import action_corner_labels, location_status_labels


@dataclass(frozen=True)
class PresentedLocationCard:
    location_id: str
    location: LocationNode
    card: TableCardModel


@dataclass(frozen=True)
class ActionSlotModel:
    key: str
    label: str
    filled: bool
    receptive: bool
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


def present_world_location_cards(state: GameState) -> tuple[PresentedLocationCard, ...]:
    cards: list[PresentedLocationCard] = []
    resolving = _is_resolving(state)
    for location_id in SCENARIO.root_location_ids:
        location = SCENARIO.locations_by_id[location_id]
        if not _location_is_visible(location_id, state):
            continue
        cards.append(
            PresentedLocationCard(
                location_id=location_id,
                location=location,
                card=TableCardModel(
                    title=location.title,
                    body=location.description,
                    labels=location_status_labels(location_id, location, state),
                    clock_ids=SCENARIO.location_clock_ids.get(location_id, ()),
                    active=state.modal.kind == "location" and state.modal.primary_id == location_id,
                    disabled=resolving,
                    style=WORLD_CARD,
                ),
            )
        )
    return tuple(cards)


def present_child_location_cards(state: GameState, location_ids: tuple[str, ...]) -> tuple[PresentedLocationCard, ...]:
    resolving = _is_resolving(state)
    cards: list[PresentedLocationCard] = []
    for location_id in location_ids:
        location = SCENARIO.locations_by_id[location_id]
        if not _location_is_visible(location_id, state):
            continue
        cards.append(
            PresentedLocationCard(
                location_id=location_id,
                location=location,
                card=TableCardModel(
                    title=location.title,
                    body=location.description,
                    labels=location_status_labels(location_id, location, state),
                    clock_ids=SCENARIO.location_clock_ids.get(location_id, ()),
                    active=state.modal.kind == "location" and state.modal.primary_id == location_id,
                    disabled=resolving,
                    style=TABLE_CARD,
                ),
            )
        )
    return tuple(cards)


def present_action_cards(state: GameState, location: LocationNode) -> tuple[PresentedActionCard, ...]:
    return tuple(
        _present_action_card(state, get_action(action_id))
        for action_id in SCENARIO.actions_by_location[location.id]
        if action_is_visible(get_action(action_id), state)
    )


def present_location_clock_ids(location_id: str) -> tuple[str, ...]:
    return SCENARIO.location_clock_ids.get(location_id, ())


def _present_action_card(state: GameState, action: ActionDef) -> PresentedActionCard:
    active = state.assembly.action_id == action.id
    available = action_is_available(action, state)
    pending = state.pending_resolution if state.pending_resolution and state.pending_resolution.resolution.action_id == action.id else None
    metadata: tuple[str, ...] = ()
    if action.check is not None:
        suits = " / ".join(SUIT_LABELS[suit] for suit in action.check.suits)
        metadata = (f"契合 {suits}", f"风险 {RISK_LABELS[action.check.risk]}")
    return PresentedActionCard(
        action=action,
        card=TableCardModel(
            title=action.title,
            body=action.description,
            labels=action_corner_labels(action),
            clock_ids=SCENARIO.action_clock_ids.get(action.id, ()),
            active=active,
            disabled=not available,
            style=ACTION_CARD,
            metadata=metadata,
            interactive=False,
        ),
        slots=_present_action_slots(state, action, pending is not None),
        attachment=_present_action_attachment(state, action, pending),
    )


def _present_action_slots(state: GameState, action: ActionDef, has_pending: bool) -> tuple[ActionSlotModel, ...]:
    locked = state.pending_resolution is not None and not has_pending
    slots: list[ActionSlotModel] = []
    if action.check is not None:
        slots.append(
            ActionSlotModel(
                key="check",
                label="手牌槽",
                filled=action_slot_ready(state, action, check_slot=True),
                receptive=(not locked) and action_can_accept_selected_input(state, action, check_slot=True),
                slot_kind="check",
            )
        )
    for requirement in action.inputs:
        slots.append(
            ActionSlotModel(
                key=f"{requirement.kind}:{requirement.key}",
                label=_slot_label(requirement),
                filled=action_slot_ready(state, action, requirement),
                receptive=(not locked) and action_can_accept_selected_input(state, action, requirement),
                slot_kind="requirement",
                requirement=requirement,
            )
        )
    if action.check is None and not action.inputs:
        slots.append(
            ActionSlotModel(
                key="auto",
                label="自动就绪",
                filled=state.assembly.action_id == action.id,
                receptive=(not state.assembly.action_id == action.id) and (not locked),
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
    if action.check is not None and state.assembly.slotted_card_id is not None:
        value = compute_action_value(state.assembly.slotted_card_id, action.check)
        return ActionAttachmentModel(
            mode="preview",
            title=f"行动值 {value}",
            row=RESULT_TABLE[clamp_action_value(value)],
            value=value,
            can_execute=action_ready_to_execute(action, state),
        )
    if action.check is not None:
        return ActionAttachmentModel(
            mode="hint",
            title="先从下方选一张手牌，再把它放进卡槽。",
            can_execute=False,
        )
    return ActionAttachmentModel(
        mode="preview",
        title="条件已满足后即可执行。",
        can_execute=action_ready_to_execute(action, state),
    )


def _slot_label(requirement: InputRequirement) -> str:
    if requirement.kind == "resource":
        return f"{requirement.label} x{requirement.amount}"
    if requirement.kind == "item":
        return requirement.label
    return requirement.label or "卡槽"


def _is_resolving(state: GameState) -> bool:
    return state.pending_resolution is not None and not state.pending_resolution.settled


def _location_is_visible(location_id: str, state: GameState) -> bool:
    return location_is_visible(location_id, state)
