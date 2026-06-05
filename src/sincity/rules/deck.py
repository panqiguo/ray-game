from __future__ import annotations

from sincity.model.enums import ScreenName
from sincity.model.state import DeckState

from .rng import RandomSource


ATTRIBUTE_ORDER = ("force", "charm", "knowledge", "sense")

CARD_DRAW_RULES: dict[ScreenName, dict[str, int]] = {
    ScreenName.CITY: {"player": 2, "companion": 2},
    ScreenName.ENCOUNTER: {"player": 4, "companion": 0},
}


def make_starting_deck(rng: RandomSource) -> DeckState:
    del rng
    deck = DeckState(
        extra_slots={},
    )
    return deck


def card_count_for_actor(actor, screen: ScreenName) -> int:
    base = CARD_DRAW_RULES[screen]
    count = base["player"] if actor.is_player else base["companion"]
    if actor.health <= 0:
        return 0
    if actor.health <= 3:
        return max(0, count - 1)
    return count


def list_spirit_slots(deck: DeckState) -> list[str]:
    return [slot_id for slot_id in _ordered_action_slots(deck) if slot_id in deck.available_slots or slot_id in deck.exhausted_slots]


def list_all_spirit_slots(deck: DeckState) -> list[str]:
    return _ordered_action_slots(deck)


def _ordered_action_slots(deck: DeckState) -> list[str]:
    known = {*deck.available_slots, *deck.exhausted_slots, *deck.locked_slots}
    return sorted(known, key=_slot_sort_key)


def _slot_sort_key(slot_id: str) -> tuple[int, str, int]:
    owner, _, raw_index = slot_id.partition(":")
    owner_rank = 0 if owner == "cole" else 1
    return (owner_rank, owner, int(raw_index or 0))


def health_penalty_for_cards(health: int) -> int:
    if health <= 6:
        return 1
    return 0


def refresh_spirit_slots(deck: DeckState, rng: RandomSource | None = None, *, actors=(), screen: ScreenName = ScreenName.CITY, status_defs=None) -> None:
    if rng is None:
        rng = RandomSource(0)
    if status_defs is None:
        status_defs = {}
    deck.action_card_values.clear()
    deck.action_card_bonuses.clear()
    deck.action_card_penalties.clear()
    deck.action_card_labels.clear()
    deck.action_card_owners.clear()
    deck.exhausted_slots.clear()
    deck.available_slots.clear()
    deck.locked_slots.clear()
    for actor in actors:
        count = card_count_for_actor(actor, screen)
        penalty = health_penalty_for_cards(actor.health)
        for index in range(count):
            slot_id = f"{actor.id}:{index}"
            raw = rng.randint(0, 3)
            value = max(0, raw - penalty)
            deck.action_card_values[slot_id] = value
            deck.action_card_owners[slot_id] = actor.id
            _apply_actor_status_to_card(deck, slot_id, actor, rng, status_defs)
            if actor.can_act:
                deck.available_slots.append(slot_id)
            else:
                deck.locked_slots.append(slot_id)


def _apply_actor_status_to_card(deck: DeckState, slot_id: str, actor, rng: RandomSource, status_defs) -> None:
    for status in getattr(actor, "statuses", ()):
        status_def = status_defs.get(status.id)
        if status_def is None or status_def.card_penalty == 0 or not status_def.card_label:
            continue
        if rng.randint(1, 100) <= int(status_def.card_chance * 100):
            deck.action_card_penalties[slot_id] = deck.action_card_penalties.get(slot_id, 0) + status_def.card_penalty
            deck.action_card_labels[slot_id] = status_def.card_label


def start_city_day(deck: DeckState, rng: RandomSource, hand_size: int = 0, *, actors=(), status_defs=None) -> None:
    del hand_size
    refresh_spirit_slots(deck, rng, actors=actors, screen=ScreenName.CITY, status_defs=status_defs)


def draw_cards(deck: DeckState, rng: RandomSource, amount: int) -> None:
    del deck, rng, amount


def reshuffle(deck: DeckState, rng: RandomSource) -> None:
    del deck, rng
