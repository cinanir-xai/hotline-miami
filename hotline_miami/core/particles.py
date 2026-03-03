"""Particle system for visual effects."""

import pygame
import math
import random
from pygame.math import Vector2
from typing import List


class Particle:
    """Base particle class."""
    
    def __init__(self, x: float, y: float, velocity: Vector2, 
                 lifetime: float, color, size: float = 3):
        self.position = Vector2(x, y)
        self.velocity = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.alive = True
        self.alpha = 255
        
    def update(self, dt: float):
        """Update particle state."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return
        
        # Move
        self.position += self.velocity * dt
        
        # Fade out
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        self.alpha = int(255 * (1.0 - progress))
        
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the particle."""
        if not self.alive:
            return
            
        pos = self.position - camera_offset
        
        # Create surface with alpha
        if isinstance(self.color, tuple) and len(self.color) == 4:
            color = self.color[:3]
        else:
            color = self.color
            
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, self.alpha), 
                          (int(self.size), int(self.size)), int(self.size))
        surface.blit(s, (pos.x - self.size, pos.y - self.size))


class PunchEffect:
    """Visual effect for punch impact."""
    
    def __init__(self, x: float, y: float, angle: float):
        self.position = Vector2(x, y)
        self.angle = angle
        self.lifetime = 0.2
        self.max_lifetime = 0.2
        self.alive = True
        self.size = 20
        
    def update(self, dt: float):
        """Update effect."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return
        
        # Expand
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        self.size = 20 + progress * 30
        
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw punch effect."""
        if not self.alive:
            return
            
        pos = self.position - camera_offset
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        alpha = int(200 * (1.0 - progress))
        
        # Draw impact ring
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 200, alpha), 
                          (int(self.size), int(self.size)), int(self.size), 2)
        surface.blit(s, (pos.x - self.size, pos.y - self.size))
        
        # Draw motion lines in punch direction
        line_length = 25
        angle_rad = math.radians(self.angle)
        for offset in [-0.3, 0, 0.3]:
            line_angle = angle_rad + offset
            start = Vector2(
                pos.x - math.cos(line_angle) * 10,
                pos.y - math.sin(line_angle) * 10
            )
            end = Vector2(
                pos.x + math.cos(line_angle) * line_length,
                pos.y + math.sin(line_angle) * line_length
            )
            pygame.draw.line(surface, (255, 255, 200, alpha), 
                           (start.x, start.y), (end.x, end.y), 2)


class ParticleSystem:
    """Manages all particles and effects."""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.effects: List[PunchEffect] = []
    
    def spawn_punch_effect(self, x: float, y: float, angle: float):
        """Spawn a punch impact effect."""
        self.effects.append(PunchEffect(x, y, angle))
        
        # Add some dust particles
        for _ in range(5):
            offset = Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
            vel = Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
            color = (180, 160, 140)
            self.particles.append(Particle(
                x + offset.x, y + offset.y, vel,
                random.uniform(0.3, 0.6), color, random.uniform(2, 4)
            ))
    
    def spawn_dust(self, x: float, y: float, amount: int = 3):
        """Spawn dust particles."""
        for _ in range(amount):
            offset = Vector2(random.uniform(-15, 15), random.uniform(-15, 15))
            vel = Vector2(random.uniform(-20, 20), random.uniform(-20, 20))
            color = (160, 140, 120)
            self.particles.append(Particle(
                x + offset.x, y + offset.y, vel,
                random.uniform(0.5, 1.0), color, random.uniform(2, 5)
            ))
    
    def spawn_blood_explosion(self, x: float, y: float, amount: int = 15):
        """Spawn blood particles on death."""
        for _ in range(amount):
            angle = random.uniform(0, 360)
            speed = random.uniform(40, 120)
            vel = Vector2(
                math.cos(math.radians(angle)) * speed,
                math.sin(math.radians(angle)) * speed
            )
            color = random.choice([(180, 30, 30), (150, 20, 20), (120, 10, 10)])
            size = random.uniform(3, 7)
            self.particles.append(Particle(
                x, y, vel,
                random.uniform(0.4, 0.8), color, size
            ))
        
        # Add some blood splatter spots that stay longer
        for _ in range(8):
            angle = random.uniform(0, 360)
            dist = random.uniform(10, 35)
            vel = Vector2(
                math.cos(math.radians(angle)) * dist * 2,
                math.sin(math.radians(angle)) * dist * 2
            )
            self.particles.append(Particle(
                x, y, vel,
                random.uniform(1.0, 2.0), (100, 10, 10), random.uniform(4, 8)
            ))
    
    def update(self, dt: float):
        """Update all particles and effects."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        
        for e in self.effects:
            e.update(dt)
        self.effects = [e for e in self.effects if e.alive]
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw all particles and effects."""
        for p in self.particles:
            p.draw(surface, camera_offset)
        for e in self.effects:
            e.draw(surface, camera_offset)
