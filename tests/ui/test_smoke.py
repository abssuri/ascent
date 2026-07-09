"""Headless smoke test: a scripted key sequence drives the whole screen flow.

The Textual app runs windowless through the Pilot. The same small block of keys,
pressed repeatedly, advances each screen in turn (confirm on menus, play cards
and end turns in combat) until the run reaches its end. This asserts the screen
machine holds together end to end, not any balance or layout detail.
"""

import asyncio

from ascent.ui.app import AscentApp, GameOverScreen


def test_scripted_run_reaches_game_over_without_raising() -> None:
    asyncio.run(_drive())


async def _drive() -> None:
    app = AscentApp(seed=0)
    async with app.run_test() as pilot:
        reached = False
        for _ in range(60):
            await pilot.press("1", "2", "3", "4", "5", "e", "enter")
            if isinstance(app.screen, GameOverScreen):
                reached = True
                break
        assert reached, "scripted run never reached the game-over screen"
