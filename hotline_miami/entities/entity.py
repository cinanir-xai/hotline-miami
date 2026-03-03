"""Base entity class."""

import pygame
from pygame.math import Vector2
from abc import ABC, abstractmethod
from typing import Optional


class Entity(ABC):
    """Base class for all game entities."""
    
    def __init__(self, x: float, y: float, size: float = 32):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.size = size
        self.rotation = 0.0  # degrees
        self.alive = True
        self.health = 1
        self.max_health = 1
        
        # Animation state
        self.animation_time = 0.0
        self.state = "idle"
        
    @property
    def rect(self) -> pygame.Rect:
        """Get the bounding rectangle."""
        half_size = self.size / 2
        return pygame.Rect(
            self.position.x - half_size,
            self.position.y - half_size,
            self.size,
            self.size
        )
    
    @property
    def center(self) -> Vector2:
        """Get the center position."""
        return self.position
    
    def move(self, direction: Vector2, speed: float, dt: float):
        """Move in a direction."""
        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.velocity = direction * speed
        
    def take_damage(self, amount: float) -> bool:
        """Take damage and return True if killed."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.on_death()
            return True
        return False
    
    def on_death(self):
        """Called when entity dies. Override in subclass."""
        pass
    
    def update(self, dt: float):
        """Update entity state."""
        self.animation_time += dt
        
        # Apply velocity
        self.position += self.velocity * dt
        
    @abstractmethod
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the entity. Must be implemented by subclasses."""
        pass
    
    def draw_shadow(self, surface: pygame.Surface, camera_offset: Vector2, 
                    radius: float = None, alpha: int = 60):
        """Draw a shadow beneath the entity."""
        if radius is None:
            radius = self.size * 0.4
            
        shadow_surface = pygame.Surface((int(radius * 2), int(radius * 2)), 
                                        pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, alpha), 
                           (0, 0, int(radius * 2), int(radius * 1.2)))
        
        pos = self.position - camera_offset
        shadow_rect = shadow_surface.get_rect(center=(pos.x, pos.y + self.size * 0.3))
        surface.blit(shadow_surface, shadow_rect)
