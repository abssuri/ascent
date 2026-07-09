"""The combat view renders as a horizontal layout.

The hand is drawn as ASCII card boxes side by side (not a vertical list), with a
header carrying player hp and a panel showing each enemy's hp and telegraphed
intent. These tests pin the horizontal arrangement and the key content; they do
not assert exact spacing.
"""

from ascent.core.cards import Card
from ascent.core.combat import CombatState
from ascent.core.effects import Damage, GainBlock
from ascent.core.entities import Combatant, EnemyCombatant
from ascent.core.intents import Intent
from ascent.core.rng import RngGroup
from ascent.ui.combat_view import render_combat


def _combat() -> CombatState:
    player = Combatant(name="Hero", max_hp=72, hp=68)
    enemy = EnemyCombatant(name="Slime", max_hp=12, hp=12, moves=(Intent.attack(6),))
    combat = CombatState(player=player, enemies=[enemy], rng=RngGroup(0))
    combat.hand = [Card("Slash", 1, (Damage(6),)), Card("Guard", 1, (GainBlock(5),))]
    combat.energy = 3
    return combat


def test_cards_are_laid_out_side_by_side() -> None:
    lines = render_combat(_combat()).splitlines()
    assert any("Slash" in line and "Guard" in line for line in lines)


def test_view_shows_player_hp_enemy_and_intent() -> None:
    text = render_combat(_combat())
    assert "68/72" in text
    assert "12/12" in text
    assert "attack 6" in text.lower()
