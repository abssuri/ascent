"""Versioned save and load of a Run.

A run serialises to a JSON-safe dict tagged with an integer ``save_version``.
Loading checks the version first and refuses anything unrecognised, rebuilds the
map from the seed (never trusting stored geometry), and reconstructs the deck
from card names. RNG stream state round-trips through ``get_state``/``from_state``;
the internal Mersenne Twister state is coerced back to tuples after a JSON round
trip has turned them into lists.
"""

from __future__ import annotations

from typing import Any

from ascent.core import content
from ascent.core.entities import Combatant
from ascent.core.map import generate_map
from ascent.core.rng import RngGroup, RngGroupState
from ascent.core.run import Run

SAVE_VERSION = 1


class SaveVersionError(Exception):
    pass


def to_dict(run: Run) -> dict[str, Any]:
    return {
        "save_version": SAVE_VERSION,
        "seed": run.seed,
        "rng": run.rng.get_state(),
        "node_index": run.node_index,
        "gold": run.gold,
        "player": {
            "name": run.player.name,
            "max_hp": run.player.max_hp,
            "hp": run.player.hp,
            "block": run.player.block,
        },
        "deck": [card.name for card in run.deck],
    }


def from_dict(data: dict[str, Any]) -> Run:
    version = data.get("save_version")
    if version != SAVE_VERSION:
        raise SaveVersionError(f"unsupported save_version {version!r}; expected {SAVE_VERSION}")
    seed = data["seed"]
    player_data = data["player"]
    player = Combatant(
        name=player_data["name"],
        max_hp=player_data["max_hp"],
        hp=player_data["hp"],
        block=player_data["block"],
    )
    return Run(
        seed=seed,
        rng=RngGroup.from_state(_coerce_rng_state(data["rng"])),
        map=generate_map(seed),
        player=player,
        deck=[content.card(name) for name in data["deck"]],
        gold=data["gold"],
        node_index=data["node_index"],
    )


def _coerce_rng_state(state: dict[str, Any]) -> RngGroupState:
    return {
        "seed": state["seed"],
        "streams": {
            name: (stream_state[0], tuple(stream_state[1]), stream_state[2])
            for name, stream_state in state["streams"].items()
        },
    }
