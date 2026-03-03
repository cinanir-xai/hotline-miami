"""Corpse and blood pool visuals."""

from __future__ import annotations

import math
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
        for _ in range(random.randint(18, 28)):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius * 3.0)
            bx = x + math.cos(angle) * dist
            by = y + math.sin(angle) * dist
            self.blood.append(Blood(bx, by))
        for _ in range(random.randint(6, 12)):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(radius * 0.6, radius * 2.2)
            bx = x + math.cos(angle) * dist
            by = y + math.sin(angle) * dist
            pool = Blood(bx, by)
            pool.radius = random.randint(7, 13)
            pool.color = random.choice([config.DARK_RED, config.DARK_ORANGE])
            self.blood.append(pool)

        # Ragdoll state: random limb positions
        self.rotation = random.uniform(0, 2 * math.pi)
        self.limb_offsets = []
        for _ in range(4):
            self.limb_offsets.append(
                (
                    random.uniform(-10, 10),
                    random.uniform(-10, 10),
                    random.uniform(0, 2 * math.pi),
                )
            )

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        for blood in self.blood:
            blood.draw(screen, offset)
        
        pos = pygame.Vector2(self.x - offset.x, self.y - offset.y)
        color = config.GREEN if self.is_player else config.ORANGE
        skin_color = (220, 180, 140)
        
        dir_vec = pygame.Vector2(math.cos(self.rotation), math.sin(self.rotation))
        side_vec = pygame.Vector2(-dir_vec.y, dir_vec.x)
        shoulder_width = 10
        arm_thickness = 6

        # Legs
        for i in range(2):
            l_angle = self.rotation + (0.6 if i == 0 else -0.6) + self.limb_offsets[i][2] * 0.2
            l_dir = pygame.Vector2(math.cos(l_angle), math.sin(l_angle))
            l_start = pos + dir_vec * -4 + side_vec * (4 if i == 0 else -4)
            l_end = l_start - l_dir * 16
            pygame.draw.line(screen, color, (int(l_start.x), int(l_start.y)), (int(l_end.x), int(l_end.y)), 6)

        # Arms (match player/enemy shoulder positioning)
        l_shoulder = pos + side_vec * -shoulder_width + dir_vec * 2
        r_shoulder = pos + side_vec * shoulder_width + dir_vec * 2
        for idx, shoulder in enumerate([l_shoulder, r_shoulder]):
            a_angle = self.rotation + (1.6 if idx == 0 else -1.6) + self.limb_offsets[idx + 2][2] * 0.2
            a_dir = pygame.Vector2(math.cos(a_angle), math.sin(a_angle))
            a_end = shoulder + a_dir * 12
            pygame.draw.line(screen, color, (int(shoulder.x), int(shoulder.y)), (int(a_end.x), int(a_end.y)), arm_thickness)

        # Torso (slightly larger, flattened)
        torso_center = pos + dir_vec * -2
        pygame.draw.ellipse(screen, color, (torso_center.x - 11, torso_center.y - 7, 22, 14))

        # Head (displaced slightly)
        h_pos = pos + dir_vec * 6
        pygame.draw.circle(screen, skin_color, (int(h_pos.x), int(h_pos.y)), 7)
        # Hair
        hair_color = (100, 50, 20) if self.is_player else (180, 160, 40)
        pygame.draw.circle(screen, hair_color, (int(h_pos.x), int(h_pos.y)), 5)
