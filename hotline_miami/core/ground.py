"""Ground/environment rendering."""

import pygame
import random
import math
from pygame.math import Vector2

from config import TILE_SIZE, Colors, SCREEN_WIDTH, SCREEN_HEIGHT


class GroundRenderer:
    """Renders the ground/environment."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.noise_cache = {}
        self._generate_textures()
    
    def _generate_textures(self):
        """Generate procedural ground textures."""
        random.seed(self.seed)
        
        # Generate various dirt tile variations
        self.tile_variations = []
        for i in range(8):
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self._draw_dirt_tile(surface, i)
            self.tile_variations.append(surface)
        
        random.seed()  # Reset seed
    
    def _draw_dirt_tile(self, surface: pygame.Surface, variation: int):
        """Draw a single dirt tile with variation."""
        # Base color
        base_colors = [Colors.DIRT_BASE, Colors.DIRT_LIGHT, Colors.DIRT_DARK]
        base = base_colors[variation % len(base_colors)]
        surface.fill(base)
        
        # Add noise/texture
        for _ in range(20):
            x = random.randint(0, TILE_SIZE - 1)
            y = random.randint(0, TILE_SIZE - 1)
            size = random.randint(1, 3)
            
            # Vary color slightly
            color_var = random.randint(-20, 20)
            r = clamp(base[0] + color_var)
            g = clamp(base[1] + color_var)
            b = clamp(base[2] + color_var)
            
            pygame.draw.circle(surface, (r, g, b), (x, y), size)
        
        # Add some larger texture patches
        for _ in range(3):
            x = random.randint(0, TILE_SIZE)
            y = random.randint(0, TILE_SIZE)
            rx = random.randint(8, 20)
            ry = random.randint(6, 15)
            
            color = random.choice([Colors.DIRT_LIGHT, Colors.DIRT_DARK])
            pygame.draw.ellipse(surface, color, (x - rx, y - ry, rx * 2, ry * 2))
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the ground visible by the camera."""
        # Calculate visible tile range
        start_x = int(camera_offset.x // TILE_SIZE) - 1
        start_y = int(camera_offset.y // TILE_SIZE) - 1
        end_x = int((camera_offset.x + SCREEN_WIDTH) // TILE_SIZE) + 1
        end_y = int((camera_offset.y + SCREEN_HEIGHT) // TILE_SIZE) + 1
        
        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                # Use position-based pseudo-random variation
                variation = (tx * 73856093 ^ ty * 19349663) % len(self.tile_variations)
                
                tile = self.tile_variations[variation]
                screen_x = tx * TILE_SIZE - camera_offset.x
                screen_y = ty * TILE_SIZE - camera_offset.y
                
                surface.blit(tile, (screen_x, screen_y))
        
        # Draw some decorative elements (rocks, cracks, etc.)
        self._draw_decorations(surface, camera_offset, start_x, start_y, end_x, end_y)
    
    def _draw_decorations(self, surface: pygame.Surface, camera_offset: Vector2,
                          start_x: int, start_y: int, end_x: int, end_y: int):
        """Draw decorative elements on the ground."""
        random.seed(self.seed)
        
        for ty in range(start_y - 5, end_y + 5):
            for tx in range(start_x - 5, end_x + 5):
                # Deterministic random based on position
                pos_hash = (tx * 73856093 ^ ty * 19349663 ^ self.seed)
                random.seed(pos_hash)
                
                # 5% chance for a decoration
                if random.random() < 0.05:
                    screen_x = tx * TILE_SIZE - camera_offset.x + TILE_SIZE // 2
                    screen_y = ty * TILE_SIZE - camera_offset.y + TILE_SIZE // 2
                    
                    # Add offset within tile
                    screen_x += random.randint(-20, 20)
                    screen_y += random.randint(-20, 20)
                    
                    dec_type = random.randint(0, 3)
                    
                    if dec_type == 0:
                        # Small rock
                        color = random.choice([(90, 90, 90), (120, 120, 120), (70, 70, 70)])
                        size = random.randint(3, 6)
                        pygame.draw.ellipse(surface, color, 
                                          (screen_x - size, screen_y - size//2, 
                                           size * 2, size))
                    elif dec_type == 1:
                        # Crack in ground
                        color = Colors.DIRT_DARK
                        points = []
                        cx, cy = screen_x, screen_y
                        for _ in range(3):
                            points.append((cx, cy))
                            cx += random.randint(-10, 10)
                            cy += random.randint(-10, 10)
                        if len(points) > 1:
                            pygame.draw.lines(surface, color, False, points, 1)
                    elif dec_type == 2:
                        # Small pebbles
                        color = random.choice([(100, 80, 60), (80, 70, 50)])
                        for _ in range(3):
                            px = screen_x + random.randint(-5, 5)
                            py = screen_y + random.randint(-5, 5)
                            pygame.draw.circle(surface, color, (px, py), 1)
                    elif dec_type == 3:
                        # Dark patch
                        color = Colors.DIRT_DARK
                        size = random.randint(5, 12)
                        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                        pygame.draw.ellipse(s, (*color, 60), (0, 0, size * 2, size))
                        surface.blit(s, (screen_x - size, screen_y - size // 2))
        
        random.seed()  # Reset seed


def clamp(value, min_val=0, max_val=255):
    """Clamp value to range."""
    return max(min_val, min(max_val, int(value)))
