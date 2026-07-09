"""Combatant damage and block model.

Block absorbs damage before hp, and block is spent when it does. Block does not
carry across turns: it resets at the owner's turn start.
"""

from ascent.core.entities import Combatant


def test_damage_is_absorbed_by_block_before_hp() -> None:
    hero = Combatant(name="Hero", max_hp=20, hp=20, block=5)

    hero.take_damage(8)

    assert hero.block == 0
    assert hero.hp == 17


def test_block_resets_at_turn_start() -> None:
    hero = Combatant(name="Hero", max_hp=20, hp=20, block=5)

    hero.start_turn()

    assert hero.block == 0


def test_hp_floors_at_zero_and_marks_the_combatant_dead() -> None:
    hero = Combatant(name="Hero", max_hp=20, hp=6)

    hero.take_damage(100)

    assert hero.hp == 0
    assert hero.is_dead
