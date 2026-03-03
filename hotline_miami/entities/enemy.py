"""Enemy AI and rendering."""

from __future__ import annotations

import math
import random
import pygame

from hotline_miami import config
from hotline_miami.entities.base import Entity
from hotline_miami.rendering.weapons import draw_bat_sprite, draw_pipe_sprite


class Enemy(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, config.ENEMY_RADIUS, config.ENEMY_SPEED, config.ENEMY_HP)
        self.punch_cooldown = 0.0
        self.in_range_timer = 0.0
        self.wander_timer = 0.0
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        self.can_see_player = False
        self.has_bat = False
        self.has_pipe = False
        self.bat_durability = config.BAT_DURABILITY
        self.pipe_durability = config.PIPE_DURABILITY

    def update(self, dt: float, player, walls: list, doors: list) -> None:
        if not self.alive:
            return

        if self.attack_timer > 0:
            self.attack_timer -= dt

        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        self.can_see_player = False
        if dist < config.ENEMY_LOS_RANGE and player.alive:
            start = pygame.Vector2(self.x, self.y)
            end = pygame.Vector2(player.x, player.y)
            blocked = False
            for wall in walls:
                if wall.intersects_line(start, end):
                    blocked = True
                    break
            if not blocked:
                for door in doors:
                    if door.intersects_line(start, end):
                        blocked = True
                        break
            self.can_see_player = not blocked

        if dist < config.ENEMY_DETECTION_RANGE and player.alive and self.can_see_player:
            if dist > 0:
                self.vx = dx / dist
                self.vy = dy / dist
        else:
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(1.0, 3.0)
                angle = random.uniform(0, 2 * math.pi)
                self.wander_dx = math.cos(angle)
                self.wander_dy = math.sin(angle)
            self.vx = self.wander_dx
            self.vy = self.wander_dy

        attack_range = config.BAT_RANGE if (self.has_bat or self.has_pipe) else config.ENEMY_PUNCH_RANGE
        if dist <= attack_range and self.can_see_player:
            self.in_range_timer += dt
        else:
            self.in_range_timer = 0.0

    def can_punch(self, player) -> bool:
        if not self.alive or not player.alive or self.punch_cooldown > 0:
            return False
        if not self.can_see_player:
            return False
        if self.in_range_timer < config.ENEMY_PUNCH_WINDUP:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist <= (config.BAT_RANGE if (self.has_bat or self.has_pipe) else config.ENEMY_PUNCH_RANGE)

    def punch(self, facing_angle: float) -> None:
        has_weapon = self.has_bat or self.has_pipe
        self.punch_cooldown = config.ENEMY_BAT_COOLDOWN if has_weapon else config.ENEMY_PUNCH_COOLDOWN
        self.attack_timer = 0.2
        self.attack_radius = 8 if not has_weapon else 10
        side = self.attack_side
        self.attack_side *= -1
        self.attack_angle = facing_angle + side * 0.7
        self.attack_offset = (
            pygame.Vector2(math.cos(self.attack_angle), math.sin(self.attack_angle)) * (self.radius + 10)
        )

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        pygame.draw.circle(screen, config.ORANGE, (int(self.x - offset.x), int(self.y - offset.y)), self.radius)
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            anim_pos = pygame.Vector2(self.x, self.y) + self.attack_offset * progress
            if not (self.has_bat or self.has_pipe):
                pygame.draw.circle(
                    screen,
                    config.ORANGE,
                    (int(anim_pos.x - offset.x), int(anim_pos.y - offset.y)),
                    self.attack_radius,
                )
            else:
                swing_arc = config.PIPE_SWING_ARC if self.has_pipe else config.BAT_SWING_ARC
                swing_angle = self.attack_angle + (progress - 0.5) * swing_arc
                if self.has_pipe:
                    draw_pipe_sprite(screen, anim_pos, swing_angle, offset, scale=1.0)
                else:
                    draw_bat_sprite(screen, anim_pos, swing_angle, offset, scale=1.0)
        if self.has_bat or self.has_pipe:
            hand_pos = pygame.Vector2(self.x, self.y) + (
                pygame.Vector2(math.cos(self.attack_angle), math.sin(self.attack_angle)) * (self.radius + 6)
            )
            if self.has_pipe:
                draw_pipe_sprite(screen, hand_pos, self.attack_angle, offset, scale=0.7)
            else:
                draw_bat_sprite(screen, hand_pos, self.attack_angle, offset, scale=0.7)
        hp_pct = self.hp / config.ENEMY_HP
        pygame.draw.rect(
            screen,
            config.BLACK,
            (int(self.x - 10 - offset.x), int(self.y - self.radius - 8 - offset.y), 20, 4),
        )
        pygame.draw.rect(
            screen,
            config.GREEN if hp_pct > 0.5 else config.YELLOW if hp_pct > 0.25 else config.RED,
            (
                int(self.x - 10 - offset.x),
                int(self.y - self.radius - 8 - offset.y),
                int(20 * hp_pct),
                4,
            ),
        )
