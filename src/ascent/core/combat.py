"""Turn engine: energy, cards, seeded enemy intents, and win/lose.

The player spends energy to play cards from hand to discard. Ending the turn
resolves each living enemy's telegraphed intent against the player, then starts
a fresh player turn: block clears, energy refills, and the hand is redrawn.
Drawing past an empty draw pile reshuffles the discard first, through the seeded
shuffle stream so a run stays reproducible.
"""

from typing import assert_never

from ascent.core.cards import Card
from ascent.core.effects import resolve
from ascent.core.entities import Combatant, EnemyCombatant
from ascent.core.intents import Intent, IntentKind
from ascent.core.rng import RngGroup

HAND_SIZE = 5
MAX_ENERGY = 3


class CombatState:
    def __init__(
        self,
        player: Combatant,
        enemies: list[EnemyCombatant],
        rng: RngGroup,
        max_energy: int = MAX_ENERGY,
        hand_size: int = HAND_SIZE,
    ) -> None:
        self.player = player
        self.enemies = enemies
        self.rng = rng
        self.max_energy = max_energy
        self.hand_size = hand_size
        self.energy = max_energy
        self.hand: list[Card] = []
        self.draw_pile: list[Card] = []
        self.discard: list[Card] = []
        self.turn = 0
        self._telegraph_intents()

    @property
    def living_enemies(self) -> list[EnemyCombatant]:
        return [enemy for enemy in self.enemies if not enemy.is_dead]

    @property
    def is_won(self) -> bool:
        return all(enemy.is_dead for enemy in self.enemies)

    @property
    def is_lost(self) -> bool:
        return self.player.is_dead

    def play_card(self, card: Card) -> None:
        if card not in self.hand:
            raise ValueError(f"{card.name} is not in hand")
        if card.cost > self.energy:
            raise ValueError(f"not enough energy to play {card.name}")
        self.energy -= card.cost
        target = self.living_enemies[0] if self.living_enemies else None
        resolve(card.effects, source=self.player, target=target)
        self.hand.remove(card)
        self.discard.append(card)

    def end_turn(self) -> None:
        for enemy in self.living_enemies:
            if enemy.intent is not None:
                self._resolve_intent(enemy.intent)
        self._start_player_turn()

    def draw(self, count: int) -> None:
        for _ in range(count):
            if not self.draw_pile:
                self._reshuffle()
            if not self.draw_pile:
                break
            self.hand.append(self.draw_pile.pop())

    def _resolve_intent(self, intent: Intent) -> None:
        match intent.kind:
            case IntentKind.ATTACK:
                self.player.take_damage(intent.amount)
            case _:
                assert_never(intent.kind)

    def _start_player_turn(self) -> None:
        self.turn += 1
        self.player.start_turn()
        self.energy = self.max_energy
        self.draw(self.hand_size)
        self._telegraph_intents()

    def _reshuffle(self) -> None:
        self.rng.stream("shuffle").shuffle(self.discard)
        self.draw_pile = self.discard
        self.discard = []

    def _telegraph_intents(self) -> None:
        stream = self.rng.stream("enemy_ai")
        for enemy in self.living_enemies:
            if enemy.moves:
                enemy.intent = stream.choice(enemy.moves)
