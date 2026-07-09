"""The card content set and the starting deck.

Every card named in the starting deck must exist in the card library, so a typo
in the deck fails here rather than deep in a run.
"""

from ascent.core.content import CARDS, STARTING_DECK


def test_starting_deck_cards_are_all_defined() -> None:
    assert all(name in CARDS for name in STARTING_DECK)
