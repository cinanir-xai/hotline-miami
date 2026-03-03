"""Corpse entity for dead characters."""

import pygame
import math
from pygame.math import Vector2

from config import Colors


class Corpse:
    """A dead body lying on the ground, face up (full body visible from top)."""
    
    def __init__(self, x: float, y: float, facing: Vector2, 
                 jacket_color, shirt_color, is_player: bool = False):
        self.position = Vector2(x, y)
        self.facing = facing
        self.jacket_color = jacket_color
        self.shirt_color = shirt_color
        self.is_player = is_player
        self.alive = True  # For compatibility with entity lists
        
        # Death animation progress (0 to 1)
        self.death_progress = 0.0
        self.death_duration = 0.4  # seconds to fall
        self.fall_angle = 0.0  # Current rotation as they fall
        
        # Blood particles spawned
        self.blood_spawned = False
        
    def update(self, dt: float):
        """Update death animation."""
        if self.death_progress < 1.0:
            self.death_progress = min(1.0, self.death_progress + dt / self.death_duration)
            # Ease out the fall
            t = self.death_progress
            self.fall_angle = 90 * (1 - (1 - t) * (1 - t))  # Ease out quad
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the corpse lying face up."""
        pos = self.position - camera_offset
        
        # Draw blood pool underneath
        if self.death_progress > 0.3:
            blood_alpha = int(200 * min(1.0, (self.death_progress - 0.3) / 0.5))
            blood_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.ellipse(blood_surf, (150, 20, 20, blood_alpha), (0, 20, 80, 40))
            pygame.draw.ellipse(blood_surf, (100, 10, 10, blood_alpha // 2), (10, 30, 60, 25))
            surface.blit(blood_surf, (pos.x - 40, pos.y - 20))
        
        # Draw body lying flat (face up = full body visible)
        # Body is now horizontal on the ground
        body_length = 55
        body_width = 28
        
        # Torso/Jacket (center)
        torso_rect = pygame.Rect(
            pos.x - body_width / 2,
            pos.y - body_length * 0.3,
            body_width,
            body_length * 0.6
        )
        pygame.draw.ellipse(surface, self.jacket_color, torso_rect)
        
        # Shirt visible (open jacket)
        shirt_rect = pygame.Rect(
            pos.x - body_width * 0.3,
            pos.y - body_length * 0.2,
            body_width * 0.6,
            body_length * 0.4
        )
        pygame.draw.ellipse(surface, self.shirt_color, shirt_rect)
        
        # Arms spread out
        arm_width = 10
        arm_length = 22
        # Left arm
        left_arm_rect = pygame.Rect(
            pos.x - body_width / 2 - arm_length + 5,
            pos.y - 5,
            arm_length,
            arm_width
        )
        pygame.draw.ellipse(surface, self.jacket_color, left_arm_rect)
        pygame.draw.circle(surface, Colors.SKIN_MID, 
                          (int(pos.x - body_width / 2 - arm_length + 5), int(pos.y)), 5)
        
        # Right arm
        right_arm_rect = pygame.Rect(
            pos.x + body_width / 2 - 5,
            pos.y - 5,
            arm_length,
            arm_width
        )
        pygame.draw.ellipse(surface, self.jacket_color, right_arm_rect)
        pygame.draw.circle(surface, Colors.SKIN_MID, 
                          (int(pos.x + body_width / 2 + arm_length - 5), int(pos.y)), 5)
        
        # Legs (lower body)
        leg_width = 12
        leg_length = 25
        # Left leg
        left_leg_rect = pygame.Rect(
            pos.x - leg_width - 2,
            pos.y + body_length * 0.25,
            leg_width,
            leg_length
        )
        pygame.draw.ellipse(surface, (60, 40, 30), left_leg_rect)  # Dark pants
        # Right leg
        right_leg_rect = pygame.Rect(
            pos.x + 2,
            pos.y + body_length * 0.25,
            leg_width,
            leg_length
        )
        pygame.draw.ellipse(surface, (60, 40, 30), right_leg_rect)
        
        # Head (at top, face up)
        head_radius = 14
        head_y = pos.y - body_length * 0.55
        head_rect = pygame.Rect(
            pos.x - head_radius,
            head_y - head_radius,
            head_radius * 2,
            head_radius * 2
        )
        pygame.draw.ellipse(surface, Colors.SKIN_LIGHT, head_rect)
        
        # Face details (face up so we see full face)
        # Eyes (looking up)
        eye_y = head_y - 3
        pygame.draw.circle(surface, Colors.WHITE, (int(pos.x - 5), int(eye_y)), 3)
        pygame.draw.circle(surface, Colors.BLACK, (int(pos.x - 5), int(eye_y)), 2)
        pygame.draw.circle(surface, Colors.WHITE, (int(pos.x + 5), int(eye_y)), 3)
        pygame.draw.circle(surface, Colors.BLACK, (int(pos.x + 5), int(eye_y)), 2)
        
        # Nose
        pygame.draw.ellipse(surface, Colors.SKIN_SHADOW,
                           (pos.x - 2, head_y + 2, 4, 3))
        
        # Mouth (slight frown/death expression)
        pygame.draw.arc(surface, (150, 100, 80),
                       (pos.x - 4, head_y + 5, 8, 4),
                       math.radians(20), math.radians(160), 1)
        
        # Hair around head
        hair_radius = head_radius + 3
        pygame.draw.ellipse(surface, Colors.HAIR_BROWN,
                           (pos.x - hair_radius, head_y - hair_radius + 2,
                            hair_radius * 2, hair_radius * 1.5))
        
        # Blood splatter on body
        if self.death_progress > 0.5:
            for i in range(3):
                bx = pos.x + (i - 1) * 10 + pygame.math.Vector2(1, 0).rotate(i * 45).x * 5
                by = pos.y + (i - 1) * 5 + pygame.math.Vector2(1, 0).rotate(i * 45).y * 5
                pygame.draw.circle(surface, (120, 20, 20), (int(bx), int(by)), 4)
