"""Seeded map generation.

The map is a pure function of the run seed: it builds its own ``RngGroup(seed)``
and never touches the live run streams, so it regenerates identically on load and
does not need serialising. For the slice it is a short linear path whose first
node is a combat and whose last is a boss.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from ascent.core.rng import RngGroup

MAP_LENGTH = 6


class NodeType(enum.Enum):
    COMBAT = "combat"
    ELITE = "elite"
    REST = "rest"
    BOSS = "boss"


@dataclass(frozen=True)
class Node:
    index: int
    type: NodeType


_MIDDLE_TYPES: tuple[NodeType, ...] = (NodeType.COMBAT, NodeType.ELITE, NodeType.REST)


def generate_map(seed: int, length: int = MAP_LENGTH) -> list[Node]:
    stream = RngGroup(seed).stream("map")
    nodes = [Node(0, NodeType.COMBAT)]
    for index in range(1, length - 1):
        nodes.append(Node(index, stream.choice(_MIDDLE_TYPES)))
    nodes.append(Node(length - 1, NodeType.BOSS))
    return nodes
