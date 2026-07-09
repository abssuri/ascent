"""Seeded map generation.

The map is a pure function of the run seed, so regenerating it (for example on
load) reproduces the same path. Every path ends at a boss.
"""

from ascent.core.map import NodeType, generate_map


def test_map_from_a_seed_is_identical_when_regenerated() -> None:
    assert generate_map(99) == generate_map(99)


def test_map_ends_at_a_boss() -> None:
    assert generate_map(99)[-1].type is NodeType.BOSS
