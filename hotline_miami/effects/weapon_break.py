"""Weapon break particle effect."""

from __future__ import annotations

import random
import pygame

from hotline_miami import config


class BatBreakPiece:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.offset = pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
        self.life = 1.0

    def update(self, dt: float) -> None:
        self.life -= dt

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        if self.life <= 0:
            return
        start = (self.x - offset.x, self.y - offset.y)
        end = (self.x + self.offset.x - offset.x, self.y + self.offset.y - offset.y)
        pygame.draw.line(screen, config.DARK_BROWN, start, end, 3)
