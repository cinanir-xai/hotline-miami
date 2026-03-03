"""Input handling system."""

import pygame
from pygame.math import Vector2


class InputHandler:
    """Centralized input handling."""
    
    def __init__(self):
        self.keys = {}
        self.prev_keys = {}
        self.mouse_pos = Vector2(0, 0)
        self.mouse_buttons = [False, False, False]
        self.prev_mouse_buttons = [False, False, False]
        self.mouse_wheel = 0
        
    def update(self):
        """Update input state."""
        # Store previous states
        self.prev_keys = self.keys.copy()
        self.prev_mouse_buttons = self.mouse_buttons.copy()
        
        # Get current key states
        keys = pygame.key.get_pressed()
        self.keys = {
            'up': keys[pygame.K_w] or keys[pygame.K_UP],
            'down': keys[pygame.K_s] or keys[pygame.K_DOWN],
            'left': keys[pygame.K_a] or keys[pygame.K_LEFT],
            'right': keys[pygame.K_d] or keys[pygame.K_RIGHT],
            'sprint': keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT],
            'interact': keys[pygame.K_e] or keys[pygame.K_SPACE],
        }
        
        # Mouse position
        mx, my = pygame.mouse.get_pos()
        self.mouse_pos = Vector2(mx, my)
        
        # Mouse buttons
        buttons = pygame.mouse.get_pressed()
        self.mouse_buttons = list(buttons)
        
        self.mouse_wheel = 0
    
    def handle_event(self, event: pygame.event.Event):
        """Handle a pygame event."""
        if event.type == pygame.MOUSEWHEEL:
            self.mouse_wheel = event.y
    
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently held."""
        return self.keys.get(key, False)
    
    def is_key_just_pressed(self, key: str) -> bool:
        """Check if a key was just pressed this frame."""
        return self.keys.get(key, False) and not self.prev_keys.get(key, False)
    
    def is_mouse_pressed(self, button: int = 0) -> bool:
        """Check if a mouse button is held (0=left, 1=middle, 2=right)."""
        return self.mouse_buttons[button]
    
    def is_mouse_just_pressed(self, button: int = 0) -> bool:
        """Check if a mouse button was just pressed."""
        return self.mouse_buttons[button] and not self.prev_mouse_buttons[button]
    
    def get_movement_vector(self) -> Vector2:
        """Get normalized movement vector from WASD/arrow keys."""
        vec = Vector2(0, 0)
        if self.keys.get('left'):
            vec.x -= 1
        if self.keys.get('right'):
            vec.x += 1
        if self.keys.get('up'):
            vec.y -= 1
        if self.keys.get('down'):
            vec.y += 1
            
        if vec.length_squared() > 0:
            vec = vec.normalize()
            
        return vec
