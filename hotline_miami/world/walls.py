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
        pygame.draw.rect(screen, config.CONCRETE_DARK, rect)
        pygame.draw.rect(screen, config.CONCRETE_LIGHT, rect, 2)
        if rect.width > rect.height:
            for x in range(int(rect.left), int(rect.right), 24):
                pygame.draw.line(
                    screen,
                    config.CONCRETE_LIGHT,
                    (x, rect.top + 3),
                    (x + 12, rect.top + rect.height - 3),
                    1,
                )
        else:
            for y in range(int(rect.top), int(rect.bottom), 24):
                pygame.draw.line(
                    screen,
                    config.CONCRETE_LIGHT,
                    (rect.left + 3, y),
                    (rect.right - 3, y + 12),
                    1,
                )


class Prop:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        kind: str,
        collidable: bool = True,
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.kind = kind
        self.collidable = collidable

    def contains_point(self, x: float, y: float, radius: float = 0) -> bool:
        if not self.collidable:
            return False
        return (
            x - radius < self.rect.right
            and x + radius > self.rect.left
            and y - radius < self.rect.bottom
            and y + radius > self.rect.top
        )

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        rect = pygame.Rect(
            self.rect.x - offset.x,
            self.rect.y - offset.y,
            self.rect.width,
            self.rect.height,
        )
        if self.kind == "plant":
            pot_rect = pygame.Rect(rect.x, rect.y + rect.height * 0.45, rect.width, rect.height * 0.55)
            pygame.draw.rect(screen, config.POT_BROWN, pot_rect)
            pygame.draw.rect(screen, config.DARK_BROWN, pot_rect, 2)
            leaf_center = (rect.centerx, rect.y + rect.height * 0.35)
            pygame.draw.circle(screen, config.PLANT_GREEN, leaf_center, int(rect.width * 0.6))
            pygame.draw.circle(screen, config.DARK_GREEN, leaf_center, int(rect.width * 0.4), 2)
        elif self.kind == "sofa":
            pygame.draw.rect(screen, config.SOFA_BLUE, rect)
            pygame.draw.rect(screen, config.DARK_GRAY, rect, 2)
            cushion = rect.inflate(-rect.width * 0.3, -rect.height * 0.4)
            pygame.draw.rect(screen, config.LIGHT_GRAY, cushion, 1)
        elif self.kind == "table":
            pygame.draw.rect(screen, config.TABLE_BROWN, rect)
            pygame.draw.rect(screen, config.DARK_BROWN, rect, 2)
            leg_width = max(2, int(rect.width * 0.15))
            for x in [rect.left, rect.right - leg_width]:
                pygame.draw.rect(screen, config.DARK_BROWN, (x, rect.bottom - rect.height * 0.2, leg_width, rect.height * 0.2))
        elif self.kind == "chair":
            pygame.draw.rect(screen, config.TABLE_BROWN, rect)
            pygame.draw.rect(screen, config.DARK_BROWN, rect, 2)
            back = pygame.Rect(rect.x, rect.y, rect.width, rect.height * 0.3)
            pygame.draw.rect(screen, config.DARK_BROWN, back)
        elif self.kind == "trash":
            pygame.draw.rect(screen, config.TRASH_GRAY, rect)
            pygame.draw.rect(screen, config.DARK_METAL, rect, 2)
            pygame.draw.line(screen, config.DARK_METAL, (rect.left + 3, rect.top + 3), (rect.right - 3, rect.top + 3), 2)
        elif self.kind == "rug":
            pygame.draw.rect(screen, config.CARPET_DARK, rect)
            pygame.draw.rect(screen, config.CARPET_BLUE, rect, 2)
        elif self.kind == "bottle":
            pygame.draw.rect(screen, config.BOTTLE_GREEN, rect)
            pygame.draw.rect(screen, config.DARK_GREEN, rect, 1)
        else:
            pygame.draw.rect(screen, config.GRAY, rect)
            pygame.draw.rect(screen, config.DARK_GRAY, rect, 1)
