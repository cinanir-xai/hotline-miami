"""Door behavior and rendering."""

from __future__ import annotations

import math
import pygame

from hotline_miami import config


class Door:
    def __init__(self, x: float, y: float, width: float, height: float, hinge_left: bool = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hinge_left = hinge_left
        self.is_open = False
        self.open_amount = 0.0
        self.is_horizontal = width > height
        self.open_speed = 5.0
        self.hit_cooldown = 0.0

    def collides_with_circle(self, cx: float, cy: float, radius: float) -> bool:
        if self.is_open and self.open_amount > 0.8:
            return False
        door_rect = self.get_collision_rect()
        closest_x = max(door_rect.left, min(cx, door_rect.right))
        closest_y = max(door_rect.top, min(cy, door_rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx * dx + dy * dy) < (radius * radius)

    def intersects_line(self, start: pygame.Vector2, end: pygame.Vector2) -> bool:
        if self.is_open and self.open_amount > 0.8:
            return False
        door_rect = self.get_collision_rect()
        return door_rect.clipline((start.x, start.y), (end.x, end.y)) != ()

    def get_collision_rect(self) -> pygame.Rect:
        if self.is_horizontal:
            if self.is_open:
                angle = self.open_amount * (math.pi / 2)
                width = self.width * math.cos(angle)
                height = self.height + self.width * math.sin(angle) * 0.3
                if self.hinge_left:
                    return pygame.Rect(
                        self.x,
                        self.y - height / 2 + self.height / 2,
                        max(width, 5),
                        max(height, 5),
                    )
                return pygame.Rect(
                    self.x + self.width - max(width, 5),
                    self.y - height / 2 + self.height / 2,
                    max(width, 5),
                    max(height, 5),
                )
            return pygame.Rect(self.x, self.y, self.width, self.height)
        if self.is_open:
            angle = self.open_amount * (math.pi / 2)
            height = self.height * math.cos(angle)
            width = self.width + self.height * math.sin(angle) * 0.3
            if self.hinge_left:
                return pygame.Rect(
                    self.x - width / 2 + self.width / 2,
                    self.y,
                    max(width, 5),
                    max(height, 5),
                )
            return pygame.Rect(
                self.x - width / 2 + self.width / 2,
                self.y + self.height - max(height, 5),
                max(width, 5),
                max(height, 5),
            )
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def push(self, entity_x: float, entity_y: float) -> None:
        if self.is_horizontal:
            if entity_y > self.y + self.height:
                self.is_open = True
        else:
            if entity_x < self.x:
                self.is_open = True

    def force_open(self) -> None:
        self.is_open = True
        self.open_speed = 18.0
        self.hit_cooldown = 0.15

    def update(self, dt: float) -> None:
        target = 1.0 if self.is_open else 0.0
        self.open_amount += (target - self.open_amount) * self.open_speed * dt
        if abs(self.open_amount - target) < 0.01:
            self.open_amount = target
        self.open_speed = max(5.0, self.open_speed - 10.0 * dt)
        if self.hit_cooldown > 0:
            self.hit_cooldown -= dt

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        if self.is_horizontal:
            if self.open_amount < 0.1:
                pygame.draw.rect(
                    screen,
                    config.BROWN,
                    (self.x - offset.x, self.y - offset.y, self.width, self.height),
                )
                pygame.draw.rect(
                    screen,
                    config.DARK_BROWN,
                    (self.x - offset.x, self.y - offset.y, self.width, self.height),
                    2,
                )
                hinge_x = self.x + 3 if self.hinge_left else self.x + self.width - 6
                pygame.draw.rect(
                    screen,
                    config.GRAY,
                    (hinge_x - offset.x, self.y - offset.y, 3, self.height),
                )
            else:
                angle = self.open_amount * (math.pi / 2.5)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)

                if self.hinge_left:
                    hinge_x, hinge_y = self.x, self.y + self.height / 2
                    end_x = hinge_x + self.width * cos_a
                    end_y = hinge_y - self.width * sin_a * 0.5
                else:
                    hinge_x, hinge_y = self.x + self.width, self.y + self.height / 2
                    end_x = hinge_x - self.width * cos_a
                    end_y = hinge_y - self.width * sin_a * 0.5

                pygame.draw.line(
                    screen,
                    config.BROWN,
                    (hinge_x - offset.x, hinge_y - offset.y),
                    (end_x - offset.x, end_y - offset.y),
                    int(self.height),
                )
                pygame.draw.circle(
                    screen,
                    config.GRAY,
                    (int(hinge_x - offset.x), int(hinge_y - offset.y)),
                    4,
                )
            return

        if self.open_amount < 0.1:
            pygame.draw.rect(
                screen,
                config.BROWN,
                (self.x - offset.x, self.y - offset.y, self.width, self.height),
            )
            pygame.draw.rect(
                screen,
                config.DARK_BROWN,
                (self.x - offset.x, self.y - offset.y, self.width, self.height),
                2,
            )
            hinge_y = self.y + 3 if self.hinge_left else self.y + self.height - 6
            pygame.draw.rect(
                screen,
                config.GRAY,
                (self.x - offset.x, hinge_y - offset.y, self.width, 3),
            )
            return

        angle = self.open_amount * (math.pi / 2.5)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        if self.hinge_left:
            hinge_x, hinge_y = self.x + self.width / 2, self.y
            end_x = hinge_x + self.height * sin_a * 0.5
            end_y = hinge_y + self.height * cos_a
        else:
            hinge_x, hinge_y = self.x + self.width / 2, self.y + self.height
            end_x = hinge_x + self.height * sin_a * 0.5
            end_y = hinge_y - self.height * cos_a

        pygame.draw.line(
            screen,
            config.BROWN,
            (hinge_x - offset.x, hinge_y - offset.y),
            (end_x - offset.x, end_y - offset.y),
            int(self.width),
        )
        pygame.draw.circle(
            screen,
            config.GRAY,
            (int(hinge_x - offset.x), int(hinge_y - offset.y)),
            4,
        )
