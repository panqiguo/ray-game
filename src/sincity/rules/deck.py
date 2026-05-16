from __future__ import annotations

from sincity.model.state import DeckState

from .rng import RandomSource


SPIRIT_ORDER = ("logic", "perception", "willpower")
BASE_ACTION_CARD_COUNT = 3


def make_starting_deck(rng: RandomSource) -> DeckState:
    del rng
    deck = DeckState(
        spirit_values={
            "logic": 2,
            "perception": 1,
            "willpower": 1,
        },
        extra_slots={
            "logic": 0,
            "perception": 0,
            "willpower": 0,
        },
        actor_names={"cole": "科尔"},
    )
    refresh_spirit_slots(deck)
    return deck


def list_spirit_slots(deck: DeckState) -> list[str]:
    return [*deck.available_slots, *deck.exhausted_slots]


def list_all_spirit_slots(deck: DeckState) -> list[str]:
    return [*deck.available_slots, *deck.exhausted_slots, *deck.locked_slots]


def action_card_count_for_health(health: int) -> int:
    if health <= 0:
        return 0
    if health <= 3:
        return 2
    return BASE_ACTION_CARD_COUNT


def health_penalty_for_cards(health: int) -> int:
    if health <= 3:
        return 1
    if health <= 6:
        return 1
    return 0


def refresh_spirit_slots(deck: DeckState, rng: RandomSource | None = None, *, health: int = 10) -> None:
    if rng is None:
        rng = RandomSource(0)
    count = action_card_count_for_health(health)
    penalty = health_penalty_for_cards(health)
    deck.action_card_values.clear()
    deck.action_card_owners.clear()
    deck.exhausted_slots.clear()
    deck.available_slots.clear()
    deck.locked_slots.clear()
    for index in range(BASE_ACTION_CARD_COUNT):
        slot_id = f"cole:{index}"
        raw = rng.randint(0, 3)
        value = max(0, raw - penalty)
        deck.action_card_values[slot_id] = value
        deck.action_card_owners[slot_id] = "cole"
        if index < count:
            deck.available_slots.append(slot_id)
        else:
            deck.locked_slots.append(slot_id)


def start_city_day(deck: DeckState, rng: RandomSource, hand_size: int = 0, *, health: int = 10) -> None:
    del hand_size
    refresh_spirit_slots(deck, rng, health=health)


def draw_cards(deck: DeckState, rng: RandomSource, amount: int) -> None:
    del deck, rng, amount


def reshuffle(deck: DeckState, rng: RandomSource) -> None:
    del deck, rng
