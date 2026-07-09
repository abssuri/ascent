"""The headless fixture lets pygame create and blit alpha surfaces windowless."""

import pygame


def test_alpha_surface_blits_under_dummy_driver() -> None:
    source = pygame.Surface((8, 8)).convert_alpha()
    source.fill((10, 20, 30, 255))
    target = pygame.Surface((8, 8)).convert_alpha()
    target.blit(source, (0, 0))
    assert target.get_at((0, 0))[:3] == (10, 20, 30)
