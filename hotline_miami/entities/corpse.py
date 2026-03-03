"""Corpse and blood pool visuals."""

from __future__ import annotations

import random
import pygame

from hotline_miami import config


class Blood:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 8)
        self.color = random.choice([config.RED, config.DARK_RED, config.DARK_ORANGE])

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x - offset.x), int(self.y - offset.y)),
            self.radius,
        )


class Corpse:
    def __init__(self, x: float, y: float, radius: float, is_player: bool = False):
        self.x = x
        self.y = y
        self.radius = radius
        self.is_player = is_player
        self.blood = []
        for _ in range(random.randint(8, 15)):
            angle = random.uniform(0, 2 * 3.14159)
            dist = random.uniform(0, radius * 1.5)
            bx = x + pygame.math.Vector2(dist, 0).rotate_rad(angle).x
            by = y + pygame.math.Vector2(dist, 0).rotate_rad(angle).y
            self.blood.append(Blood(bx, by))

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        for blood in self.blood:
            blood.draw(screen, offset)
        color = config.GREEN if self.is_player else config.ORANGE
        pygame.draw.ellipse(
            screen,
            color,
            (
                int(self.x - self.radius - offset.x),
                int(self.y - self.radius / 2 - offset.y),
                int(self.radius * 2),
                int(self.radius),
            ),
        )
