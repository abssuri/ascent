"""Seeded RNG group: named, independent, reproducible streams.

Determinism is the load-bearing property of the game. The same seed must
reproduce a run, consuming randomness in one subsystem must not shift another,
and a saved run must resume identically.
"""

import pytest

from ascent.core.rng import STREAM_NAMES, RngGroup


def _draw(group: RngGroup, name: str, count: int) -> list[float]:
    stream = group.stream(name)
    return [stream.random() for _ in range(count)]


def test_defines_the_named_stream_vocabulary() -> None:
    assert set(STREAM_NAMES) == {"map", "shuffle", "enemy_ai", "card_reward"}


def test_same_seed_yields_identical_sequence_on_a_stream() -> None:
    assert _draw(RngGroup(42), "map", 20) == _draw(RngGroup(42), "map", 20)


def test_unknown_stream_name_is_rejected_by_name() -> None:
    with pytest.raises(ValueError, match="bogus"):
        RngGroup(1).stream("bogus")


def test_consuming_one_stream_does_not_shift_another() -> None:
    consumed = RngGroup(3)
    _draw(consumed, "map", 50)

    untouched = RngGroup(3)
    assert _draw(consumed, "shuffle", 10) == _draw(untouched, "shuffle", 10)


def test_stream_restored_from_saved_state_continues_identically() -> None:
    group = RngGroup(7)
    _draw(group, "shuffle", 5)

    state = group.get_state()
    expected = _draw(group, "shuffle", 5)

    restored = RngGroup.from_state(state)
    assert _draw(restored, "shuffle", 5) == expected
