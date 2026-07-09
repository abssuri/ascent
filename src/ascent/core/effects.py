"""Card effects and the single function that applies them.

Effects are pure data. ``resolve`` is the only place they mutate combat state,
so all damage and block bookkeeping lives in one spot. Damage lands on the
target; GainBlock shields the source.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import assert_never

from ascent.core.entities import Combatant


@dataclass(frozen=True)
class Damage:
    amount: int


@dataclass(frozen=True)
class GainBlock:
    amount: int


Effect = Damage | GainBlock


def resolve(
    effects: Iterable[Effect],
    *,
    source: Combatant,
    target: Combatant | None,
) -> None:
    for effect in effects:
        match effect:
            case Damage(amount=amount):
                if target is None:
                    raise ValueError("Damage requires a target")
                target.take_damage(amount)
            case GainBlock(amount=amount):
                source.block += amount
            case _:
                assert_never(effect)
