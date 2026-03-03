"""Hotline Miami - Complete Rewrite (Basic Shapes Only)"""
import pygame
import math
import random
from typing import List, Optional

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 60, 60)
RED = (200, 50, 50)
DARK_RED = (150, 30, 30)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (255, 255, 0)
BROWN = (139, 90, 43)
DARK_BROWN = (100, 60, 30)

# Screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Player
PLAYER_RADIUS = 15
PLAYER_SPEED = 220
PLAYER_HP = 5
PLAYER_PUNCH_RANGE = 50
PLAYER_PUNCH_COOLDOWN = 0.4

# Enemy
ENEMY_RADIUS = 14
ENEMY_SPEED = 130
ENEMY_HP = 3
ENEMY_PUNCH_RANGE = 45
ENEMY_PUNCH_COOLDOWN = 3.0
ENEMY_DETECTION_RANGE = 300


class Blood:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 8)
        self.color = random.choice([RED, DARK_RED])
        
    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


class Corpse:
    def __init__(self, x: float, y: float, radius: float, is_player: bool = False):
        self.x = x
        self.y = y
        self.radius = radius
        self.is_player = is_player
        self.blood: List[Blood] = []
        # Create blood pool around corpse
        for _ in range(random.randint(8, 15)):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius * 1.5)
            bx = x + math.cos(angle) * dist
            by = y + math.sin(angle) * dist
            self.blood.append(Blood(bx, by))
    
    def draw(self, screen: pygame.Surface):
        # Draw blood first (underneath)
        for blood in self.blood:
            blood.draw(screen)
        # Draw corpse as flattened circle
        color = GREEN if self.is_player else RED
        pygame.draw.ellipse(screen, color, 
                          (int(self.x - self.radius), int(self.y - self.radius/2),
                           int(self.radius * 2), int(self.radius)))


class Entity:
    def __init__(self, x: float, y: float, radius: float, speed: float, hp: int):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.hp = hp
        self.max_hp = hp
        self.alive = True
        self.vx = 0.0
        self.vy = 0.0
        
    def move(self, dt: float, walls: List['Wall'], doors: List['Door']):
        if not self.alive:
            return
            
        new_x = self.x + self.vx * self.speed * dt
        new_y = self.y + self.vy * self.speed * dt
        
        # Check wall collisions
        collides_x = False
        collides_y = False
        
        for wall in walls:
            if wall.contains_point(new_x, self.y, self.radius):
                collides_x = True
            if wall.contains_point(self.x, new_y, self.radius):
                collides_y = True
        
        for door in doors:
            if not door.is_open and door.collides_with_circle(new_x, self.y, self.radius):
                collides_x = True
            if not door.is_open and door.collides_with_circle(self.x, new_y, self.radius):
                collides_y = True
        
        if not collides_x:
            self.x = new_x
        if not collides_y:
            self.y = new_y
        
        # Keep in bounds
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))


class Player(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, PLAYER_RADIUS, PLAYER_SPEED, PLAYER_HP)
        self.punch_cooldown = 0.0
        self.facing_angle = 0.0
        
    def update(self, dt: float, keys, mouse_pos):
        if not self.alive:
            return
            
        # Movement
        self.vx = 0
        self.vy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = 1
        
        # Normalize diagonal
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.707
            self.vy *= 0.707
        
        # Face mouse
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        self.facing_angle = math.atan2(dy, dx)
        
        # Cooldown
        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt
    
    def punch(self) -> bool:
        if not self.alive or self.punch_cooldown > 0:
            return False
        self.punch_cooldown = PLAYER_PUNCH_COOLDOWN
        return True
    
    def get_punch_hitbox(self) -> tuple:
        """Returns (x, y) of punch position"""
        px = self.x + math.cos(self.facing_angle) * PLAYER_PUNCH_RANGE
        py = self.y + math.sin(self.facing_angle) * PLAYER_PUNCH_RANGE
        return (px, py)
    
    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return
        # Body
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), self.radius)
        # Direction indicator
        end_x = self.x + math.cos(self.facing_angle) * (self.radius + 5)
        end_y = self.y + math.sin(self.facing_angle) * (self.radius + 5)
        pygame.draw.line(screen, DARK_GRAY, (self.x, self.y), (end_x, end_y), 3)
        # Punch indicator if on cooldown
        if self.punch_cooldown > PLAYER_PUNCH_COOLDOWN * 0.5:
            px, py = self.get_punch_hitbox()
            pygame.draw.circle(screen, YELLOW, (int(px), int(py)), 8)


