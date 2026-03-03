"""Main game class."""

import pygame
import sys
from pygame.math import Vector2

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE, Colors
import math
from core import Camera, InputHandler, GroundRenderer, ParticleSystem, draw_health, SimpleRoom
from entities import Player, Enemy


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
        self.particle_system = ParticleSystem()
        
        # Initialize entities
        self.player = Player(0, 0)
        self.player.set_punch_callback(self.particle_system.spawn_punch_effect)
        self.camera.set_target(self.player)
        
        # Map
        self.room = SimpleRoom(self.player.position, width=900, height=600, door_width=140)
        
        # Entity lists for future expansion
        self.entities = []
        self.enemies = []
        self._spawn_enemies(5)
        
    def _spawn_enemies(self, count: int):
        """Spawn enemies around the player."""
        import random
        for _ in range(count):
            angle = random.uniform(0, 360)
            distance = random.uniform(220, 420)
            offset = Vector2(
                math.cos(math.radians(angle)) * distance,
                math.sin(math.radians(angle)) * distance
            )
            enemy = Enemy(self.player.position.x + offset.x, self.player.position.y + offset.y)
            enemy.set_target(self.player)
            enemy.set_attack_callback(self._enemy_attack)
            self.enemies.append(enemy)

    def _enemy_attack(self, enemy: Enemy):
        """Handle enemy attacks on player."""
        if not self.player.alive:
            return
        # Apply damage if in range at attack moment
        if enemy.position.distance_to(self.player.position) <= 55:
            self.player.take_damage(1)

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
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.alive:
                enemy.update(dt)
        
        # Remove dead entities
        self.entities = [e for e in self.entities if e.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        
        # Update particles/effects
        self.particle_system.update(dt)
    
    def _draw(self):
        """Render the game."""
        # Clear screen
        self.screen.fill(Colors.DIRT_BASE)
        
        # Get camera offset
        camera_offset = self.camera.get_offset()
        
        # Draw ground
        self.ground.draw(self.screen, camera_offset)
        
        # Draw room walls
        self.room.draw(self.screen, camera_offset)
        
        # Draw entities (sorted by Y for depth)
        all_entities = [self.player] + self.entities + self.enemies
        all_entities.sort(key=lambda e: e.position.y)
        
        for entity in all_entities:
            if entity.alive:
                entity.draw(self.screen, camera_offset)
        
        # Draw particles/effects
        self.particle_system.draw(self.screen, camera_offset)
        
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
        
        # Player health hearts (top right)
        draw_health(self.screen, self.player.health, self.player.max_health, Vector2(SCREEN_WIDTH - 10, 10))
        


def main():
    """Entry point."""
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
