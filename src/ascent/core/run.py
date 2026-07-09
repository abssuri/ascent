"""The Run aggregate: the save root that tracks progress through the map.

hp, gold, and deck persist across nodes. Clearing a battle node awards gold from
the seeded ``card_reward`` stream and advances to the next node.
"""

from __future__ import annotations

from ascent.core import content
from ascent.core.cards import Card
from ascent.core.entities import Combatant
from ascent.core.map import Node, NodeType, generate_map
from ascent.core.rng import RngGroup

STARTING_HP = 60
GOLD_REWARD = (10, 20)
_BATTLE_NODES = (NodeType.COMBAT, NodeType.ELITE, NodeType.BOSS)


class Run:
    def __init__(
        self,
        seed: int,
        rng: RngGroup,
        map: list[Node],
        player: Combatant,
        deck: list[Card],
        gold: int = 0,
        node_index: int = 0,
    ) -> None:
        self.seed = seed
        self.rng = rng
        self.map = map
        self.player = player
        self.deck = deck
        self.gold = gold
        self.node_index = node_index

    @classmethod
    def from_seed(cls, seed: int) -> Run:
        return cls(
            seed=seed,
            rng=RngGroup(seed),
            map=generate_map(seed),
            player=Combatant(name="Hero", max_hp=STARTING_HP, hp=STARTING_HP),
            deck=[content.card(name) for name in content.STARTING_DECK],
        )

    @property
    def current_node(self) -> Node:
        return self.map[self.node_index]

    @property
    def is_complete(self) -> bool:
        return self.node_index >= len(self.map)

    def clear_node(self) -> None:
        low, high = GOLD_REWARD
        if self.current_node.type in _BATTLE_NODES:
            self.gold += self.rng.stream("card_reward").randint(low, high)
        self.node_index += 1
