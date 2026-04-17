from __future__ import annotations

from dataclasses import dataclass

from raygame.model.state import GameState
from raygame.rules import action_is_visible, current_world_snapshot

from .table_presenters import (
    PresentedActionCard,
    PresentedLocationCard,
    present_action_card,
    present_action_cards_for_location,
    present_location_cards,
)
from .ui_cards import WORLD_CARD, TableCardModel
from .ui_tags import location_status_labels


@dataclass(frozen=True)
class PresentedWorldObject:
    kind: str
    position: tuple[int, int]
    card: TableCardModel
    scale_bias: float = 1.0
    location_id: str | None = None
    action_card: PresentedActionCard | None = None


def present_world_objects(state: GameState) -> tuple[PresentedWorldObject, ...]:
    snapshot = current_world_snapshot(state)
    cards: list[PresentedWorldObject] = []
    for presented in present_location_cards(state, snapshot, snapshot.root_location_ids):
        assert presented.position is not None
        cards.append(
            PresentedWorldObject(
                kind="location",
                position=presented.position,
                location_id=presented.location_id,
                scale_bias=1.0,
                card=TableCardModel(
                    title=presented.location.title,
                    body=presented.location.description,
                    labels=location_status_labels(presented.location_id, presented.location, state),
                    clock_ids=snapshot.location_clock_ids.get(presented.location_id, ()),
                    active=presented.card.active,
                    disabled=presented.card.disabled,
                    style=WORLD_CARD,
                ),
            )
        )
    for action_id in snapshot.actions_by_location[snapshot.world_root_id]:
        action = snapshot.actions_by_id[action_id]
        if not action_is_visible(action, state):
            continue
        presented_action = present_action_card(state, action)
        assert action.position is not None, f"world action missing position: {action.id}"
        cards.append(
            PresentedWorldObject(
                kind="action",
                position=action.position,
                card=presented_action.card,
                scale_bias=0.86,
                action_card=presented_action,
            )
        )
    return tuple(cards)


def present_child_location_cards(state: GameState, location_ids: tuple[str, ...]) -> tuple[PresentedLocationCard, ...]:
    return present_location_cards(state, current_world_snapshot(state), location_ids)


def present_action_cards(state: GameState, location) -> tuple[PresentedActionCard, ...]:
    return present_action_cards_for_location(state, current_world_snapshot(state), location)


def present_location_clock_ids(state: GameState, location_id: str) -> tuple[str, ...]:
    return current_world_snapshot(state).location_clock_ids.get(location_id, ())
