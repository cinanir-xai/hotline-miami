"""Camera system for following the player."""

import pygame
from pygame.math import Vector2

from config import SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_SMOOTHNESS
from utils.math_utils import lerp


class Camera:
    """Smooth camera that follows a target."""
    
    def __init__(self, target=None):
        self.position = Vector2(0, 0)
        self.target = target
        self.shake_amount = 0.0
        self.shake_decay = 0.0
        
    def set_target(self, target):
        """Set the target to follow."""
        self.target = target
        if target:
            self.position = target.position.copy()
    
    def add_shake(self, amount: float, decay: float = 5.0):
        """Add screen shake."""
        self.shake_amount = amount
        self.shake_decay = decay
    
    def update(self, dt: float):
        """Update camera position."""
        if self.target:
            # Smooth follow
            target_pos = self.target.position
            self.position.x = lerp(self.position.x, target_pos.x, CAMERA_SMOOTHNESS)
            self.position.y = lerp(self.position.y, target_pos.y, CAMERA_SMOOTHNESS)
        
        # Decay shake
        if self.shake_amount > 0:
            self.shake_amount = max(0, self.shake_amount - self.shake_decay * dt)
    
    def get_offset(self) -> Vector2:
        """Get the camera offset for rendering."""
        offset = self.position.copy()
        
        # Add shake
        if self.shake_amount > 0:
            import random
            offset.x += random.uniform(-self.shake_amount, self.shake_amount)
            offset.y += random.uniform(-self.shake_amount, self.shake_amount)
        
        # Center on screen
        offset.x -= SCREEN_WIDTH / 2
        offset.y -= SCREEN_HEIGHT / 2
        
        return offset
    
    def world_to_screen(self, world_pos: Vector2) -> Vector2:
        """Convert world position to screen position."""
        return world_pos - self.get_offset()
    
    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """Convert screen position to world position."""
        return screen_pos + self.get_offset()
    
    def get_view_rect(self) -> pygame.Rect:
        """Get the visible world rectangle."""
        offset = self.get_offset()
        return pygame.Rect(offset.x, offset.y, SCREEN_WIDTH, SCREEN_HEIGHT)
