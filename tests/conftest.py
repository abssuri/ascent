"""Headless pygame test configuration.

The SDL dummy drivers must be selected before pygame is imported anywhere in the
test process, so the environment is set at module import time, above the pygame
import.
"""

import os
from collections.abc import Iterator

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def _pygame_session() -> Iterator[None]:
    pygame.display.init()
    pygame.font.init()
    # A real display surface must exist for convert_alpha() and blits, even under
    # the dummy video driver.
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
