"""Turn engine: energy, playing cards, enemy intents, drawing, and win/lose.

The player spends energy to play cards from hand to discard. Ending the turn
resolves each enemy's telegraphed intent against the player, then starts a fresh
player turn (block cleared, energy refilled, hand redrawn). Drawing from an empty
draw pile reshuffles the discard first.
"""

from ascent.core.cards import Card
from ascent.core.combat import CombatState
from ascent.core.effects import Damage
from ascent.core.entities import Combatant, EnemyCombatant
from ascent.core.intents import Intent
from ascent.core.rng import RngGroup


def make_combat(
    *,
    enemy_hp: int = 12,
    enemy_moves: tuple[Intent, ...] = (),
    seed: int = 1,
) -> CombatState:
    player = Combatant(name="Hero", max_hp=50, hp=50)
    enemy = EnemyCombatant(
        name="Slime",
        max_hp=enemy_hp,
        hp=enemy_hp,
        moves=enemy_moves or (Intent.attack(5),),
    )
    return CombatState(player=player, enemies=[enemy], rng=RngGroup(seed))


def test_playing_a_card_spends_energy_and_moves_it_to_discard() -> None:
    combat = make_combat()
    strike = Card(name="Strike", cost=1, effects=(Damage(6),))
    combat.hand = [strike]
    combat.energy = 3

    combat.play_card(strike)

    assert combat.energy == 2
    assert strike in combat.discard
    assert strike not in combat.hand


def test_ending_the_turn_resolves_the_enemy_intent_and_refills_energy() -> None:
    combat = make_combat(enemy_moves=(Intent.attack(6),))
    combat.energy = 0

    combat.end_turn()

    assert combat.player.hp == 50 - 6
    assert combat.energy == combat.max_energy


def test_drawing_reshuffles_the_discard_when_the_draw_pile_empties() -> None:
    combat = make_combat()
    combat.draw_pile = []
    combat.discard = [
        Card(name="A", cost=1, effects=()),
        Card(name="B", cost=1, effects=()),
        Card(name="C", cost=1, effects=()),
    ]
    combat.hand = []

    combat.draw(3)

    assert len(combat.hand) == 3
    assert combat.discard == []
    assert combat.draw_pile == []


def test_combat_is_won_when_every_enemy_is_dead() -> None:
    combat = make_combat(enemy_hp=6)
    strike = Card(name="Strike", cost=1, effects=(Damage(6),))
    combat.hand = [strike]
    combat.energy = 1

    combat.play_card(strike)

    assert combat.is_won


def test_combat_is_lost_when_the_player_is_dead() -> None:
    combat = make_combat(enemy_moves=(Intent.attack(100),))

    combat.end_turn()

    assert combat.is_lost
