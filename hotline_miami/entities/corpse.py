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
        for _ in range(random.randint(12, 20)):
            angle = random.uniform(0, 2 * 3.14159)
            dist = random.uniform(0, radius * 2.5)
            bx = x + math.cos(angle) * dist
            by = y + math.sin(angle) * dist
            self.blood.append(Blood(bx, by))
        
        # Ragdoll state: random limb positions
        self.rotation = random.uniform(0, 2 * 3.14159)
        self.limb_offsets = []
        for _ in range(4): # 2 arms, 2 legs
            self.limb_offsets.append((
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                random.uniform(0, 2 * 3.14159)
            ))

    def draw(self, screen: pygame.Surface, offset: pygame.Vector2) -> None:
        for blood in self.blood:
            blood.draw(screen, offset)
        
        pos = pygame.Vector2(self.x - offset.x, self.y - offset.y)
        color = config.GREEN if self.is_player else config.ORANGE
        skin_color = (220, 180, 140)
        
        # Draw legs (as simple rectangles/lines)
        for i in range(2):
            l_angle = self.rotation + (0.5 if i == 0 else -0.5) + self.limb_offsets[i][2] * 0.2
            l_dir = pygame.Vector2(math.cos(l_angle), math.sin(l_angle))
            l_end = pos - l_dir * 15
            pygame.draw.line(screen, color, (int(pos.x), int(pos.y)), (int(l_end.x), int(l_end.y)), 6)
            
        # Draw arms
        for i in range(2, 4):
            a_angle = self.rotation + (1.5 if i == 2 else -1.5) + self.limb_offsets[i][2] * 0.2
            a_dir = pygame.Vector2(math.cos(a_angle), math.sin(a_angle))
            a_end = pos + a_dir * 12
            pygame.draw.line(screen, color, (int(pos.x), int(pos.y)), (int(a_end.x), int(a_end.y)), 5)

        # Draw Torso
        pygame.draw.circle(screen, color, (int(pos.x), int(pos.y)), 8)
        
        # Draw Head (displaced slightly)
        h_pos = pos + pygame.Vector2(math.cos(self.rotation), math.sin(self.rotation)) * 5
        pygame.draw.circle(screen, skin_color, (int(h_pos.x), int(h_pos.y)), 6)
        # Hair
        hair_color = (100, 50, 20) if self.is_player else (180, 160, 40)
        pygame.draw.circle(screen, hair_color, (int(h_pos.x), int(h_pos.y)), 4)