class Enemy(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, ENEMY_RADIUS, ENEMY_SPEED, ENEMY_HP)
        self.punch_cooldown = 0.0
        self.wander_timer = 0.0
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        
    def update(self, dt: float, player: Player, walls: List['Wall'], doors: List['Door']):
        if not self.alive:
            return
            
        # Cooldown
        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt
        
        # Distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < ENEMY_DETECTION_RANGE and player.alive:
            # Chase player
            if dist > 0:
                self.vx = dx / dist
                self.vy = dy / dist
        else:
            # Wander
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self.wander_timer = random.uniform(1.0, 3.0)
                angle = random.uniform(0, 2 * math.pi)
                self.wander_dx = math.cos(angle)
                self.wander_dy = math.sin(angle)
            self.vx = self.wander_dx
            self.vy = self.wander_dy
    
    def can_punch(self, player: Player) -> bool:
        if not self.alive or not player.alive or self.punch_cooldown > 0:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist <= ENEMY_PUNCH_RANGE
    
    def punch(self):
        self.punch_cooldown = ENEMY_PUNCH_COOLDOWN
    
    def draw(self, screen: pygame.Surface):
        if not self.alive:
            return
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        # Health indicator
        hp_pct = self.hp / ENEMY_HP
        pygame.draw.rect(screen, BLACK, (int(self.x - 10), int(self.y - self.radius - 8), 20, 4))
        pygame.draw.rect(screen, GREEN if hp_pct > 0.5 else YELLOW if hp_pct > 0.25 else RED,
                        (int(self.x - 10), int(self.y - self.radius - 8), int(20 * hp_pct), 4))


class Wall:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.rect = pygame.Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def contains_point(self, x: float, y: float, radius: float = 0) -> bool:
        return (x - radius < self.x + self.width and x + radius > self.x and
                y - radius < self.y + self.height and y + radius > self.y)
    
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, GRAY, self.rect, 2)


