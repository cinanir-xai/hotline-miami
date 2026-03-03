"""Wall and map rendering/collision helpers."""

import pygame
from pygame.math import Vector2
from config import Colors


class Wall:
    """Simple wall segment."""
    
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw wall block."""
        screen_rect = self.rect.move(-camera_offset.x, -camera_offset.y)
        pygame.draw.rect(surface, (60, 60, 60), screen_rect)
        pygame.draw.rect(surface, (30, 30, 30), screen_rect, 2)


class SimpleRoom:
    """Simple boxed room with a doorway gap."""
    
    def __init__(self, center: Vector2, width: int = 900, height: int = 600, door_width: int = 120):
        self.center = center
        self.width = width
        self.height = height
        self.door_width = door_width
        self.walls = []
        self._build_walls()
    
    def _build_walls(self):
        """Build wall rectangles with a doorway gap at the bottom wall."""
        half_w = self.width // 2
        half_h = self.height // 2
        wall_thickness = 30
        
        left = self.center.x - half_w
        right = self.center.x + half_w
        top = self.center.y - half_h
        bottom = self.center.y + half_h
        
        # Top wall
        self.walls.append(Wall(pygame.Rect(left, top - wall_thickness, self.width, wall_thickness)))
        # Left wall
        self.walls.append(Wall(pygame.Rect(left - wall_thickness, top, wall_thickness, self.height)))
        # Right wall
        self.walls.append(Wall(pygame.Rect(right, top, wall_thickness, self.height)))
        
        # Bottom wall with gap (door)
        door_left = self.center.x - self.door_width // 2
        door_right = self.center.x + self.door_width // 2
        
        self.walls.append(Wall(pygame.Rect(left, bottom, door_left - left, wall_thickness)))
        self.walls.append(Wall(pygame.Rect(door_right, bottom, right - door_right, wall_thickness)))
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the room walls."""
        for wall in self.walls:
            wall.draw(surface, camera_offset)

    def get_collision_rects(self):
        """Return wall rects for collision."""
        return [wall.rect for wall in self.walls]
