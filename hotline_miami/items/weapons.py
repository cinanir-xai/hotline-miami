"""Weapon items and thrown weapon projectiles."""

from __future__ import annotations

import math
import pygame

from hotline_miami import config
from hotline_miami.rendering.weapons import draw_bat_sprite, draw_pipe_sprite, draw_pistol_sprite


class BatItem:
    def __init__(self, x: float, y: float, durability: int = config.BAT_DURABILITY, is_pipe: bool = False):
        self.x = x
        self.y = y
        self.durability = durability
        self.is_pipe = is_pipe

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        if self.is_pipe:
            draw_pipe_sprite(
                screen,
                pygame.Vector2(self.x, self.y),
                0.25,
                offset,
                scale=config.PIPE_GROUND_SCALE,
                outline=True,
            )
        else:
            draw_bat_sprite(
                screen,
                pygame.Vector2(self.x, self.y),
                0.35,
                offset,
                scale=config.BAT_GROUND_SCALE,
                outline=True,
            )


class BatProjectile:
    def __init__(self, x: float, y: float, velocity: pygame.Vector2, durability: int, is_pipe: bool = False):
        self.x = x
        self.y = y
        self.velocity = velocity
        self.durability = durability
        self.is_pipe = is_pipe
        self.alive = True
        self.life = config.BAT_PROJECTILE_LIFE
        self.spin = 0.0

    def update(self, dt: float, walls: list, doors: list) -> None:
        if not self.alive:
            return
        next_x = self.x + self.velocity.x * dt
        next_y = self.y + self.velocity.y * dt

        collided = False
        for wall in walls:
            if wall.contains_point(next_x, next_y, 6):
                collided = True
                break
        if not collided:
            for door in doors:
                if not door.is_open and door.collides_with_circle(next_x, next_y, 6):
                    collided = True
                    break

        if collided:
            self.velocity *= config.WEAPON_THROW_WALL_DAMPING
            self.velocity = -self.velocity * config.WEAPON_THROW_BOUNCE
            if self.velocity.length() < config.WEAPON_THROW_STOP_SPEED:
                self.alive = False
                return
        else:
            self.x = next_x
            self.y = next_y

        spin_speed = config.PIPE_PROJECTILE_SPIN if self.is_pipe else config.BAT_PROJECTILE_SPIN
        self.spin += spin_speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        if self.is_pipe:
            draw_pipe_sprite(screen, pygame.Vector2(self.x, self.y), self.spin, offset, scale=1.0)
        else:
            draw_bat_sprite(screen, pygame.Vector2(self.x, self.y), self.spin, offset, scale=1.0)


class PistolItem:
    def __init__(self, x: float, y: float, ammo: int = config.PISTOL_AMMO):
        self.x = x
        self.y = y
        self.ammo = ammo

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        draw_pistol_sprite(
            screen,
            pygame.Vector2(self.x, self.y),
            0.15,
            offset,
            scale=1.0,
            outline=True,
        )


class BulletProjectile:
    def __init__(
        self,
        x: float,
        y: float,
        velocity: pygame.Vector2,
        source_is_player: bool,
        owner_id: int | None = None,
    ):
        self.x = x
        self.y = y
        self.velocity = velocity
        self.source_is_player = source_is_player
        self.owner_id = owner_id
        self.alive = True
        self.life = config.PISTOL_BULLET_LIFE

    def update(self, dt: float, walls: list, doors: list) -> None:
        if not self.alive:
            return
        next_x = self.x + self.velocity.x * dt
        next_y = self.y + self.velocity.y * dt

        for wall in walls:
            if wall.contains_point(next_x, next_y, 2):
                self.alive = False
                return

        for door in doors:
            if door.intersects_line(pygame.Vector2(self.x, self.y), pygame.Vector2(next_x, next_y)):
                door.force_open()
                break

        self.x = next_x
        self.y = next_y
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        tip = pygame.Vector2(self.x, self.y)
        if self.velocity.length() == 0:
            tail = tip
        else:
            tail = tip - self.velocity.normalize() * 10
        pygame.draw.line(
            screen,
            config.YELLOW,
            (int(tail.x - offset.x), int(tail.y - offset.y)),
            (int(tip.x - offset.x), int(tip.y - offset.y)),
            2,
        )
        pygame.draw.circle(
            screen,
            (255, 230, 150),
            (int(tip.x - offset.x), int(tip.y - offset.y)),
            3,
        )
