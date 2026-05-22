from __future__ import annotations

from sincity.model.state import DeckState

from .rng import RandomSource


SPIRIT_ORDER = ("logic", "perception", "willpower")
BASE_ACTION_CARD_COUNT = 4


def make_starting_deck(rng: RandomSource) -> DeckState:
    del rng
    deck = DeckState(
        extra_slots={
            "logic": 0,
            "perception": 0,
            "willpower": 0,
        },
    )
    return deck


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


def action_card_count_for_health(health: int, *, is_player: bool = True) -> int:
    if health <= 0:
        return 0
    if not is_player:
        return 1
    if health <= 3:
        return 3
    return BASE_ACTION_CARD_COUNT


def health_penalty_for_cards(health: int) -> int:
    if health <= 6:
        return 1
    return 0


def refresh_spirit_slots(deck: DeckState, rng: RandomSource | None = None, *, actors=()) -> None:
    if rng is None:
        rng = RandomSource(0)
    deck.action_card_values.clear()
    deck.action_card_bonuses.clear()
    deck.action_card_owners.clear()
    deck.exhausted_slots.clear()
    deck.available_slots.clear()
    deck.locked_slots.clear()
    for actor in actors:
        count = action_card_count_for_health(actor.health, is_player=actor.is_player)
        max_slots = BASE_ACTION_CARD_COUNT if actor.is_player else 1
        penalty = health_penalty_for_cards(actor.health)
        for index in range(max_slots):
            slot_id = f"{actor.id}:{index}"
            raw = rng.randint(0, 3)
            value = max(0, raw - penalty)
            deck.action_card_values[slot_id] = value
            deck.action_card_owners[slot_id] = actor.id
            if actor.can_act and index < count:
                deck.available_slots.append(slot_id)
            else:
                deck.locked_slots.append(slot_id)


def start_city_day(deck: DeckState, rng: RandomSource, hand_size: int = 0, *, actors=()) -> None:
    del hand_size
    refresh_spirit_slots(deck, rng, actors=actors)


def draw_cards(deck: DeckState, rng: RandomSource, amount: int) -> None:
    del deck, rng, amount


def reshuffle(deck: DeckState, rng: RandomSource) -> None:
    del deck, rng
