"""Card content and the starting deck.

Cards are frozen data keyed by name; a deck references them by name so a run
saves compactly and a name typo surfaces at load rather than mid-run.
"""

from ascent.core.cards import Card
from ascent.core.effects import Damage, GainBlock

_CARD_LIST: tuple[Card, ...] = (
    Card("Slash", 1, (Damage(6),)),
    Card("Guard", 1, (GainBlock(5),)),
    Card("Lunge", 2, (Damage(10),)),
    Card("Brace", 2, (GainBlock(8),)),
    Card("Jab", 0, (Damage(3),)),
)

CARDS: dict[str, Card] = {card.name: card for card in _CARD_LIST}

STARTING_DECK: tuple[str, ...] = (
    "Slash",
    "Slash",
    "Slash",
    "Slash",
    "Slash",
    "Guard",
    "Guard",
    "Guard",
    "Guard",
    "Lunge",
)


def card(name: str) -> Card:
    return CARDS[name]
