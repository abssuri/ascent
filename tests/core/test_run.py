"""Run aggregate: the save root that tracks progress through the map.

Clearing a combat node awards gold and advances to the next node. hp, gold, and
deck persist across nodes.
"""

from ascent.core.map import NodeType
from ascent.core.run import Run


def test_clearing_a_combat_node_advances_and_awards_gold() -> None:
    run = Run.from_seed(1)
    assert run.current_node.type is NodeType.COMBAT
    gold_before = run.gold

    run.clear_node()

    assert run.node_index == 1
    assert run.gold > gold_before
