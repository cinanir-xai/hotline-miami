"""Main game class."""

import pygame
import sys
import math
import random
from pygame.math import Vector2

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE, Colors
from core import Camera, InputHandler, GroundRenderer, ParticleSystem, draw_health, SimpleRoom, Door
from entities import Player, Enemy, Corpse


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
        
        # Map - player starts outside, south of the house
        self.player = Player(0, 250)  # Start below the house
        self.player.set_punch_callback(self.particle_system.spawn_punch_effect)
        self.player.set_death_callback(self._on_player_death)
        self.camera.set_target(self.player)
        
        # Create multiple rooms (house layout)
        self.rooms = []
        self._build_house()
        
        # Doors
        self.doors = []
        self._create_doors()
        
        # Corpses (persist throughout level)
        self.corpses = []
        
        # Entity lists
        self.entities = []
        self.enemies = []
        self._spawn_enemies(5)
        
    def _build_house(self):
        """Build a house with multiple rooms."""
        # Main room (south entrance)
        main_room = SimpleRoom(Vector2(0, -50), width=700, height=500, door_width=140)
        self.rooms.append(main_room)
        
        # East room
        east_room = SimpleRoom(Vector2(450, -50), width=500, height=400, door_width=100)
        self.rooms.append(east_room)
        
        # North room (connected to main)
        north_room = SimpleRoom(Vector2(0, -400), width=600, height=400, door_width=120)
        self.rooms.append(north_room)
        
        # West room
        west_room = SimpleRoom(Vector2(-450, -50), width=450, height=400, door_width=100)
        self.rooms.append(west_room)
    
    def _create_doors(self):
        """Create physics-based doors between rooms."""
        # Main entrance (south)
        self.doors.append(Door(Vector2(0, 200), is_horizontal=True, width=120))
        
        # Main to East
        self.doors.append(Door(Vector2(350, -50), is_horizontal=False, width=100))
        
        # Main to North
        self.doors.append(Door(Vector2(0, -250), is_horizontal=True, width=100))
        
        # Main to West
        self.doors.append(Door(Vector2(-350, -50), is_horizontal=False, width=100))
    
    def _on_player_death(self, corpse: Corpse):
        """Handle player death."""
        self.particle_system.spawn_blood_explosion(self.player.position.x, self.player.position.y)
        self.corpses.append(corpse)
    
    def _on_enemy_death(self, corpse: Corpse):
        """Handle enemy death."""
        self.particle_system.spawn_blood_explosion(corpse.position.x, corpse.position.y)
        self.corpses.append(corpse)

    def _spawn_enemies(self, count: int):
        """Spawn enemies around the player."""
        import random
        for _ in range(count):
            # Spawn enemies inside the house (north of entrance)
            x = random.uniform(-300, 300)
            y = random.uniform(-300, 100)
            enemy = Enemy(x, y)
            enemy.set_target(self.player)
            enemy.set_attack_callback(self._enemy_attack)
            enemy.set_death_callback(self._on_enemy_death)
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
        
        # Update corpses
        for corpse in self.corpses:
            corpse.update(dt)
        
        # Update doors
        for door in self.doors:
            door.update(dt, self.player, self.enemies)
        
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
        
        # Draw house floor (inside rooms)
        self._draw_house_floor(camera_offset)
        
        # Draw room walls
        for room in self.rooms:
            room.draw(self.screen, camera_offset)
        
        # Draw doors
        for door in self.doors:
            door.draw(self.screen, camera_offset)
        
        # Draw corpses (under everything)
        for corpse in self.corpses:
            corpse.draw(self.screen, camera_offset)
        
        # Draw entities (sorted by Y for depth)
        all_entities = []
        if self.player.alive:
            all_entities.append(self.player)
        all_entities.extend([e for e in self.entities if e.alive])
        all_entities.extend([e for e in self.enemies if e.alive])
        all_entities.sort(key=lambda e: e.position.y)
        
        for entity in all_entities:
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
        if self.player.alive:
            draw_health(self.screen, self.player.health, self.player.max_health, Vector2(SCREEN_WIDTH - 10, 10))
        

    def _draw_house_floor(self, camera_offset: Vector2):
        """Draw floor inside the house rooms."""
        floor_color = (140, 120, 100)  # Wooden floor
        for room in self.rooms:
            # Get room bounds
            half_w = room.width // 2
            half_h = room.height // 2
            rect = pygame.Rect(
                room.center.x - half_w - camera_offset.x,
                room.center.y - half_h - camera_offset.y,
                room.width,
                room.height
            )
            pygame.draw.rect(self.screen, floor_color, rect)
            # Floor planks texture
            for i in range(0, room.height, 20):
                y = room.center.y - half_h + i - camera_offset.y
                pygame.draw.line(self.screen, (120, 100, 80),
                               (room.center.x - half_w - camera_offset.x, y),
                               (room.center.x + half_w - camera_offset.x, y), 1)


def main():
    """Entry point."""
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
