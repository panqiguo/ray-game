from __future__ import annotations

from raygame.constants import HAND_SIZE
from raygame.content.cards import CARD_DEFS, STARTING_DECK
from raygame.model.state import DeckState

from .rng import RandomSource


def make_starting_deck(rng: RandomSource) -> DeckState:
    draw_pile = list(STARTING_DECK)
    rng.shuffle(draw_pile)
    return DeckState(draw_pile=draw_pile)


def reshuffle(deck: DeckState, rng: RandomSource) -> None:
    if not deck.discard_pile:
        return
    deck.draw_pile = list(deck.discard_pile)
    deck.discard_pile.clear()
    rng.shuffle(deck.draw_pile)


def draw_cards(deck: DeckState, rng: RandomSource, amount: int) -> None:
    while len(deck.hand) < amount:
        if not deck.draw_pile:
            reshuffle(deck, rng)
            if not deck.draw_pile:
                break
        deck.hand.append(deck.draw_pile.pop())


def start_city_day(deck: DeckState, rng: RandomSource, hand_size: int = HAND_SIZE) -> None:
    deck.hand.clear()
    if deck.retained_card_id is not None:
        deck.hand.append(deck.retained_card_id)
        deck.retained_card_id = None
    draw_cards(deck, rng, hand_size)


def start_mission_hand(deck: DeckState, rng: RandomSource) -> None:
    deck.hand.clear()
    draw_cards(deck, rng, HAND_SIZE)


def discard_card(deck: DeckState, card_id: str) -> None:
    deck.hand.remove(card_id)
    deck.discard_pile.append(card_id)


def choose_casebook_card(deck: DeckState, card_id: str | None) -> None:
    if card_id is None:
        deck.retained_card_id = None
        return
    if card_id not in deck.hand:
        return
    deck.hand.remove(card_id)
    deck.retained_card_id = card_id


def remove_negative_cards(deck: DeckState, count: int, family: str | None = None) -> int:
    removed = 0
    piles = [deck.hand, deck.discard_pile, deck.draw_pile]
    for pile in piles:
        keep: list[str] = []
        for card_id in pile:
            card = CARD_DEFS[card_id]
            should_remove = (
                removed < count
                and card.is_negative
                and (family is None or card.negative_family == family)
            )
            if should_remove:
                removed += 1
                continue
            keep.append(card_id)
        pile[:] = keep
        if removed >= count:
            break
    return removed


def replace_first_base_card(deck: DeckState, old_prefix: str, new_card_id: str) -> bool:
    target = f"{old_prefix}_0"
    for pile in (deck.hand, deck.draw_pile, deck.discard_pile):
        for index, card_id in enumerate(pile):
            if card_id.startswith(target):
                pile[index] = new_card_id
                return True
    return False

