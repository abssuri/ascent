"""Cards: named, energy-costed bundles of effects."""

from dataclasses import dataclass

from ascent.core.effects import Effect


@dataclass(frozen=True)
class Card:
    name: str
    cost: int
    effects: tuple[Effect, ...]
