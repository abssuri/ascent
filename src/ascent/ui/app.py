"""Textual UI shell: the five screens and the transitions between them.

``AscentApp`` owns the run and the current combat. Each screen renders a text
view of core state and forwards key presses to core commands; it never reaches
past the core's own methods. The screen flow is Title -> Map -> Combat -> Reward
and back to Map, ending at GameOver on death or once the boss is cleared.
"""

from __future__ import annotations

from typing import ClassVar, cast

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Static

from ascent.core import content
from ascent.core.combat import CombatState
from ascent.core.entities import EnemyCombatant
from ascent.core.map import NodeType
from ascent.core.run import Run
from ascent.ui.combat_view import render_combat


def _start_combat(run: Run, enemy: EnemyCombatant) -> CombatState:
    run.player.block = 0
    combat = CombatState(player=run.player, enemies=[enemy], rng=run.rng)
    combat.draw_pile = list(run.deck)
    combat.rng.stream("shuffle").shuffle(combat.draw_pile)
    combat.draw(combat.hand_size)
    return combat


class _TextScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        # markup=False: key hints like "[Enter]" and "[e]" are literal text, not
        # Rich markup tags (which would be parsed away).
        yield Static(id="view", markup=False)

    def on_mount(self) -> None:
        self.refresh_view()

    def refresh_view(self) -> None:
        self.query_one("#view", Static).update(self.view_text())

    def view_text(self) -> str:
        return ""

    @property
    def game(self) -> AscentApp:
        return cast("AscentApp", self.app)


class TitleScreen(_TextScreen):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "new_game", "New game"),
        Binding("q", "quit_game", "Quit"),
    ]

    def action_new_game(self) -> None:
        self.game.new_game()

    def action_quit_game(self) -> None:
        self.app.exit()

    def view_text(self) -> str:
        return "ASCENT\n\nClimb the tower of Papel.\n\n[Enter] New game    [q] Quit"


class MapScreen(_TextScreen):
    BINDINGS: ClassVar[list[BindingType]] = [Binding("enter", "enter_node", "Enter node")]

    def action_enter_node(self) -> None:
        self.game.enter_node()

    def view_text(self) -> str:
        run = self.game.active_run
        if run is None:
            return ""
        lines = ["MAP", ""]
        for node in run.map:
            marker = ">" if node.index == run.node_index else " "
            lines.append(f" {marker} {node.index}  {node.type.value}")
        lines += [
            "",
            f"gold {run.gold}    hp {run.player.hp}/{run.player.max_hp}",
            "",
            "[Enter] enter node",
        ]
        return "\n".join(lines)


class CombatScreen(_TextScreen):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("1", "play(0)", "Play 1"),
        Binding("2", "play(1)", "Play 2"),
        Binding("3", "play(2)", "Play 3"),
        Binding("4", "play(3)", "Play 4"),
        Binding("5", "play(4)", "Play 5"),
        Binding("e", "end_turn", "End turn"),
        Binding("q", "quit_game", "Quit"),
    ]

    def action_quit_game(self) -> None:
        self.app.exit()

    def action_play(self, index: int) -> None:
        combat = self.game.combat
        if combat is None:
            return
        if 0 <= index < len(combat.hand):
            card = combat.hand[index]
            if card.cost <= combat.energy:
                combat.play_card(card)
        self._after_action()

    def action_end_turn(self) -> None:
        combat = self.game.combat
        if combat is None:
            return
        combat.end_turn()
        self._after_action()

    def _after_action(self) -> None:
        combat = self.game.combat
        if combat is None:
            return
        if combat.is_lost:
            self.game.go_game_over(victory=False)
        elif combat.is_won:
            self.game.go_reward()
        else:
            self.refresh_view()

    def view_text(self) -> str:
        combat = self.game.combat
        if combat is None:
            return ""
        return render_combat(combat)


class RewardScreen(_TextScreen):
    BINDINGS: ClassVar[list[BindingType]] = [Binding("enter", "take_reward", "Continue")]

    def action_take_reward(self) -> None:
        self.game.take_reward()

    def view_text(self) -> str:
        run = self.game.active_run
        if run is None:
            return ""
        return (
            f"VICTORY\n\ngold {run.gold}\nhp {run.player.hp}/{run.player.max_hp}\n\n"
            "[Enter] continue"
        )


class GameOverScreen(_TextScreen):
    BINDINGS: ClassVar[list[BindingType]] = [Binding("q", "quit_game", "Quit")]

    def action_quit_game(self) -> None:
        self.app.exit()

    def view_text(self) -> str:
        result = "VICTORY" if self.game.victory else "GAME OVER"
        run = self.game.active_run
        gold = run.gold if run is not None else 0
        return f"{result}\n\ngold {gold}\n\n[q] quit"


class AscentApp(App[None]):
    def __init__(self, seed: int = 0) -> None:
        super().__init__()
        self.seed = seed
        self.active_run: Run | None = None
        self.combat: CombatState | None = None
        self.victory = False

    def on_mount(self) -> None:
        self.push_screen(TitleScreen())

    def new_game(self) -> None:
        self.active_run = Run.from_seed(self.seed)
        self.switch_screen(MapScreen())

    def enter_node(self) -> None:
        run = self.active_run
        if run is None:
            return
        node = run.current_node
        if node.type is NodeType.REST:
            healed = run.player.max_hp * 3 // 10
            run.player.hp = min(run.player.max_hp, run.player.hp + healed)
            run.clear_node()
            self._after_node_change()
        else:
            self.combat = _start_combat(run, content.enemy_for(node.type))
            self.switch_screen(CombatScreen())

    def go_reward(self) -> None:
        self.switch_screen(RewardScreen())

    def take_reward(self) -> None:
        run = self.active_run
        if run is None:
            return
        run.clear_node()
        self.combat = None
        self._after_node_change()

    def go_game_over(self, victory: bool) -> None:
        self.victory = victory
        self.switch_screen(GameOverScreen())

    def _after_node_change(self) -> None:
        run = self.active_run
        if run is None:
            return
        if run.player.is_dead:
            self.go_game_over(victory=False)
        elif run.is_complete:
            self.go_game_over(victory=True)
        else:
            self.switch_screen(MapScreen())
