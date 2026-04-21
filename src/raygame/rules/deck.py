from __future__ import annotations

from raygame.model.state import DeckState

from .rng import RandomSource


SPIRIT_ORDER = ("logic", "perception", "willpower")


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
    )
    refresh_spirit_slots(deck)
    return deck


def list_spirit_slots(deck: DeckState) -> list[str]:
    slots: list[str] = []
    max_slot_count = max((1 + deck.extra_slots.get(spirit, 0) for spirit in SPIRIT_ORDER), default=1)
    for slot_index in range(max_slot_count):
        for spirit in SPIRIT_ORDER:
            if slot_index < 1 + deck.extra_slots.get(spirit, 0):
                slots.append(f"{spirit}:{slot_index}")
    return slots


def refresh_spirit_slots(deck: DeckState) -> None:
    deck.available_slots = list_spirit_slots(deck)
    deck.exhausted_slots.clear()


def start_city_day(deck: DeckState, rng: RandomSource, hand_size: int = 0) -> None:
    del rng, hand_size
    refresh_spirit_slots(deck)


def draw_cards(deck: DeckState, rng: RandomSource, amount: int) -> None:
    del deck, rng, amount


def reshuffle(deck: DeckState, rng: RandomSource) -> None:
    del deck, rng

