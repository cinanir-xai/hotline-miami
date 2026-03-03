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

# World
WORLD_WIDTH = 2400
WORLD_HEIGHT = 1400

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
ENEMY_DETECTION_RANGE = 320
ENEMY_LOS_RANGE = 450

# Door interactions
DOOR_PUNCH_DAMAGE = 1
DOOR_PUNCH_RANGE = 60
DOOR_PUNCH_ANGLE = math.pi


def line_segments_intersect(p1: pygame.Vector2, p2: pygame.Vector2, q1: pygame.Vector2, q2: pygame.Vector2) -> bool:
    def ccw(a, b, c):
        return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)
    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))


def angle_difference(a: float, b: float) -> float:
    diff = (a - b + math.pi) % (2 * math.pi) - math.pi
    return diff


class Blood:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 8)
        self.color = random.choice([RED, DARK_RED])
        
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        pygame.draw.circle(screen, self.color, (int(self.x - offset.x), int(self.y - offset.y)), self.radius)


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
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        # Draw blood first (underneath)
        for blood in self.blood:
            blood.draw(screen, offset)
        # Draw corpse as flattened circle
        color = GREEN if self.is_player else RED
        pygame.draw.ellipse(screen, color, 
                          (int(self.x - self.radius - offset.x), int(self.y - self.radius/2 - offset.y),
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
        self.x = max(self.radius, min(WORLD_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(WORLD_HEIGHT - self.radius, self.y))


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
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        if not self.alive:
            return
        # Body
        pygame.draw.circle(screen, GREEN, (int(self.x - offset.x), int(self.y - offset.y)), self.radius)
        # Direction indicator
        end_x = self.x + math.cos(self.facing_angle) * (self.radius + 5)
        end_y = self.y + math.sin(self.facing_angle) * (self.radius + 5)
        pygame.draw.line(screen, DARK_GRAY, (self.x - offset.x, self.y - offset.y), (end_x - offset.x, end_y - offset.y), 3)
        # Punch indicator if on cooldown
        if self.punch_cooldown > PLAYER_PUNCH_COOLDOWN * 0.5:
            px, py = self.get_punch_hitbox()
            pygame.draw.circle(screen, YELLOW, (int(px - offset.x), int(py - offset.y)), 8)


class Enemy(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, ENEMY_RADIUS, ENEMY_SPEED, ENEMY_HP)
        self.punch_cooldown = 0.0
        self.wander_timer = 0.0
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        self.can_see_player = False
        
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
        
        self.can_see_player = False
        if dist < ENEMY_LOS_RANGE and player.alive:
            start = pygame.Vector2(self.x, self.y)
            end = pygame.Vector2(player.x, player.y)
            blocked = False
            for wall in walls:
                if wall.intersects_line(start, end):
                    blocked = True
                    break
            if not blocked:
                for door in doors:
                    if door.intersects_line(start, end):
                        blocked = True
                        break
            self.can_see_player = not blocked
        
        if dist < ENEMY_DETECTION_RANGE and player.alive and self.can_see_player:
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
        if not self.can_see_player:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist <= ENEMY_PUNCH_RANGE
    
    def punch(self):
        self.punch_cooldown = ENEMY_PUNCH_COOLDOWN
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        if not self.alive:
            return
        pygame.draw.circle(screen, RED, (int(self.x - offset.x), int(self.y - offset.y)), self.radius)
        # Health indicator
        hp_pct = self.hp / ENEMY_HP
        pygame.draw.rect(screen, BLACK, (int(self.x - 10 - offset.x), int(self.y - self.radius - 8 - offset.y), 20, 4))
        pygame.draw.rect(screen, GREEN if hp_pct > 0.5 else YELLOW if hp_pct > 0.25 else RED,
                        (int(self.x - 10 - offset.x), int(self.y - self.radius - 8 - offset.y), int(20 * hp_pct), 4))


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
    
    def intersects_line(self, start: pygame.Vector2, end: pygame.Vector2) -> bool:
        rect_lines = [
            (pygame.Vector2(self.x, self.y), pygame.Vector2(self.x + self.width, self.y)),
            (pygame.Vector2(self.x + self.width, self.y), pygame.Vector2(self.x + self.width, self.y + self.height)),
            (pygame.Vector2(self.x + self.width, self.y + self.height), pygame.Vector2(self.x, self.y + self.height)),
            (pygame.Vector2(self.x, self.y + self.height), pygame.Vector2(self.x, self.y)),
        ]
        for a, b in rect_lines:
            if line_segments_intersect(start, end, a, b):
                return True
        return self.rect.clipline((start.x, start.y), (end.x, end.y)) != ()
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        rect = pygame.Rect(self.rect.x - offset.x, self.rect.y - offset.y, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, WHITE, rect)
        pygame.draw.rect(screen, GRAY, rect, 2)


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
        self.open_speed = 5.0
        self.hit_cooldown = 0.0
        
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
    
    def intersects_line(self, start: pygame.Vector2, end: pygame.Vector2) -> bool:
        if self.is_open and self.open_amount > 0.8:
            return False
        door_rect = self.get_collision_rect()
        return door_rect.clipline((start.x, start.y), (end.x, end.y)) != ()
    
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
    
    def force_open(self):
        self.is_open = True
        self.open_speed = 18.0
        self.hit_cooldown = 0.15
    
    def update(self, dt: float):
        target = 1.0 if self.is_open else 0.0
        self.open_amount += (target - self.open_amount) * self.open_speed * dt
        if abs(self.open_amount - target) < 0.01:
            self.open_amount = target
        self.open_speed = max(5.0, self.open_speed - 10.0 * dt)
        if self.hit_cooldown > 0:
            self.hit_cooldown -= dt
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        if self.is_horizontal:
            if self.open_amount < 0.1:
                # Closed
                pygame.draw.rect(screen, BROWN, (self.x - offset.x, self.y - offset.y, self.width, self.height))
                pygame.draw.rect(screen, DARK_BROWN, (self.x - offset.x, self.y - offset.y, self.width, self.height), 2)
                # Hinge
                hinge_x = self.x + 3 if self.hinge_left else self.x + self.width - 6
                pygame.draw.rect(screen, GRAY, (hinge_x - offset.x, self.y - offset.y, 3, self.height))
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
                
                pygame.draw.line(screen, BROWN, (hinge_x - offset.x, hinge_y - offset.y), (end_x - offset.x, end_y - offset.y), int(self.height))
                pygame.draw.circle(screen, GRAY, (int(hinge_x - offset.x), int(hinge_y - offset.y)), 4)
        else:
            if self.open_amount < 0.1:
                pygame.draw.rect(screen, BROWN, (self.x - offset.x, self.y - offset.y, self.width, self.height))
                pygame.draw.rect(screen, DARK_BROWN, (self.x - offset.x, self.y - offset.y, self.width, self.height), 2)
                hinge_y = self.y + 3 if self.hinge_left else self.y + self.height - 6
                pygame.draw.rect(screen, GRAY, (self.x - offset.x, hinge_y - offset.y, self.width, 3))
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
                
                pygame.draw.line(screen, BROWN, (hinge_x - offset.x, hinge_y - offset.y), (end_x - offset.x, end_y - offset.y), int(self.width))
                pygame.draw.circle(screen, GRAY, (int(hinge_x - offset.x), int(hinge_y - offset.y)), 4)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hotline Miami - Basic")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.player = Player(300, 900)
        self.enemies: List[Enemy] = []
        self.walls: List[Wall] = []
        self.doors: List[Door] = []
        self.corpses: List[Corpse] = []
        self.camera_offset = pygame.Vector2(0, 0)
        
        self.create_map()
    
    def create_map(self):
        """Create a multi-room building layout with NO overlapping walls"""
        
        # Main building - large structure on the right (twice size)
        main_x, main_y = 1000, 200
        main_w, main_h = 1200, 1000
        
        # Outer walls (clockwise from top-left)
        self.walls.append(Wall(main_x, main_y, main_w, 24))  # Top
        self.walls.append(Wall(main_x, main_y + main_h - 24, main_w, 24))  # Bottom
        self.walls.append(Wall(main_x, main_y, 24, main_h))  # Left
        self.walls.append(Wall(main_x + main_w - 24, main_y, 24, main_h))  # Right
        
        # External doors for main building (multiple entrances)
        self.doors.append(Door(main_x + 300, main_y, 120, 24, hinge_left=True))  # Top entrance
        self.doors.append(Door(main_x + 700, main_y + main_h - 24, 120, 24, hinge_left=False))  # Bottom entrance
        self.doors.append(Door(main_x, main_y + 300, 24, 140, hinge_left=True))  # Left entrance
        self.doors.append(Door(main_x + main_w - 24, main_y + 600, 24, 140, hinge_left=False))  # Right entrance
        
        # Internal room divisions
        # Vertical divider (left of center)
        self.walls.append(Wall(main_x + 300, main_y + 24, 24, 300))  # Top portion
        self.walls.append(Wall(main_x + 300, main_y + 500, 24, 476))  # Bottom portion
        # Door gap between 324-500
        
        # Horizontal divider (middle)
        self.walls.append(Wall(main_x + 24, main_y + 420, 276, 24))  # Left portion
        self.walls.append(Wall(main_x + 324, main_y + 420, 852, 24))  # Right portion
        
        # Vertical divider for back rooms
        self.walls.append(Wall(main_x + 700, main_y + 24, 24, 250))
        self.walls.append(Wall(main_x + 700, main_y + 520, 24, 456))
        
        # Small room in back right
        self.walls.append(Wall(main_x + 724, main_y + 300, 200, 24))
        
        # Internal doors for main building (multiple connectors)
        self.doors.append(Door(main_x + 300, main_y + 324, 24, 176, hinge_left=True))
        self.doors.append(Door(main_x + 300, main_y + 420, 140, 24, hinge_left=True))
        self.doors.append(Door(main_x + 700, main_y + 300, 24, 220, hinge_left=False))
        self.doors.append(Door(main_x + 724, main_y + 300, 120, 24, hinge_left=True))
        self.doors.append(Door(main_x + 500, main_y + 420, 120, 24, hinge_left=False))
        self.doors.append(Door(main_x + 900, main_y + 420, 120, 24, hinge_left=True))
        
        # Smaller building on the left (twice size)
        small_x, small_y = 150, 250
        small_w, small_h = 600, 500
        
        self.walls.append(Wall(small_x, small_y, small_w, 24))
        self.walls.append(Wall(small_x, small_y + small_h - 24, small_w, 24))
        self.walls.append(Wall(small_x, small_y, 24, small_h))
        self.walls.append(Wall(small_x + small_w - 24, small_y, 24, small_h))
        
        # External doors for small building
        self.doors.append(Door(small_x + 200, small_y, 100, 24, hinge_left=True))
        self.doors.append(Door(small_x + small_w - 24, small_y + 140, 24, 120, hinge_left=False))
        self.doors.append(Door(small_x + 120, small_y + small_h - 24, 100, 24, hinge_left=False))
        
        # Internal divider in small building
        self.walls.append(Wall(small_x + 24, small_y + 240, 250, 24))
        self.walls.append(Wall(small_x + 350, small_y + 240, 226, 24))
        
        # Internal doors in small building
        self.doors.append(Door(small_x + 274, small_y + 240, 76, 24, hinge_left=True))
        self.doors.append(Door(small_x + 24, small_y + 140, 24, 100, hinge_left=True))
        self.doors.append(Door(small_x + small_w - 24, small_y + 320, 24, 100, hinge_left=False))
        
        # Enemies in main building
        for pos in [
            (main_x + 120, main_y + 120), (main_x + 420, main_y + 140),
            (main_x + 680, main_y + 200), (main_x + 980, main_y + 200),
            (main_x + 300, main_y + 700), (main_x + 520, main_y + 800),
            (main_x + 840, main_y + 700), (main_x + 1050, main_y + 520),
            (main_x + 200, main_y + 900), (main_x + 900, main_y + 900),
        ]:
            self.enemies.append(Enemy(*pos))
        
        # Enemies in small building
        for pos in [
            (small_x + 120, small_y + 120), (small_x + 400, small_y + 120),
            (small_x + 200, small_y + 360), (small_x + 460, small_y + 380),
        ]:
            self.enemies.append(Enemy(*pos))
        
        # Enemies outside
        for pos in [
            (700, 900), (900, 1050), (600, 450), (800, 300)
        ]:
            self.enemies.append(Enemy(*pos))
    
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
            punch_angle = self.player.facing_angle
            
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
            
            # Door punch (violent open + damage cone)
            for door in self.doors:
                if door.is_open:
                    continue
                door_center = pygame.Vector2(door.x + door.width / 2, door.y + door.height / 2)
                to_door = door_center - pygame.Vector2(self.player.x, self.player.y)
                if to_door.length() > DOOR_PUNCH_RANGE:
                    continue
                door_angle = math.atan2(to_door.y, to_door.x)
                if abs(angle_difference(door_angle, punch_angle)) > DOOR_PUNCH_ANGLE / 2:
                    continue
                door.force_open()
                
                # Apply damage to entities near door within 180-degree swing
                for target in [self.player] + [e for e in self.enemies if e.alive]:
                    if not target.alive:
                        continue
                    vec = pygame.Vector2(target.x, target.y) - door_center
                    if vec.length() > DOOR_PUNCH_RANGE:
                        continue
                    target_angle = math.atan2(vec.y, vec.x)
                    if abs(angle_difference(target_angle, door_angle)) <= DOOR_PUNCH_ANGLE / 2:
                        target.hp -= DOOR_PUNCH_DAMAGE
                        if target.hp <= 0 and target.alive:
                            target.alive = False
                            is_player = isinstance(target, Player)
                            self.corpses.append(Corpse(target.x, target.y, target.radius, is_player))
                break
    
    def update(self, dt: float):
        keys = pygame.key.get_pressed()
        self.camera_offset.x = max(0, min(self.player.x - SCREEN_WIDTH / 2, WORLD_WIDTH - SCREEN_WIDTH))
        self.camera_offset.y = max(0, min(self.player.y - SCREEN_HEIGHT / 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        mouse_pos = pygame.mouse.get_pos()
        world_mouse = (mouse_pos[0] + self.camera_offset.x, mouse_pos[1] + self.camera_offset.y)
        
        self.player.update(dt, keys, world_mouse)
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
        
        self.camera_offset.x = max(0, min(self.player.x - SCREEN_WIDTH / 2, WORLD_WIDTH - SCREEN_WIDTH))
        self.camera_offset.y = max(0, min(self.player.y - SCREEN_HEIGHT / 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        
        # Draw floor areas (visual only)
        pygame.draw.rect(self.screen, DARK_GRAY, (1000 - self.camera_offset.x + 24, 200 - self.camera_offset.y + 24, 1200 - 48, 1000 - 48))
        pygame.draw.rect(self.screen, DARK_GRAY, (150 - self.camera_offset.x + 24, 250 - self.camera_offset.y + 24, 600 - 48, 500 - 48))
        
        # Draw doors
        for door in self.doors:
            door.draw(self.screen, self.camera_offset)
        
        # Draw walls
        for wall in self.walls:
            wall.draw(self.screen, self.camera_offset)
        
        # Draw corpses
        for corpse in self.corpses:
            corpse.draw(self.screen, self.camera_offset)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_offset)
        
        # Draw player
        self.player.draw(self.screen, self.camera_offset)
        
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
