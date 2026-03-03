"""UI rendering utilities."""

import pygame
from pygame.math import Vector2
from config import Colors


def draw_heart(surface: pygame.Surface, pos: Vector2, size: int, filled: bool = True):
    """Draw a heart icon."""
    color = (220, 50, 50) if filled else (120, 80, 80)
    outline = (60, 20, 20)
    x, y = pos.x, pos.y
    
    # Heart composed of two circles and a triangle
    heart_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    radius = size * 0.25
    center_y = size * 0.35
    
    pygame.draw.circle(heart_surface, color, (int(size * 0.3), int(center_y)), int(radius))
    pygame.draw.circle(heart_surface, color, (int(size * 0.7), int(center_y)), int(radius))
    points = [
        (size * 0.1, center_y),
        (size * 0.9, center_y),
        (size * 0.5, size * 0.95)
    ]
    pygame.draw.polygon(heart_surface, color, points)
    
    # Outline
    pygame.draw.circle(heart_surface, outline, (int(size * 0.3), int(center_y)), int(radius), 1)
    pygame.draw.circle(heart_surface, outline, (int(size * 0.7), int(center_y)), int(radius), 1)
    pygame.draw.polygon(heart_surface, outline, points, 1)
    
    surface.blit(heart_surface, (x, y))


def draw_health(surface: pygame.Surface, health: int, max_health: int, top_right: Vector2):
    """Draw health hearts at the top right."""
    size = 24
    spacing = 6
    for i in range(max_health):
        pos = Vector2(top_right.x - (i + 1) * (size + spacing), top_right.y)
        draw_heart(surface, pos, size, filled=i < health)
