"""Player entity and controls."""

from __future__ import annotations

import math
import pygame

from hotline_miami import config
from hotline_miami.entities.base import Entity
from hotline_miami.rendering.weapons import draw_bat_sprite, draw_pipe_sprite


class Player(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, config.PLAYER_RADIUS, config.PLAYER_SPEED, config.PLAYER_HP)
        self.punch_cooldown = 0.0
        self.facing_angle = 0.0

    def update(self, dt: float, keys, mouse_pos) -> None:
        if not self.alive:
            return

        self.vx = 0
        self.vy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = 1

        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.707
            self.vy *= 0.707

        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        self.facing_angle = math.atan2(dy, dx)

        if self.attack_timer > 0:
            self.attack_timer -= dt

        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt

    def punch(self, has_weapon: bool = False) -> bool:
        if not self.alive or self.punch_cooldown > 0:
            return False
        self.punch_cooldown = config.PLAYER_BAT_COOLDOWN if has_weapon else config.PLAYER_PUNCH_COOLDOWN
        self.attack_timer = 0.2
        self.attack_radius = 8 if not has_weapon else 10
        side = self.attack_side
        self.attack_side *= -1
        self.attack_angle = self.facing_angle + side * 0.7
        self.attack_offset = (
            pygame.Vector2(math.cos(self.attack_angle), math.sin(self.attack_angle)) * (self.radius + 10)
        )
        return True

    def get_punch_hitbox(self) -> tuple:
        px = self.x + math.cos(self.facing_angle) * config.PLAYER_PUNCH_RANGE
        py = self.y + math.sin(self.facing_angle) * config.PLAYER_PUNCH_RANGE
        return (px, py)

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2, has_bat: bool, has_pipe: bool) -> None:
        if not self.alive:
            return
        
        pos = pygame.Vector2(self.x - offset.x, self.y - offset.y)
        angle = self.facing_angle
        dir_vec = pygame.Vector2(math.cos(angle), math.sin(angle))
        side_vec = pygame.Vector2(-dir_vec.y, dir_vec.x)
        
        # Calculate arm positions based on attack animation
        left_arm_ext = 0
        right_arm_ext = 0
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            # Punch extension: out and back
            extension = math.sin(progress * math.pi) * 15
            if self.attack_side == -1: # Last side was 1, then flipped to -1 in punch()
                right_arm_ext = extension
            else:
                left_arm_ext = extension

        # Draw Arms/Shoulders
        shoulder_width = 12
        arm_thickness = 7
        
        # Left Arm
        l_shoulder = pos + side_vec * -shoulder_width + dir_vec * (2 + left_arm_ext)
        pygame.draw.circle(screen, config.GREEN, (int(l_shoulder.x), int(l_shoulder.y)), arm_thickness)
        
        # Right Arm
        r_shoulder = pos + side_vec * shoulder_width + dir_vec * (2 + right_arm_ext)
        pygame.draw.circle(screen, config.GREEN, (int(r_shoulder.x), int(r_shoulder.y)), arm_thickness)

        # Body/Torso (Shoulder connection)
        pygame.draw.line(screen, config.GREEN, (int(l_shoulder.x), int(l_shoulder.y)), (int(r_shoulder.x), int(r_shoulder.y)), 10)

        # Head (Top down: Hair and skin)
        head_radius = 8
        pygame.draw.circle(screen, (240, 200, 160), (int(pos.x), int(pos.y)), head_radius) # Skin
        # Hair (Brownish messy top)
        pygame.draw.circle(screen, (100, 50, 20), (int(pos.x), int(pos.y)), head_radius - 2)
        # Small detail for face direction (nose/eyes hint)
        face_tip = pos + dir_vec * head_radius
        pygame.draw.circle(screen, (240, 200, 160), (int(face_tip.x), int(face_tip.y)), 3)

        # Weapon rendering
        hand_offset = self.radius + 6
        right_hand = pygame.Vector2(self.x, self.y) + dir_vec * 2 + side_vec * shoulder_width + dir_vec * right_arm_ext
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            swing_arc = config.PIPE_SWING_ARC if has_pipe else config.BAT_SWING_ARC
            swing_angle = self.attack_angle + (progress - 0.5) * swing_arc
            swing_center = right_hand + dir_vec * hand_offset
            if has_bat or has_pipe:
                if has_pipe:
                    draw_pipe_sprite(screen, swing_center, swing_angle, offset, scale=1.1)
                else:
                    draw_bat_sprite(screen, swing_center, swing_angle, offset, scale=1.1)
                arc_radius = config.BAT_RANGE if has_bat else config.BAT_RANGE * 0.9
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
        if (has_bat or has_pipe) and self.attack_timer <= 0:
            hand_pos = right_hand + dir_vec * hand_offset
            if has_pipe:
                draw_pipe_sprite(screen, hand_pos, self.facing_angle, offset, scale=0.8)
            else:
                draw_bat_sprite(screen, hand_pos, self.facing_angle, offset, scale=0.8)
