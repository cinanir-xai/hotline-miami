"""Main game class."""

import pygame
import sys
from pygame.math import Vector2

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE, Colors
from core import Camera, InputHandler, GroundRenderer
from entities import Player


class Game:
    """Main game class that manages the game loop and state."""
    
    def __init__(self):
        pygame.init()
        
        # Create window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        # Clock for frame rate control
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize systems
        self.input_handler = InputHandler()
        self.camera = Camera()
        self.ground = GroundRenderer(seed=42)
        
        # Initialize entities
        self.player = Player(0, 0)
        self.camera.set_target(self.player)
        
        # Entity lists for future expansion
        self.entities = []
        self.particles = []
        
    def run(self):
        """Main game loop."""
        self.running = True
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            self._handle_events()
            self._update(dt)
            self._draw()
            
        pygame.quit()
        sys.exit()
    
    def _handle_events(self):
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            
            self.input_handler.handle_event(event)
    
    def _update(self, dt: float):
        """Update game state."""
        # Update input
        self.input_handler.update()
        
        # Get input for player
        keys = pygame.key.get_pressed()
        mouse_clicked = self.input_handler.is_mouse_just_pressed(0)
        
        # Update player
        self.player.handle_input(keys, self.input_handler.mouse_pos, 
                                 mouse_clicked, self.camera.get_offset())
        self.player.update(dt)
        
        # Update camera
        self.camera.update(dt)
        
        # Update other entities
        for entity in self.entities:
            if entity.alive:
                entity.update(dt)
        
        # Remove dead entities
        self.entities = [e for e in self.entities if e.alive]
        
        # Update particles
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.alive]
    
    def _draw(self):
        """Render the game."""
        # Clear screen
        self.screen.fill(Colors.DIRT_BASE)
        
        # Get camera offset
        camera_offset = self.camera.get_offset()
        
        # Draw ground
        self.ground.draw(self.screen, camera_offset)
        
        # Draw entities (sorted by Y for depth)
        all_entities = [self.player] + self.entities
        all_entities.sort(key=lambda e: e.position.y)
        
        for entity in all_entities:
            if entity.alive:
                entity.draw(self.screen, camera_offset)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen, camera_offset)
        
        # Draw UI
        self._draw_ui()
        
        # Update display
        pygame.display.flip()
    
    def _draw_ui(self):
        """Draw user interface."""
        # Simple FPS counter
        fps = int(self.clock.get_fps())
        font = pygame.font.SysFont('arial', 20)
        fps_text = font.render(f'FPS: {fps}', True, Colors.WHITE)
        self.screen.blit(fps_text, (10, 10))
        
        # Controls hint
        hint_text = font.render('WASD: Move | Mouse: Aim | Click: Punch | ESC: Quit', 
                               True, Colors.WHITE)
        self.screen.blit(hint_text, (10, SCREEN_HEIGHT - 30))


def main():
    """Entry point."""
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