class Door:
    def __init__(self, x: float, y: float, width: float, height: float, hinge_left: bool = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hinge_left = hinge_left  # True = left/top hinge, False = right/bottom
        self.is_open = False
        self.open_amount = 0.0  # 0 = closed, 1 = fully open
        self.is_horizontal = width > height
        
    def collides_with_circle(self, cx: float, cy: float, radius: float) -> bool:
        if self.is_open and self.open_amount > 0.8:
            return False
        # Simplified collision with door rect
        door_rect = self.get_collision_rect()
        closest_x = max(door_rect.left, min(cx, door_rect.right))
        closest_y = max(door_rect.top, min(cy, door_rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx * dx + dy * dy) < (radius * radius)
    
    def get_collision_rect(self) -> pygame.Rect:
        if self.is_horizontal:
            # Horizontal door
            if self.is_open:
                angle = self.open_amount * (math.pi / 2)
                w = self.width * math.cos(angle)
                h = self.height + self.width * math.sin(angle) * 0.3
                if self.hinge_left:
                    return pygame.Rect(self.x, self.y - h/2 + self.height/2, max(w, 5), max(h, 5))
                else:
                    return pygame.Rect(self.x + self.width - max(w, 5), self.y - h/2 + self.height/2, max(w, 5), max(h, 5))
            else:
                return pygame.Rect(self.x, self.y, self.width, self.height)
        else:
            # Vertical door
            if self.is_open:
                angle = self.open_amount * (math.pi / 2)
                h = self.height * math.cos(angle)
                w = self.width + self.height * math.sin(angle) * 0.3
                if self.hinge_left:
                    return pygame.Rect(self.x - w/2 + self.width/2, self.y, max(w, 5), max(h, 5))
                else:
                    return pygame.Rect(self.x - w/2 + self.width/2, self.y + self.height - max(h, 5), max(w, 5), max(h, 5))
            else:
                return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def push(self, entity_x: float, entity_y: float):
        """Try to push door open from entity position"""
        # Determine if pushing from correct side
        if self.is_horizontal:
            # Horizontal door - push from below to open outward
            if entity_y > self.y + self.height:
                self.is_open = True
        else:
            # Vertical door - push from left to open outward  
            if entity_x < self.x:
                self.is_open = True
    
    def update(self, dt: float):
        target = 1.0 if self.is_open else 0.0
        self.open_amount += (target - self.open_amount) * 5 * dt
        if abs(self.open_amount - target) < 0.01:
            self.open_amount = target
    
    def draw(self, screen: pygame.Surface):
        if self.is_horizontal:
            if self.open_amount < 0.1:
                # Closed
                pygame.draw.rect(screen, BROWN, (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, DARK_BROWN, (self.x, self.y, self.width, self.height), 2)
                # Hinge
                hinge_x = self.x + 3 if self.hinge_left else self.x + self.width - 6
                pygame.draw.rect(screen, GRAY, (hinge_x, self.y, 3, self.height))
            else:
                # Opening animation
                angle = self.open_amount * (math.pi / 2.5)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                
                if self.hinge_left:
                    hinge_x, hinge_y = self.x, self.y + self.height/2
                    end_x = hinge_x + self.width * cos_a
                    end_y = hinge_y - self.width * sin_a * 0.5
                else:
                    hinge_x, hinge_y = self.x + self.width, self.y + self.height/2
                    end_x = hinge_x - self.width * cos_a
                    end_y = hinge_y - self.width * sin_a * 0.5
                
                pygame.draw.line(screen, BROWN, (hinge_x, hinge_y), (end_x, end_y), int(self.height))
                pygame.draw.circle(screen, GRAY, (int(hinge_x), int(hinge_y)), 4)
        else:
            if self.open_amount < 0.1:
                pygame.draw.rect(screen, BROWN, (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, DARK_BROWN, (self.x, self.y, self.width, self.height), 2)
                hinge_y = self.y + 3 if self.hinge_left else self.y + self.height - 6
                pygame.draw.rect(screen, GRAY, (self.x, hinge_y, self.width, 3))
            else:
                angle = self.open_amount * (math.pi / 2.5)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                
                if self.hinge_left:
                    hinge_x, hinge_y = self.x + self.width/2, self.y
                    end_x = hinge_x + self.height * sin_a * 0.5
                    end_y = hinge_y + self.height * cos_a
                else:
                    hinge_x, hinge_y = self.x + self.width/2, self.y + self.height
                    end_x = hinge_x + self.height * sin_a * 0.5
                    end_y = hinge_y - self.height * cos_a
                
                pygame.draw.line(screen, BROWN, (hinge_x, hinge_y), (end_x, end_y), int(self.width))
                pygame.draw.circle(screen, GRAY, (int(hinge_x), int(hinge_y)), 4)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hotline Miami - Basic")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.player = Player(200, 500)
        self.enemies: List[Enemy] = []
        self.walls: List[Wall] = []
        self.doors: List[Door] = []
        self.corpses: List[Corpse] = []
        
        self.create_map()
    
    def create_map(self):
        """Create a multi-room building layout with NO overlapping walls"""
        
        # Main building - large structure on the right
        # Outer walls
        main_x, main_y = 600, 100
        main_w, main_h = 600, 500
        
        # Outer walls (clockwise from top-left)
        self.walls.append(Wall(main_x, main_y, main_w, 20))  # Top
        self.walls.append(Wall(main_x, main_y + main_h - 20, main_w, 20))  # Bottom
        self.walls.append(Wall(main_x, main_y, 20, main_h))  # Left
        self.walls.append(Wall(main_x + main_w - 20, main_y, 20, main_h))  # Right
        
        # Internal room divisions
        # Vertical divider (left of center)
        self.walls.append(Wall(main_x + 200, main_y + 20, 20, 200))  # Top portion
        self.walls.append(Wall(main_x + 200, main_y + 320, 20, 180))  # Bottom portion
        # Door gap at y=320-340
        
        # Horizontal divider (middle)
        self.walls.append(Wall(main_x + 20, main_y + 250, 180, 20))  # Left portion
        self.walls.append(Wall(main_x + 220, main_y + 250, 380, 20))  # Right portion
        
        # Another vertical divider for back room
        self.walls.append(Wall(main_x + 400, main_y + 20, 20, 130))  # Top
        self.walls.append(Wall(main_x + 400, main_y + 270, 20, 230))  # Bottom
        
        # Small room in back right
        self.walls.append(Wall(main_x + 420, main_y + 150, 80, 20))  # Divider
        
        # Doors
        self.doors.append(Door(main_x + 200, main_y + 220, 20, 100, hinge_left=True))  # Vertical door
        self.doors.append(Door(main_x + 200, main_y + 270, 100, 20, hinge_left=True))  # Horizontal door
        self.doors.append(Door(main_x + 400, main_y + 150, 20, 120, hinge_left=False))  # Vertical door
        
        # Main entrance door (left side of building)
        self.doors.append(Door(main_x, main_y + 200, 20, 100, hinge_left=True))
        
        # Smaller building on the left
        small_x, small_y = 100, 150
        small_w, small_h = 300, 250
        
        self.walls.append(Wall(small_x, small_y, small_w, 20))
        self.walls.append(Wall(small_x, small_y + small_h - 20, small_w, 20))
        self.walls.append(Wall(small_x, small_y, 20, small_h))
        self.walls.append(Wall(small_x + small_w - 20, small_y, 20, small_h))
        
        # Internal divider in small building
        self.walls.append(Wall(small_x + 20, small_y + 120, 130, 20))
        self.walls.append(Wall(small_x + 200, small_y + 120, 80, 20))
        
        self.doors.append(Door(small_x + 150, small_y + 120, 50, 20, hinge_left=True))
        self.doors.append(Door(small_x + small_w - 20, small_y + 80, 20, 80, hinge_left=False))
        
        # Enemies in main building
        self.enemies.append(Enemy(main_x + 100, main_y + 100))
        self.enemies.append(Enemy(main_x + 300, main_y + 150))
        self.enemies.append(Enemy(main_x + 500, main_y + 350))
        self.enemies.append(Enemy(main_x + 100, main_y + 400))
        
        # Enemies in small building
        self.enemies.append(Enemy(small_x + 80, small_y + 60))
        self.enemies.append(Enemy(small_x + 220, small_y + 180))
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.player_punch()
    
    def player_punch(self):
        if self.player.punch():
            px, py = self.player.get_punch_hitbox()
            for enemy in self.enemies:
                if enemy.alive:
                    dx = enemy.x - px
                    dy = enemy.y - py
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < enemy.radius + 15:  # Hit radius
                        enemy.hp -= 1
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius))
    
    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        self.player.update(dt, keys, mouse_pos)
        self.player.move(dt, self.walls, self.doors)
        
        # Check door pushing
        for door in self.doors:
            if door.collides_with_circle(self.player.x, self.player.y, self.player.radius):
                door.push(self.player.x, self.player.y)
            door.update(dt)
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.walls, self.doors)
            enemy.move(dt, self.walls, self.doors)
            
            # Enemy attacks
            if enemy.can_punch(self.player):
                enemy.punch()
                self.player.hp -= 1
                if self.player.hp <= 0 and self.player.alive:
                    self.player.alive = False
                    self.corpses.append(Corpse(self.player.x, self.player.y, self.player.radius, True))
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw floor areas (visual only)
        pygame.draw.rect(self.screen, DARK_GRAY, (620, 120, 560, 460))  # Main building floor
        pygame.draw.rect(self.screen, DARK_GRAY, (120, 170, 260, 210))  # Small building floor
        
        # Draw doors
        for door in self.doors:
            door.draw(self.screen)
        
        # Draw walls
        for wall in self.walls:
            wall.draw(self.screen)
        
        # Draw corpses
        for corpse in self.corpses:
            corpse.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw UI
        font = pygame.font.SysFont(None, 24)
        hp_text = font.render(f"HP: {self.player.hp}/{PLAYER_HP}", True, WHITE)
        self.screen.blit(hp_text, (10, 10))
        
        enemy_count = sum(1 for e in self.enemies if e.alive)
        enemy_text = font.render(f"Enemies: {enemy_count}", True, WHITE)
        self.screen.blit(enemy_text, (10, 35))
        
        if not self.player.alive:
            over_font = pygame.font.SysFont(None, 72)
            over_text = over_font.render("GAME OVER", True, RED)
            rect = over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            self.screen.blit(over_text, rect)
        
        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
