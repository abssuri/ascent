"""Horizontal combat layout.

Renders the combat state as a monospace view: a header carrying player hp, a
boxed enemy panel with an hp bar and the telegraphed intent beside it, and the
hand as ASCII card boxes side by side. Pure and Textual-free, so it is unit
tested without a terminal.
"""

from __future__ import annotations

from ascent.core.cards import Card
from ascent.core.combat import CombatState
from ascent.core.effects import Damage, GainBlock
from ascent.core.entities import EnemyCombatant

_PANEL_WIDTH = 44
_ENEMY_INNER = 24
_CARD_INNER = 7
_BAR_WIDTH = 10


def render_combat(combat: CombatState) -> str:
    player = combat.player
    header = _row("COMBAT", f"HP {player.hp}/{player.max_hp}", _PANEL_WIDTH)
    status = _row(
        f"Block {player.block}",
        f"Energy {combat.energy}/{combat.max_energy}",
        _PANEL_WIDTH,
    )
    sections = [
        header,
        "",
        *_enemy_lines(combat.living_enemies),
        "",
        status,
        "",
        *_hand_lines(combat.hand),
        "",
        "[1-5] play   [e] end turn   [q] quit",
    ]
    return "\n".join(sections)


def _row(left: str, right: str, width: int) -> str:
    pad = max(1, width - len(left) - len(right))
    return left + " " * pad + right


def _hp_bar(current: int, maximum: int, width: int = _BAR_WIDTH) -> str:
    ratio = 0.0 if maximum <= 0 else current / maximum
    filled = max(0, min(width, round(width * ratio)))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _enemy_lines(enemies: list[EnemyCombatant]) -> list[str]:
    if not enemies:
        return ["(no enemies)"]
    border = "+" + "-" * _ENEMY_INNER + "+"
    lines: list[str] = []
    for enemy in enemies:
        name_hp = _row(f" {enemy.name}", f"{enemy.hp}/{enemy.max_hp} ", _ENEMY_INNER)
        bar = (" " + _hp_bar(enemy.hp, enemy.max_hp)).ljust(_ENEMY_INNER)
        intent = enemy.intent
        telegraph = f"intent: {intent.kind.value} {intent.amount}" if intent else "intent: -"
        lines += [border, "|" + name_hp + "|   " + telegraph, "|" + bar + "|", border]
    return lines


def _hand_lines(hand: list[Card]) -> list[str]:
    if not hand:
        return ["(hand empty)"]
    columns = [_card_column(index, card) for index, card in enumerate(hand, start=1)]
    return [" ".join(parts) for parts in zip(*columns, strict=True)]


def _card_column(slot: int, card: Card) -> list[str]:
    border = "+" + "-" * _CARD_INNER + "+"
    return [
        f"[{slot}]".center(_CARD_INNER + 2),
        border,
        "|" + card.name[:_CARD_INNER].center(_CARD_INNER) + "|",
        "|" + _card_stat(card) + "|",
        border,
    ]


def _card_stat(card: Card) -> str:
    damage = sum(effect.amount for effect in card.effects if isinstance(effect, Damage))
    block = sum(effect.amount for effect in card.effects if isinstance(effect, GainBlock))
    value = f"[{block}]" if block else str(damage)
    cost = str(card.cost)
    pad = max(1, _CARD_INNER - len(cost) - len(value))
    return cost + " " * pad + value
