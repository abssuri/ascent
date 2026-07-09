"""Enemy intents: what an enemy telegraphs it will do next.

An intent is pure, readable data (a kind and an amount) so the UI can show it a
turn ahead. The combat engine, not the intent, decides how to apply it.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class IntentKind(enum.Enum):
    ATTACK = "attack"


@dataclass(frozen=True)
class Intent:
    kind: IntentKind
    amount: int

    @classmethod
    def attack(cls, amount: int) -> Intent:
        return cls(IntentKind.ATTACK, amount)
