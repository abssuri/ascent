"""Seeded RNG group: named, independent, reproducible streams.

Determinism is the load-bearing property of the game, so all randomness runs
through named streams derived from a single run seed. Stream seeds derive from
sha256 rather than the builtin ``hash()`` (which ``PYTHONHASHSEED`` salts), so a
seed reproduces a run across separate processes and saved games.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, TypedDict

STREAM_NAMES: tuple[str, ...] = ("map", "shuffle", "enemy_ai", "card_reward")


class RngGroupState(TypedDict):
    seed: int
    streams: dict[str, tuple[Any, ...]]


def _derive_seed(*parts: object) -> int:
    key = ":".join(str(part) for part in parts)
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest(), "big")


class RngGroup:
    """A run's named ``random.Random`` streams, each seeded independently.

    Consuming randomness from one stream never shifts another because each is
    seeded from ``(seed, name)`` rather than sharing a single generator.
    """

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._streams: dict[str, random.Random] = {}

    def stream(self, name: str) -> random.Random:
        if name not in STREAM_NAMES:
            raise ValueError(f"unknown stream {name!r}; valid names are {STREAM_NAMES}")
        stream = self._streams.get(name)
        if stream is None:
            stream = random.Random(_derive_seed(self._seed, name))
            self._streams[name] = stream
        return stream

    def get_state(self) -> RngGroupState:
        return {
            "seed": self._seed,
            "streams": {name: rng.getstate() for name, rng in self._streams.items()},
        }

    @classmethod
    def from_state(cls, state: RngGroupState) -> RngGroup:
        group = cls(state["seed"])
        for name, stream_state in state["streams"].items():
            rng = random.Random()
            rng.setstate(stream_state)
            group._streams[name] = rng
        return group
