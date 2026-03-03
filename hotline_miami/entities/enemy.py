"""Enemy entity with wandering and chasing behavior."""

import pygame
import math
import random
from pygame.math import Vector2

from .entity import Entity
from config import (
    ENEMY_SIZE, ENEMY_SPEED, ENEMY_ACCEL, ENEMY_DECEL,
    ENEMY_ATTACK_RANGE, ENEMY_ATTACK_COOLDOWN, ENEMY_ATTACK_DAMAGE,
    ENEMY_MAX_HEALTH, ENEMY_DETECTION_RANGE,
    ENEMY_WANDER_INTERVAL, ENEMY_WANDER_RADIUS,
    PUNCH_DURATION, PUNCH_EXTEND_DISTANCE, Colors
)
from utils.math_utils import lerp, angle_from_vec, vec_from_angle


class Enemy(Entity):
    """Enemy that wanders and chases the player."""
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, ENEMY_SIZE)
        
        # Behavior
        self.target = None
        self.wander_timer = 0.0
        self.wander_direction = Vector2(0, 0)
        self.state = "wander"
        
        # Combat
        self.attack_cooldown = random.uniform(0.2, 0.6)
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_angle = 0.0
        self.attack_hand = "right"
        self.on_attack_callback = None
        
        # Animation
        self.bob_offset = 0.0
        self.arm_extension = 0.0
        self.facing = Vector2(0, 1)
        
        # Health
        self.max_health = ENEMY_MAX_HEALTH
        self.health = ENEMY_MAX_HEALTH
        
        # Visual
        self.head_radius = 13
        self.shoulder_width = 28
        self.shoulder_height = 18
        self.neck_offset = 3
        self.hand_radius = 4
        self.shirt_color = (180, 60, 60)
        self.jacket_color = (100, 40, 40)
    
    def set_target(self, target):
        """Set the player target."""
        self.target = target
    
    def set_attack_callback(self, callback):
        """Set callback for dealing damage."""
        self.on_attack_callback = callback
    
    def update(self, dt: float):
        """Update enemy behavior and animation."""
        super().update(dt)
        
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # Update behavior
        if self.target:
            distance = self.target.position.distance_to(self.position)
            if distance < ENEMY_DETECTION_RANGE:
                self.state = "chase"
                self._chase_target(dt, distance)
            else:
                self.state = "wander"
                self._wander(dt)
        else:
            self._wander(dt)
        
        # Update attack animation
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.arm_extension = 0.0
            else:
                progress = 1.0 - (self.attack_timer / PUNCH_DURATION)
                self.arm_extension = math.sin(progress * math.pi) * PUNCH_EXTEND_DISTANCE
        
        # Apply movement
        self.position += self.velocity * dt
        
        # Bob animation
        if self.velocity.length_squared() > 1:
            self.bob_offset = math.sin(self.animation_time * 12) * 1.5
        else:
            self.bob_offset = lerp(self.bob_offset, 0, dt * 10)
    
    def _wander(self, dt: float):
        """Random wandering behavior."""
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_timer = ENEMY_WANDER_INTERVAL + random.uniform(-0.5, 0.5)
            angle = random.uniform(0, 360)
            self.wander_direction = vec_from_angle(angle, 1)
        
        self._move_towards(self.wander_direction, dt)
    
    def _chase_target(self, dt: float, distance: float):
        """Chase the player and attack if in range."""
        direction = (self.target.position - self.position)
        if direction.length_squared() > 0:
            self.facing = direction.normalize()
        
        if distance <= ENEMY_ATTACK_RANGE:
            self.velocity = Vector2(0, 0)
            if self.attack_cooldown <= 0 and not self.is_attacking:
                self._start_attack()
        else:
            self._move_towards(self.facing, dt)
    
    def _move_towards(self, direction: Vector2, dt: float):
        """Move with acceleration/deceleration."""
        if direction.length_squared() > 0:
            target = direction.normalize() * ENEMY_SPEED
            self.velocity = Vector2(
                lerp(self.velocity.x, target.x, 1 - math.exp(-ENEMY_ACCEL * dt)),
                lerp(self.velocity.y, target.y, 1 - math.exp(-ENEMY_ACCEL * dt))
            )
        else:
            self.velocity = Vector2(
                lerp(self.velocity.x, 0, 1 - math.exp(-ENEMY_DECEL * dt)),
                lerp(self.velocity.y, 0, 1 - math.exp(-ENEMY_DECEL * dt))
            )
        
    def _start_attack(self):
        """Start an attack animation and apply damage."""
        self.is_attacking = True
        self.attack_timer = PUNCH_DURATION
        self.attack_cooldown = ENEMY_ATTACK_COOLDOWN
        self.attack_angle = angle_from_vec(self.facing)
        self.attack_hand = "left" if self.attack_hand == "right" else "right"
        
        if self.on_attack_callback:
            self.on_attack_callback(self)
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the enemy."""
        pos = self.position - camera_offset
        
        # Draw shadow
        self.draw_shadow(surface, camera_offset, radius=15, alpha=50)
        
        # Calculate positions
        head_center = Vector2(pos.x, pos.y - 8 + self.bob_offset) + self.facing * 2
        shoulder_y = pos.y + 6 + self.bob_offset * 0.5
        
        # Get arm positions
        arm_offset = self._get_arm_offsets(pos, shoulder_y)
        
        # Draw arms behind
        self._draw_arms(surface, arm_offset, behind=True)
        
        # Draw shoulders
        self._draw_shoulders(surface, pos, shoulder_y)
        
        # Draw neck and head
        self._draw_neck(surface, shoulder_y, head_center)
        self._draw_head(surface, head_center)
        
        # Draw arms in front
        self._draw_arms(surface, arm_offset, behind=False)
    
    def _get_arm_offsets(self, pos: Vector2, shoulder_y: float) -> dict:
        """Calculate arm positions based on facing direction."""
        shoulder_left = Vector2(-self.shoulder_width * 0.4, shoulder_y - pos.y)
        shoulder_right = Vector2(self.shoulder_width * 0.4, shoulder_y - pos.y)
        
        if self.is_attacking:
            extend_vec = vec_from_angle(self.attack_angle, self.arm_extension)
            if self.attack_hand == "right":
                shoulder_right += extend_vec
            else:
                shoulder_left += extend_vec
        
        facing_angle = angle_from_vec(self.facing)
        side_factor = abs(math.cos(math.radians(facing_angle))) * 3
        
        if 90 < facing_angle < 270:
            shoulder_left.x -= side_factor
            shoulder_right.x -= side_factor * 0.5
        else:
            shoulder_left.x += side_factor * 0.5
            shoulder_right.x += side_factor
        
        return {
            'left': Vector2(pos.x + shoulder_left.x, pos.y + shoulder_left.y),
            'right': Vector2(pos.x + shoulder_right.x, pos.y + shoulder_right.y)
        }
    
    def _draw_shoulders(self, surface: pygame.Surface, pos: Vector2, shoulder_y: float):
        """Draw shoulders and torso."""
        body_rect = pygame.Rect(
            pos.x - self.shoulder_width / 2,
            shoulder_y - self.shoulder_height / 2,
            self.shoulder_width,
            self.shoulder_height
        )
        pygame.draw.ellipse(surface, self.jacket_color, body_rect)
        
        shirt_rect = pygame.Rect(
            pos.x - self.shoulder_width * 0.25,
            shoulder_y - self.shoulder_height * 0.3,
            self.shoulder_width * 0.5,
            self.shoulder_height * 0.6
        )
        pygame.draw.ellipse(surface, self.shirt_color, shirt_rect)
    
    def _draw_neck(self, surface: pygame.Surface, shoulder_y: float, head_center: Vector2):
        """Draw neck."""
        neck_width = 7
        neck_height = 5
        neck_rect = pygame.Rect(
            head_center.x - neck_width / 2,
            shoulder_y - neck_height / 2 - self.neck_offset,
            neck_width,
            neck_height
        )
        pygame.draw.ellipse(surface, Colors.SKIN_MID, neck_rect)
    
    def _draw_head(self, surface: pygame.Surface, head_center: Vector2):
        """Draw head."""
        head_rect = pygame.Rect(
            head_center.x - self.head_radius,
            head_center.y - self.head_radius,
            self.head_radius * 2,
            self.head_radius * 2
        )
        pygame.draw.ellipse(surface, Colors.SKIN_LIGHT, head_rect)
        shade_rect = pygame.Rect(
            head_center.x - self.head_radius + 2,
            head_center.y - self.head_radius + 2,
            self.head_radius * 2 - 4,
            self.head_radius * 2 - 4
        )
        pygame.draw.ellipse(surface, Colors.SKIN_MID, shade_rect)
        
        facing_angle = angle_from_vec(self.facing)
        nose_offset = vec_from_angle(facing_angle, self.head_radius * 0.5)
        nose_pos = (head_center.x + nose_offset.x, head_center.y + nose_offset.y)
        pygame.draw.ellipse(surface, Colors.SKIN_SHADOW,
                           (nose_pos[0] - 3, nose_pos[1] - 2, 6, 4))
        
        # Simple hair patch
        hair_radius = self.head_radius * 0.8
        back_angle = facing_angle + 180
        hair_center = vec_from_angle(back_angle, self.head_radius * 0.3)
        hair_x = head_center.x + hair_center.x
        hair_y = head_center.y + hair_center.y
        pygame.draw.ellipse(surface, Colors.HAIR_DARK,
                           (hair_x - hair_radius, hair_y - hair_radius,
                            hair_radius * 2, hair_radius * 2))
        
        # Eyes
        eye_offset_x = 5
        eye_offset_y = 3
        vertical_factor = abs(math.cos(math.radians(facing_angle)))
        if vertical_factor > 0.3:
            if 0 <= facing_angle <= 180:
                eye_y = head_center.y + eye_offset_y
            else:
                eye_y = head_center.y - eye_offset_y
            pygame.draw.circle(surface, Colors.BLACK,
                             (head_center.x - eye_offset_x, eye_y), 1)
            pygame.draw.circle(surface, Colors.BLACK,
                             (head_center.x + eye_offset_x, eye_y), 1)
    
    def _draw_arms(self, surface: pygame.Surface, arm_offset: dict, behind: bool):
        """Draw arms."""
        arm_width = 8
        arm_length = 12
        
        for hand, arm_pos in arm_offset.items():
            is_right = hand == "right"
            facing_angle = angle_from_vec(self.facing)
            arm_behind = False
            if 90 < facing_angle < 270:
                arm_behind = is_right
            else:
                arm_behind = not is_right
            
            if arm_behind == behind:
                arm_rect = pygame.Rect(
                    arm_pos.x - arm_width / 2,
                    arm_pos.y - arm_length / 2,
                    arm_width,
                    arm_length
                )
                pygame.draw.ellipse(surface, self.jacket_color, arm_rect)
                
                hand_offset = vec_from_angle(angle_from_vec(self.facing), arm_length * 0.3)
                if self.is_attacking and hand == self.attack_hand:
                    hand_offset = vec_from_angle(self.attack_angle,
                                                 arm_length * 0.3 + self.arm_extension * 0.3)
                
                hand_pos = (arm_pos.x + hand_offset.x, arm_pos.y + hand_offset.y)
                pygame.draw.circle(surface, Colors.SKIN_MID, hand_pos, self.hand_radius)
