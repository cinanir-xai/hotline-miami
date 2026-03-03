"""Wall geometry and collision."""

from __future__ import annotations

import pygame

from hotline_miami import config
from hotline_miami.core.math_utils import line_segments_intersect


class Wall:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.rect = pygame.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains_point(self, x: float, y: float, radius: float = 0) -> bool:
        return (
            x - radius < self.x + self.width
            and x + radius > self.x
            and y - radius < self.y + self.height
            and y + radius > self.y
        )

    def intersects_line(self, start: pygame.Vector2, end: pygame.Vector2) -> bool:
        rect_lines = [
            (pygame.Vector2(self.x, self.y), pygame.Vector2(self.x + self.width, self.y)),
            (pygame.Vector2(self.x + self.width, self.y), pygame.Vector2(self.x + self.width, self.y + self.height)),
            (
                pygame.Vector2(self.x + self.width, self.y + self.height),
                pygame.Vector2(self.x, self.y + self.height),
            ),
            (pygame.Vector2(self.x, self.y + self.height), pygame.Vector2(self.x, self.y)),
        ]
        for a, b in rect_lines:
            if line_segments_intersect(start, end, a, b):
                return True
        return self.rect.clipline((start.x, start.y), (end.x, end.y)) != ()

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        rect = pygame.Rect(
            self.rect.x - offset.x,
            self.rect.y - offset.y,
            self.rect.width,
            self.rect.height,
        )
        pygame.draw.rect(screen, config.DARK_GRAY, rect)
        pygame.draw.rect(screen, config.GRAY, rect, 2)
        if rect.width > rect.height:
            for x in range(int(rect.left), int(rect.right), 24):
                pygame.draw.line(
                    screen,
                    config.LIGHT_GRAY,
                    (x, rect.top + 3),
                    (x + 12, rect.top + rect.height - 3),
                    1,
                )
        else:
            for y in range(int(rect.top), int(rect.bottom), 24):
                pygame.draw.line(
                    screen,
                    config.LIGHT_GRAY,
                    (rect.left + 3, y),
                    (rect.right - 3, y + 12),
                    1,
                )
