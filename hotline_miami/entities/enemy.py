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

        attack_range = config.BAT_RANGE if (self.has_bat or self.has_pipe) else config.ENEMY_PUNCH_RANGE
        stop_range = attack_range * 0.9

        if dist < config.ENEMY_DETECTION_RANGE and player.alive and self.can_see_player:
            if dist > stop_range and dist > 0:
                self.vx = dx / dist
                self.vy = dy / dist
            else:
                self.vx = 0.0
                self.vy = 0.0
        else:
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(1.0, 3.0)
                angle = random.uniform(0, 2 * math.pi)
                self.wander_dx = math.cos(angle)
                self.wander_dy = math.sin(angle)
            self.vx = self.wander_dx
            self.vy = self.wander_dy

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
        
        pos = pygame.Vector2(self.x - offset.x, self.y - offset.y)
        # Enemies face their movement direction or attack angle
        if self.attack_timer > 0:
            angle = self.attack_angle
        elif self.vx != 0 or self.vy != 0:
            angle = math.atan2(self.vy, self.vx)
        else:
            angle = 0 # Default
            
        dir_vec = pygame.Vector2(math.cos(angle), math.sin(angle))
        side_vec = pygame.Vector2(-dir_vec.y, dir_vec.x)
        
        # Calculate arm positions based on attack animation
        left_arm_ext = 0
        right_arm_ext = 0
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            extension = math.sin(progress * math.pi) * 12
            if self.attack_side == -1:
                right_arm_ext = extension
            else:
                left_arm_ext = extension

        # Draw Arms/Shoulders
        shoulder_width = 11
        arm_thickness = 6
        
        # Left Arm
        l_shoulder = pos + side_vec * -shoulder_width + dir_vec * (2 + left_arm_ext)
        pygame.draw.circle(screen, config.ORANGE, (int(l_shoulder.x), int(l_shoulder.y)), arm_thickness)
        
        # Right Arm
        r_shoulder = pos + side_vec * shoulder_width + dir_vec * (2 + right_arm_ext)
        pygame.draw.circle(screen, config.ORANGE, (int(r_shoulder.x), int(r_shoulder.y)), arm_thickness)

        # Body/Torso
        pygame.draw.line(screen, config.ORANGE, (int(l_shoulder.x), int(l_shoulder.y)), (int(r_shoulder.x), int(r_shoulder.y)), 9)

        # Head
        head_radius = 7
        pygame.draw.circle(screen, (220, 180, 140), (int(pos.x), int(pos.y)), head_radius) # Skin
        # Hair (Blonde/Yellowish for enemies to distinguish)
        pygame.draw.circle(screen, (180, 160, 40), (int(pos.x), int(pos.y)), head_radius - 2)

        # Weapon rendering
        hand_offset = self.radius + 6
        right_hand = pygame.Vector2(self.x, self.y) + dir_vec * 2 + side_vec * shoulder_width + dir_vec * right_arm_ext
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            swing_arc = config.PIPE_SWING_ARC if self.has_pipe else config.BAT_SWING_ARC
            swing_angle = self.attack_angle + (progress - 0.5) * swing_arc
            swing_center = right_hand + dir_vec * hand_offset
            if self.has_bat or self.has_pipe:
                if self.has_pipe:
                    draw_pipe_sprite(screen, swing_center, swing_angle, offset, scale=1.0)
                else:
                    draw_bat_sprite(screen, swing_center, swing_angle, offset, scale=1.0)
                arc_radius = config.BAT_RANGE if self.has_bat else config.BAT_RANGE * 0.9
                arc_start = self.attack_angle - swing_arc / 2
                arc_end = self.attack_angle + swing_arc / 2
                steps = 8
                arc_points = []
                for i in range(steps + 1):
                    t = arc_start + (arc_end - arc_start) * (i / steps)
                    arc_points.append(
                        (
                            int(self.x + math.cos(t) * arc_radius - offset.x),
                            int(self.y + math.sin(t) * arc_radius - offset.y),
                        )
                    )
                if len(arc_points) > 1:
                    pygame.draw.lines(screen, config.WHITE, False, arc_points, 2)
        if (self.has_bat or self.has_pipe) and self.attack_timer <= 0:
            hand_pos = right_hand + dir_vec * hand_offset
            if self.has_pipe:
                draw_pipe_sprite(screen, hand_pos, angle, offset, scale=0.7)
            else:
                draw_bat_sprite(screen, hand_pos, angle, offset, scale=0.7)

        # Health bar
        hp_pct = self.hp / config.ENEMY_HP
        pygame.draw.rect(
            screen,
            config.BLACK,
            (int(self.x - 10 - offset.x), int(self.y - self.radius - 12 - offset.y), 20, 4),
        )
        pygame.draw.rect(
            screen,
            config.GREEN if hp_pct > 0.5 else config.YELLOW if hp_pct > 0.25 else config.RED,
            (
                int(self.x - 10 - offset.x),
                int(self.y - self.radius - 12 - offset.y),
                int(20 * hp_pct),
                4,
            ),
        )
