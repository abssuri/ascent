"""Combatant runtime state: hp, block, and the damage model.

Block absorbs incoming damage before hp and is spent as it absorbs; hp floors at
zero. Block does not persist across turns: ``start_turn`` clears it.
"""

from dataclasses import dataclass


@dataclass
class Combatant:
    name: str
    max_hp: int
    hp: int
    block: int = 0

    def take_damage(self, amount: int) -> None:
        absorbed = min(self.block, amount)
        self.block -= absorbed
        self.hp = max(0, self.hp - (amount - absorbed))

    def start_turn(self) -> None:
        self.block = 0

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0
