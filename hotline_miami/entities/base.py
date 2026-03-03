"""Base entity class shared by player and enemies."""

from __future__ import annotations

from typing import List
import pygame

from hotline_miami import config


class Entity:
    def __init__(self, x: float, y: float, radius: float, speed: float, hp: int):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.hp = hp
        self.max_hp = hp
        self.alive = True
        self.vx = 0.0
        self.vy = 0.0
        self.attack_timer = 0.0
        self.attack_side = 1
        self.attack_offset = pygame.Vector2(0, 0)
        self.attack_radius = 0
        self.attack_angle = 0.0

    def move(self, dt: float, walls: List, doors: List, props: List) -> None:
        if not self.alive:
            return

        new_x = self.x + self.vx * self.speed * dt
        new_y = self.y + self.vy * self.speed * dt

        collides_x = False
        collides_y = False

        for wall in walls:
            if wall.contains_point(new_x, self.y, self.radius):
                collides_x = True
            if wall.contains_point(self.x, new_y, self.radius):
                collides_y = True

        for door in doors:
            if not door.is_open and door.collides_with_circle(new_x, self.y, self.radius):
                collides_x = True
            if not door.is_open and door.collides_with_circle(self.x, new_y, self.radius):
                collides_y = True

        for prop in props:
            if prop.contains_point(new_x, self.y, self.radius):
                collides_x = True
            if prop.contains_point(self.x, new_y, self.radius):
                collides_y = True

        if not collides_x:
            self.x = new_x
        if not collides_y:
            self.y = new_y

        self.x = max(self.radius, min(config.WORLD_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(config.WORLD_HEIGHT - self.radius, self.y))
