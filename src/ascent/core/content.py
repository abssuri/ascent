"""Card and enemy content, and the starting deck.

Cards are frozen data keyed by name; a deck references them by name so a run
saves compactly and a name typo surfaces at load rather than mid-run. Enemies are
built fresh per encounter so each combat gets its own mutable combatant.
"""

from ascent.core.cards import Card
from ascent.core.effects import Damage, GainBlock
from ascent.core.entities import EnemyCombatant
from ascent.core.intents import Intent
from ascent.core.map import NodeType

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


def basic_enemy() -> EnemyCombatant:
    return EnemyCombatant(name="Husk", max_hp=28, hp=28, moves=(Intent.attack(6),))


def elite_enemy() -> EnemyCombatant:
    return EnemyCombatant(name="Warden", max_hp=44, hp=44, moves=(Intent.attack(10),))


def boss_enemy() -> EnemyCombatant:
    return EnemyCombatant(name="The Gatekeeper", max_hp=80, hp=80, moves=(Intent.attack(16),))


def enemy_for(node_type: NodeType) -> EnemyCombatant:
    match node_type:
        case NodeType.ELITE:
            return elite_enemy()
        case NodeType.BOSS:
            return boss_enemy()
        case _:
            return basic_enemy()
