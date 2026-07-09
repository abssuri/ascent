"""Card effects resolve through one function that mutates combat state.

Damage lands on the target and is absorbed by its block before hp; GainBlock
shields the source. Resolving a list applies the effects in order.
"""

from ascent.core.effects import Damage, GainBlock, resolve
from ascent.core.entities import Combatant


def test_resolving_damage_then_block_hits_the_target_and_shields_the_source() -> None:
    player = Combatant(name="Hero", max_hp=50, hp=50)
    enemy = Combatant(name="Slime", max_hp=12, hp=12)

    resolve([Damage(6), GainBlock(5)], source=player, target=enemy)

    assert enemy.hp == 6
    assert player.block == 5
