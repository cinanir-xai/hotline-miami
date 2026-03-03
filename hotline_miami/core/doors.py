"""Physics-based doors."""

import pygame
import math
from pygame.math import Vector2


class Door:
    """A physics-based door that swings open when pushed."""
    
    def __init__(self, position: Vector2, is_horizontal: bool = True, width: float = 100):
        self.position = position
        self.is_horizontal = is_horizontal
        self.width = width
        self.thickness = 8
        
        # Door state
        self.angle = 0.0  # Current rotation angle (0 = closed)
        self.angular_velocity = 0.0
        self.max_angle = 90.0  # Maximum open angle
        self.spring_strength = 8.0  # How fast it closes
        self.damping = 0.92  # Friction
        self.push_strength = 15.0  # How much player pushes
        
        # Collision rect (when closed)
        if is_horizontal:
            self.closed_rect = pygame.Rect(
                position.x - width / 2, position.y - self.thickness / 2,
                width, self.thickness
            )
        else:
            self.closed_rect = pygame.Rect(
                position.x - self.thickness / 2, position.y - width / 2,
                self.thickness, width
            )
    
    def update(self, dt: float, player, enemies):
        """Update door physics."""
        # Check collisions with player
        if player.alive:
            self._check_entity_collision(player, dt)
        
        # Check collisions with enemies
        for enemy in enemies:
            if enemy.alive:
                self._check_entity_collision(enemy, dt)
        
        # Spring physics (return to closed)
        self.angular_velocity -= self.spring_strength * math.sin(math.radians(self.angle)) * dt
        self.angular_velocity *= self.damping
        self.angle += self.angular_velocity
        
        # Clamp angle
        self.angle = max(-self.max_angle, min(self.max_angle, self.angle))
    
    def _check_entity_collision(self, entity, dt: float):
        """Check if entity is pushing the door."""
        # Simple circle-rect collision
        entity_radius = entity.size / 2
        closest_x = max(self.closed_rect.left, min(entity.position.x, self.closed_rect.right))
        closest_y = max(self.closed_rect.top, min(entity.position.y, self.closed_rect.bottom))
        
        dx = entity.position.x - closest_x
        dy = entity.position.y - closest_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < entity_radius:
            # Entity is pushing the door
            push_direction = 1 if dx > 0 or dy > 0 else -1
            
            # Get entity velocity in direction perpendicular to door
            if self.is_horizontal:
                push = entity.velocity.y * push_direction
            else:
                push = entity.velocity.x * push_direction
            
            if abs(push) > 10:  # Minimum velocity to push
                self.angular_velocity += push_direction * self.push_strength * dt
    
    def get_collision_rect(self):
        """Get current collision rect based on angle."""
        if abs(self.angle) < 5:
            return self.closed_rect
        # When open, door doesn't block
        return pygame.Rect(0, 0, 0, 0)
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the door."""
        # Calculate door endpoints based on angle
        half_w = self.width / 2
        
        if self.is_horizontal:
            # Door rotates around center
            cos_a = math.cos(math.radians(self.angle))
            sin_a = math.sin(math.radians(self.angle))
            
            # Start and end points of door
            x1 = self.position.x - half_w * cos_a
            y1 = self.position.y - half_w * sin_a
            x2 = self.position.x + half_w * cos_a
            y2 = self.position.y + half_w * sin_a
        else:
            # Vertical door
            cos_a = math.cos(math.radians(self.angle))
            sin_a = math.sin(math.radians(self.angle))
            
            x1 = self.position.x - half_w * sin_a
            y1 = self.position.y - half_w * cos_a
            x2 = self.position.x + half_w * sin_a
            y2 = self.position.y + half_w * cos_a
        
        # Convert to screen coords
        sx1 = x1 - camera_offset.x
        sy1 = y1 - camera_offset.y
        sx2 = x2 - camera_offset.x
        sy2 = y2 - camera_offset.y
        
        # Draw door panel
        pygame.draw.line(surface, (139, 90, 43), (sx1, sy1), (sx2, sy2), self.thickness)
        pygame.draw.line(surface, (80, 50, 30), (sx1, sy1), (sx2, sy2), 2)
        
        # Draw hinge
        hinge_x = self.position.x - camera_offset.x
        hinge_y = self.position.y - camera_offset.y
        pygame.draw.circle(surface, (60, 60, 60), (int(hinge_x), int(hinge_y)), 4)
        
        # Draw door handle
        handle_x = (x1 + x2) / 2 + camera_offset.x * 0  # Midpoint
        handle_y = (y1 + y2) / 2
        # Offset handle from center
        if self.is_horizontal:
            handle_x = self.position.x + 15
            handle_y = self.position.y + 15 * math.sin(math.radians(self.angle))
        else:
            handle_x = self.position.x + 15 * math.sin(math.radians(self.angle))
            handle_y = self.position.y + 15
        
        screen_handle_x = handle_x - camera_offset.x
        screen_handle_y = handle_y - camera_offset.y
        pygame.draw.circle(surface, (200, 180, 100), (int(screen_handle_x), int(screen_handle_y)), 3)
