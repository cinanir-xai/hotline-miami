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
LIGHT_GRAY = (140, 140, 140)
RED = (200, 50, 50)
DARK_RED = (150, 30, 30)
ORANGE = (230, 140, 40)
DARK_ORANGE = (180, 100, 30)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (255, 255, 0)
BROWN = (139, 90, 43)
DARK_BROWN = (100, 60, 30)
DIRT_BROWN = (101, 67, 33)
DIRT_LIGHT = (120, 80, 45)
DIRT_DARK = (80, 50, 25)

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
PLAYER_BAT_COOLDOWN = 0.75

# Weapons
BAT_DAMAGE = 2
BAT_ARC = math.pi
BAT_RANGE = 85
BAT_DURABILITY = 5
BAT_THROW_CHARGE = 1.5
BAT_THROW_SPEED = 520
BAT_GROUND_SCALE = 1.4
BAT_SWING_ARC = math.pi * 0.9
BAT_SWING_LENGTH = 32
BAT_SWING_WIDTH = 6
BAT_PROJECTILE_SPIN = 10.0
BAT_PROJECTILE_LIFE = 1.6
BAT_IMPACT_FLASH = 0.18
BAT_PICKUP_RANGE = 22
BAT_SPAWN_CHANCE = 0.25

# Enemy
ENEMY_RADIUS = 14
ENEMY_SPEED = 130
ENEMY_HP = 3
ENEMY_PUNCH_RANGE = 45
ENEMY_PUNCH_COOLDOWN = 3.0
ENEMY_PUNCH_WINDUP = 2.0
ENEMY_BAT_COOLDOWN = 5.0
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


def draw_bat_sprite(screen: pygame.Surface, center: pygame.Vector2, angle: float, offset: pygame.Vector2, scale: float = 1.0):
    """Draw a cleaner bat sprite using a shaft + barrel + grip."""
    length = 28 * scale
    barrel = 10 * scale
    grip = 6 * scale
    thickness = 6 * scale

    direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    perp = pygame.Vector2(-direction.y, direction.x)

    shaft_start = center - direction * (length * 0.6)
    shaft_end = center + direction * (length * 0.3)

    # Shaft
    shaft_points = [
        (shaft_start + perp * (thickness * 0.35)),
        (shaft_start - perp * (thickness * 0.35)),
        (shaft_end - perp * (thickness * 0.35)),
        (shaft_end + perp * (thickness * 0.35)),
    ]
    pygame.draw.polygon(screen, BROWN, [(p.x - offset.x, p.y - offset.y) for p in shaft_points])

    # Barrel
    barrel_center = center + direction * (length * 0.55)
    barrel_radius = barrel * 0.55
    pygame.draw.circle(screen, DARK_BROWN, (int(barrel_center.x - offset.x), int(barrel_center.y - offset.y)), int(barrel_radius))

    # Grip
    grip_center = center - direction * (length * 0.75)
    pygame.draw.circle(screen, DARK_BROWN, (int(grip_center.x - offset.x), int(grip_center.y - offset.y)), int(grip * 0.4))


class Blood:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 8)
        self.color = random.choice([RED, DARK_RED, DARK_ORANGE])
        
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
        color = GREEN if self.is_player else ORANGE
        pygame.draw.ellipse(screen, color, 
                          (int(self.x - self.radius - offset.x), int(self.y - self.radius/2 - offset.y),
                           int(self.radius * 2), int(self.radius)))


class BatItem:
    def __init__(self, x: float, y: float, durability: int = BAT_DURABILITY):
        self.x = x
        self.y = y
        self.durability = durability
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        draw_bat_sprite(screen, pygame.Vector2(self.x, self.y), 0.35, offset, scale=BAT_GROUND_SCALE)


class BatProjectile:
    def __init__(self, x: float, y: float, velocity: pygame.Vector2, durability: int):
        self.x = x
        self.y = y
        self.velocity = velocity
        self.durability = durability
        self.alive = True
        self.life = BAT_PROJECTILE_LIFE
        self.spin = 0.0
    
    def update(self, dt: float):
        if not self.alive:
            return
        self.x += self.velocity.x * dt
        self.y += self.velocity.y * dt
        self.spin += BAT_PROJECTILE_SPIN * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        draw_bat_sprite(screen, pygame.Vector2(self.x, self.y), self.spin, offset, scale=1.0)


class BatBreakPiece:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.offset = pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
        self.life = 1.0
    
    def update(self, dt: float):
        self.life -= dt
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        if self.life <= 0:
            return
        start = (self.x - offset.x, self.y - offset.y)
        end = (self.x + self.offset.x - offset.x, self.y + self.offset.y - offset.y)
        pygame.draw.line(screen, DARK_BROWN, start, end, 3)


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
        self.attack_timer = 0.0
        self.attack_side = 1
        self.attack_offset = pygame.Vector2(0, 0)
        self.attack_radius = 0
        self.attack_angle = 0.0
        
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
        
        # Attack animation timer
        if self.attack_timer > 0:
            self.attack_timer -= dt
        
        # Cooldown
        if self.punch_cooldown > 0:
            self.punch_cooldown -= dt
    
    def punch(self, has_bat: bool = False) -> bool:
        if not self.alive or self.punch_cooldown > 0:
            return False
        self.punch_cooldown = PLAYER_BAT_COOLDOWN if has_bat else PLAYER_PUNCH_COOLDOWN
        self.attack_timer = 0.2
        self.attack_radius = 8 if not has_bat else 10
        side = self.attack_side
        self.attack_side *= -1
        self.attack_angle = self.facing_angle + side * 0.7
        self.attack_offset = pygame.Vector2(math.cos(self.attack_angle), math.sin(self.attack_angle)) * (self.radius + 10)
        return True
    
    def get_punch_hitbox(self) -> tuple:
        """Returns (x, y) of punch position"""
        px = self.x + math.cos(self.facing_angle) * PLAYER_PUNCH_RANGE
        py = self.y + math.sin(self.facing_angle) * PLAYER_PUNCH_RANGE
        return (px, py)
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2, has_bat: bool):
        if not self.alive:
            return
        # Body
        pygame.draw.circle(screen, GREEN, (int(self.x - offset.x), int(self.y - offset.y)), self.radius)
        # Direction indicator
        end_x = self.x + math.cos(self.facing_angle) * (self.radius + 5)
        end_y = self.y + math.sin(self.facing_angle) * (self.radius + 5)
        pygame.draw.line(screen, DARK_GRAY, (self.x - offset.x, self.y - offset.y), (end_x - offset.x, end_y - offset.y), 3)
        
        # Attack animation
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            anim_pos = pygame.Vector2(self.x, self.y) + self.attack_offset * progress
            if not has_bat:
                pygame.draw.circle(screen, GREEN, (int(anim_pos.x - offset.x), int(anim_pos.y - offset.y)), self.attack_radius)
            else:
                swing_angle = self.attack_angle + (progress - 0.5) * BAT_SWING_ARC
                draw_bat_sprite(screen, anim_pos, swing_angle, offset, scale=1.1)
        if has_bat:
            hand_pos = pygame.Vector2(self.x, self.y) + pygame.Vector2(math.cos(self.facing_angle), math.sin(self.facing_angle)) * (self.radius + 6)
            draw_bat_sprite(screen, hand_pos, self.facing_angle, offset, scale=0.8)


class Enemy(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, ENEMY_RADIUS, ENEMY_SPEED, ENEMY_HP)
        self.punch_cooldown = 0.0
        self.in_range_timer = 0.0
        self.wander_timer = 0.0
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        self.can_see_player = False
        self.has_bat = False
        self.bat_durability = BAT_DURABILITY
        
    def update(self, dt: float, player: Player, walls: List['Wall'], doors: List['Door']):
        if not self.alive:
            return
            
        # Attack animation timer
        if self.attack_timer > 0:
            self.attack_timer -= dt
            
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
        
        # Track time in range
        attack_range = BAT_RANGE if self.has_bat else ENEMY_PUNCH_RANGE
        if dist <= attack_range and self.can_see_player:
            self.in_range_timer += dt
        else:
            self.in_range_timer = 0.0
    
    def can_punch(self, player: Player) -> bool:
        if not self.alive or not player.alive or self.punch_cooldown > 0:
            return False
        if not self.can_see_player:
            return False
        if self.in_range_timer < ENEMY_PUNCH_WINDUP:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist <= (BAT_RANGE if self.has_bat else ENEMY_PUNCH_RANGE)
    
    def punch(self, facing_angle: float):
        self.punch_cooldown = ENEMY_BAT_COOLDOWN if self.has_bat else ENEMY_PUNCH_COOLDOWN
        self.attack_timer = 0.2
        self.attack_radius = 8 if not self.has_bat else 10
        side = self.attack_side
        self.attack_side *= -1
        self.attack_angle = facing_angle + side * 0.7
        self.attack_offset = pygame.Vector2(math.cos(self.attack_angle), math.sin(self.attack_angle)) * (self.radius + 10)
    
    def draw(self, screen: pygame.Surface, offset: pygame.Vector2):
        if not self.alive:
            return
        pygame.draw.circle(screen, ORANGE, (int(self.x - offset.x), int(self.y - offset.y)), self.radius)
        # Attack animation
        if self.attack_timer > 0:
            progress = 1.0 - (self.attack_timer / 0.2)
            anim_pos = pygame.Vector2(self.x, self.y) + self.attack_offset * progress
            if not self.has_bat:
                pygame.draw.circle(screen, ORANGE, (int(anim_pos.x - offset.x), int(anim_pos.y - offset.y)), self.attack_radius)
            else:
                swing_angle = self.attack_angle + (progress - 0.5) * BAT_SWING_ARC
                draw_bat_sprite(screen, anim_pos, swing_angle, offset, scale=1.0)
        if self.has_bat:
            hand_pos = pygame.Vector2(self.x, self.y) + pygame.Vector2(math.cos(self.attack_angle), math.sin(self.attack_angle)) * (self.radius + 6)
            draw_bat_sprite(screen, hand_pos, self.attack_angle, offset, scale=0.7)
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
        self.bat_items: List[BatItem] = []
        self.bat_projectiles: List[BatProjectile] = []
        self.bat_breaks: List[BatBreakPiece] = []
        self.player_has_bat = False
        self.player_bat_durability = BAT_DURABILITY
        self.throw_charge = 0.0
        self.throw_charging = False
        self.camera_offset = pygame.Vector2(0, 0)
        self.impact_flashes: List[float] = []
        
        self.create_map()
    
    def create_map(self):
        """Create a multi-room building layout with NO overlapping walls"""
        
        # Main building - large structure on the right (twice size)
        main_x, main_y = 1000, 200
        main_w, main_h = 1200, 1000
        
        # Exterior doors for main building - positions (gap start, door width)
        door_n = (main_x + 540, 120)   # North (top)
        door_s = (main_x + 540, 120)   # South (bottom)
        door_w = (main_y + 430, 140)   # West (left) - y position
        door_e = (main_y + 430, 140)   # East (right) - y position
        
        # Top wall with gap for North door
        self.walls.append(Wall(main_x, main_y, door_n[0] - main_x, 24))  # Left of door
        self.walls.append(Wall(door_n[0] + door_n[1], main_y, main_w - (door_n[0] - main_x) - door_n[1], 24))  # Right of door
        self.doors.append(Door(door_n[0], main_y, door_n[1], 24, hinge_left=True))  # North door
        
        # Bottom wall with gap for South door
        self.walls.append(Wall(main_x, main_y + main_h - 24, door_s[0] - main_x, 24))
        self.walls.append(Wall(door_s[0] + door_s[1], main_y + main_h - 24, main_w - (door_s[0] - main_x) - door_s[1], 24))
        self.doors.append(Door(door_s[0], main_y + main_h - 24, door_s[1], 24, hinge_left=False))  # South door
        
        # Left wall with gap for West door
        self.walls.append(Wall(main_x, main_y, 24, door_w[0] - main_y))
        self.walls.append(Wall(main_x, door_w[0] + door_w[1], 24, main_h - (door_w[0] - main_y) - door_w[1]))
        self.doors.append(Door(main_x, door_w[0], 24, door_w[1], hinge_left=True))  # West door
        
        # Right wall with gap for East door
        self.walls.append(Wall(main_x + main_w - 24, main_y, 24, door_e[0] - main_y))
        self.walls.append(Wall(main_x + main_w - 24, door_e[0] + door_e[1], 24, main_h - (door_e[0] - main_y) - door_e[1]))
        self.doors.append(Door(main_x + main_w - 24, door_e[0], 24, door_e[1], hinge_left=False))  # East door
        
        # Store building bounds for floor rendering
        self.main_building = (main_x, main_y, main_w, main_h)
        
        # Internal room divisions
        # Vertical divider (left of center) with door gap
        self.walls.append(Wall(main_x + 300, main_y + 24, 24, 300))  # Top portion
        self.walls.append(Wall(main_x + 300, main_y + 500, 24, 476))  # Bottom portion
        self.doors.append(Door(main_x + 300, main_y + 324, 24, 176, hinge_left=True))
        
        # Horizontal divider (middle) with door gap
        self.walls.append(Wall(main_x + 24, main_y + 420, 276, 24))  # Left portion
        self.walls.append(Wall(main_x + 324, main_y + 420, 852, 24))  # Right portion
        self.doors.append(Door(main_x + 300, main_y + 420, 140, 24, hinge_left=True))
        
        # Vertical divider for back rooms with door gap
        self.walls.append(Wall(main_x + 700, main_y + 24, 24, 250))
        self.walls.append(Wall(main_x + 700, main_y + 520, 24, 456))
        self.doors.append(Door(main_x + 700, main_y + 300, 24, 220, hinge_left=False))
        
        # Small room in back right
        self.walls.append(Wall(main_x + 724, main_y + 300, 200, 24))
        self.doors.append(Door(main_x + 724, main_y + 300, 120, 24, hinge_left=True))
        
        # Additional internal doors
        self.doors.append(Door(main_x + 500, main_y + 420, 120, 24, hinge_left=False))
        self.doors.append(Door(main_x + 900, main_y + 420, 120, 24, hinge_left=True))
        
        # Smaller building on the left (twice size)
        small_x, small_y = 150, 250
        small_w, small_h = 600, 500
        
        # Exterior doors for small building
        s_door_n = (small_x + 250, 100)   # North
        s_door_s = (small_x + 250, 100)   # South
        s_door_w = (small_y + 200, 100)   # West - y position
        s_door_e = (small_y + 200, 100)   # East - y position
        
        # Top wall with gap
        self.walls.append(Wall(small_x, small_y, s_door_n[0] - small_x, 24))
        self.walls.append(Wall(s_door_n[0] + s_door_n[1], small_y, small_w - (s_door_n[0] - small_x) - s_door_n[1], 24))
        self.doors.append(Door(s_door_n[0], small_y, s_door_n[1], 24, hinge_left=True))
        
        # Bottom wall with gap
        self.walls.append(Wall(small_x, small_y + small_h - 24, s_door_s[0] - small_x, 24))
        self.walls.append(Wall(s_door_s[0] + s_door_s[1], small_y + small_h - 24, small_w - (s_door_s[0] - small_x) - s_door_s[1], 24))
        self.doors.append(Door(s_door_s[0], small_y + small_h - 24, s_door_s[1], 24, hinge_left=False))
        
        # Left wall with gap
        self.walls.append(Wall(small_x, small_y, 24, s_door_w[0] - small_y))
        self.walls.append(Wall(small_x, s_door_w[0] + s_door_w[1], 24, small_h - (s_door_w[0] - small_y) - s_door_w[1]))
        self.doors.append(Door(small_x, s_door_w[0], 24, s_door_w[1], hinge_left=True))
        
        # Right wall with gap
        self.walls.append(Wall(small_x + small_w - 24, small_y, 24, s_door_e[0] - small_y))
        self.walls.append(Wall(small_x + small_w - 24, s_door_e[0] + s_door_e[1], 24, small_h - (s_door_e[0] - small_y) - s_door_e[1]))
        self.doors.append(Door(small_x + small_w - 24, s_door_e[0], 24, s_door_e[1], hinge_left=False))
        
        # Store building bounds
        self.small_building = (small_x, small_y, small_w, small_h)
        
        # Internal divider in small building with door gap
        self.walls.append(Wall(small_x + 24, small_y + 240, 250, 24))
        self.walls.append(Wall(small_x + 350, small_y + 240, 226, 24))
        self.doors.append(Door(small_x + 274, small_y + 240, 76, 24, hinge_left=True))
        
        # Enemies in main building
        for pos in [
            (main_x + 120, main_y + 120), (main_x + 420, main_y + 140),
            (main_x + 680, main_y + 200), (main_x + 980, main_y + 200),
            (main_x + 300, main_y + 700), (main_x + 520, main_y + 800),
            (main_x + 840, main_y + 700), (main_x + 1050, main_y + 520),
            (main_x + 200, main_y + 900), (main_x + 900, main_y + 900),
        ]:
            enemy = Enemy(*pos)
            if random.random() < BAT_SPAWN_CHANCE:
                enemy.has_bat = True
                enemy.bat_durability = BAT_DURABILITY
            self.enemies.append(enemy)
        
        # Enemies in small building
        for pos in [
            (small_x + 120, small_y + 120), (small_x + 400, small_y + 120),
            (small_x + 200, small_y + 360), (small_x + 460, small_y + 380),
        ]:
            enemy = Enemy(*pos)
            if random.random() < BAT_SPAWN_CHANCE:
                enemy.has_bat = True
                enemy.bat_durability = BAT_DURABILITY
            self.enemies.append(enemy)
        
        # Enemies outside
        for pos in [
            (700, 900), (900, 1050), (600, 450), (800, 300)
        ]:
            enemy = Enemy(*pos)
            if random.random() < BAT_SPAWN_CHANCE:
                enemy.has_bat = True
                enemy.bat_durability = BAT_DURABILITY
            self.enemies.append(enemy)
    
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
                elif event.button == 3:  # Right click
                    if self.player_has_bat:
                        self.throw_charging = True
                        self.throw_charge = 0.0
                    else:
                        self.try_pickup_bat()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    if self.throw_charging:
                        self.throw_charging = False
                        if self.throw_charge >= BAT_THROW_CHARGE and self.player_has_bat:
                            self.throw_bat()
                        else:
                            self.try_pickup_bat()
    
    def player_punch(self):
        if self.player.punch(self.player_has_bat):
            px, py = self.player.get_punch_hitbox()
            punch_angle = self.player.facing_angle
            
            is_bat = self.player_has_bat
            if is_bat:
                self.apply_bat_attack(self.player.x, self.player.y, punch_angle, source_is_player=True)
                # Bat attacks open doors without durability loss
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
                    break
                return
            
            for enemy in self.enemies:
                if enemy.alive:
                    dx = enemy.x - px
                    dy = enemy.y - py
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < enemy.radius + 15:  # Hit radius
                        enemy.hp -= 1
                        self.impact_flashes.append(BAT_IMPACT_FLASH)
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius))
                            if enemy.has_bat:
                                self.bat_items.append(BatItem(enemy.x, enemy.y, enemy.bat_durability))
                                enemy.has_bat = False
            
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
        
        # Bat throw charging
        if self.throw_charging:
            self.throw_charge += dt
        
        # Update projectiles
        for projectile in list(self.bat_projectiles):
            projectile.update(dt)
            if not projectile.alive:
                if projectile.durability > 0:
                    self.bat_items.append(BatItem(projectile.x, projectile.y, projectile.durability))
                else:
                    self.spawn_bat_break(projectile.x, projectile.y)
                self.bat_projectiles.remove(projectile)
                continue
            # Check projectile collision with enemies
            for enemy in self.enemies:
                if enemy.alive:
                    dist = math.hypot(enemy.x - projectile.x, enemy.y - projectile.y)
                    if dist <= enemy.radius + 8:
                        enemy.hp -= BAT_DAMAGE
                        self.impact_flashes.append(BAT_IMPACT_FLASH)
                        projectile.durability -= 1
                        projectile.alive = False
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.corpses.append(Corpse(enemy.x, enemy.y, enemy.radius))
                            if enemy.has_bat:
                                self.bat_items.append(BatItem(enemy.x, enemy.y, enemy.bat_durability))
                                enemy.has_bat = False
                        if projectile.durability <= 0:
                            self.spawn_bat_break(projectile.x, projectile.y)
                        break
        
        # Update bat break pieces
        for piece in list(self.bat_breaks):
            piece.update(dt)
            if piece.life <= 0:
                self.bat_breaks.remove(piece)
        
        # Update impact flashes
        for i in range(len(self.impact_flashes)):
            self.impact_flashes[i] -= dt
        self.impact_flashes = [t for t in self.impact_flashes if t > 0]
        
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
                facing = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                enemy.punch(facing)
                if enemy.has_bat:
                    self.apply_bat_attack(enemy.x, enemy.y, facing, source_is_player=False, attacker=enemy)
                else:
                    self.player.hp -= 1
                    self.impact_flashes.append(BAT_IMPACT_FLASH)
                if self.player.hp <= 0 and self.player.alive:
                    self.player.alive = False
                    self.corpses.append(Corpse(self.player.x, self.player.y, self.player.radius, True))
            
            if not enemy.alive and enemy.has_bat:
                self.bat_items.append(BatItem(enemy.x, enemy.y, enemy.bat_durability))
                enemy.has_bat = False
    
    def try_pickup_bat(self):
        if self.player_has_bat:
            return
        for bat in list(self.bat_items):
            dist = math.hypot(bat.x - self.player.x, bat.y - self.player.y)
            if dist <= BAT_PICKUP_RANGE:
                self.player_has_bat = True
                self.player_bat_durability = bat.durability
                self.bat_items.remove(bat)
                return
    
    def throw_bat(self):
        if not self.player_has_bat:
            return
        direction = pygame.Vector2(math.cos(self.player.facing_angle), math.sin(self.player.facing_angle))
        velocity = direction * BAT_THROW_SPEED
        projectile = BatProjectile(self.player.x, self.player.y, velocity, self.player_bat_durability)
        self.bat_projectiles.append(projectile)
        self.player_has_bat = False
        self.player_bat_durability = BAT_DURABILITY
    
    def spawn_bat_break(self, x: float, y: float):
        for _ in range(3):
            self.bat_breaks.append(BatBreakPiece(x, y))
    
    def apply_bat_attack(self, attacker_x: float, attacker_y: float, facing_angle: float, source_is_player: bool, attacker: Optional[Enemy] = None):
        targets = [self.player] + [e for e in self.enemies if e.alive]
        hit_any = False
        for target in targets:
            if not target.alive:
                continue
            if source_is_player and target is self.player:
                continue
            vec = pygame.Vector2(target.x - attacker_x, target.y - attacker_y)
            if vec.length() > BAT_RANGE:
                continue
            target_angle = math.atan2(vec.y, vec.x)
            if abs(angle_difference(target_angle, facing_angle)) <= BAT_ARC / 2:
                target.hp -= BAT_DAMAGE
                hit_any = True
                if target.hp <= 0:
                    target.alive = False
                    is_player = isinstance(target, Player)
                    self.corpses.append(Corpse(target.x, target.y, target.radius, is_player))
                    if isinstance(target, Enemy) and target.has_bat:
                        self.bat_items.append(BatItem(target.x, target.y, target.bat_durability))
        if hit_any:
            self.impact_flashes.append(BAT_IMPACT_FLASH)
        if source_is_player and self.player_has_bat and hit_any:
            self.player_bat_durability -= 1
            if self.player_bat_durability <= 0:
                self.player_has_bat = False
                self.spawn_bat_break(attacker_x, attacker_y)
        elif not source_is_player and attacker and hit_any:
            attacker.bat_durability -= 1
            if attacker.bat_durability <= 0:
                attacker.has_bat = False
                self.spawn_bat_break(attacker_x, attacker_y)

    def draw(self):
        self.screen.fill(BLACK)
        
        self.camera_offset.x = max(0, min(self.player.x - SCREEN_WIDTH / 2, WORLD_WIDTH - SCREEN_WIDTH))
        self.camera_offset.y = max(0, min(self.player.y - SCREEN_HEIGHT / 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        
        # Draw dirt ground with texture detail
        self.draw_dirt_ground()
        
        # Draw building floors (plank floors)
        self.draw_building_floors()
        
        # Draw bat items and projectiles
        for bat in self.bat_items:
            bat.draw(self.screen, self.camera_offset)
        for projectile in self.bat_projectiles:
            projectile.draw(self.screen, self.camera_offset)
        for piece in self.bat_breaks:
            piece.draw(self.screen, self.camera_offset)
        
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
        self.player.draw(self.screen, self.camera_offset, self.player_has_bat)
        
        # Draw UI
        font = pygame.font.SysFont(None, 24)
        hp_text = font.render(f"HP: {self.player.hp}/{PLAYER_HP}", True, WHITE)
        self.screen.blit(hp_text, (10, 10))
        
        enemy_count = sum(1 for e in self.enemies if e.alive)
        enemy_text = font.render(f"Enemies: {enemy_count}", True, WHITE)
        self.screen.blit(enemy_text, (10, 35))
        
        if self.player_has_bat:
            bat_text = font.render(f"Bat Durability: {self.player_bat_durability}", True, WHITE)
            self.screen.blit(bat_text, (10, 60))
        elif self.throw_charging:
            charge_text = font.render("Charging throw...", True, WHITE)
            self.screen.blit(charge_text, (10, 60))
        
        if not self.player.alive:
            over_font = pygame.font.SysFont(None, 72)
            over_text = over_font.render("GAME OVER", True, RED)
            rect = over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            self.screen.blit(over_text, rect)
        
        # Impact flash feedback
        if self.impact_flashes:
            intensity = min(180, int(255 * max(self.impact_flashes)))
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, intensity))
            self.screen.blit(flash, (0, 0))
        
        pygame.display.flip()
    
    def draw_dirt_ground(self):
        """Draw textured dirt ground outside buildings"""
        cx, cy = self.camera_offset.x, self.camera_offset.y
        
        # Base dirt color
        dirt_rect = pygame.Rect(-cx, -cy, WORLD_WIDTH, WORLD_HEIGHT)
        pygame.draw.rect(self.screen, DIRT_BROWN, dirt_rect)
        
        # Draw dirt patches and texture
        seed = 42
        random.seed(seed)
        for _ in range(400):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            size = random.randint(3, 12)
            color = random.choice([DIRT_LIGHT, DIRT_DARK])
            pygame.draw.circle(self.screen, color, (int(x - cx), int(y - cy)), size)
        
        # Draw small pebbles/stones
        for _ in range(150):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            size = random.randint(2, 4)
            pygame.draw.circle(self.screen, (90, 85, 80), (int(x - cx), int(y - cy)), size)
        
        # Draw some grass tufts
        for _ in range(80):
            x = random.randint(0, WORLD_WIDTH)
            y = random.randint(0, WORLD_HEIGHT)
            color = (60, 80, 40)
            for i in range(3):
                ox = random.randint(-5, 5)
                oy = random.randint(-5, 5)
                pygame.draw.line(self.screen, color, (x - cx, y - cy), (x + ox - cx, y + oy - cy), 2)
        
        random.seed()
    
    def draw_building_floors(self):
        """Draw gray plank floor inside buildings"""
        cx, cy = self.camera_offset.x, self.camera_offset.y
        
        # Main building floor
        mx, my, mw, mh = self.main_building
        floor_rect = pygame.Rect(mx + 24 - cx, my + 24 - cy, mw - 48, mh - 48)
        pygame.draw.rect(self.screen, DARK_GRAY, floor_rect)
        
        # Draw planks (horizontal lines)
        plank_spacing = 20
        for y in range(my + 24, my + mh - 24, plank_spacing):
            pygame.draw.line(self.screen, GRAY, (mx + 24 - cx, y - cy), (mx + mw - 24 - cx, y - cy), 1)
        
        # Draw vertical plank dividers
        for x in range(mx + 24, mx + mw - 24, 80):
            pygame.draw.line(self.screen, LIGHT_GRAY, (x - cx, my + 24 - cy), (x - cx, my + mh - 24 - cy), 2)
        
        # Small building floor
        sx, sy, sw, sh = self.small_building
        floor_rect2 = pygame.Rect(sx + 24 - cx, sy + 24 - cy, sw - 48, sh - 48)
        pygame.draw.rect(self.screen, DARK_GRAY, floor_rect2)
        
        # Draw planks
        for y in range(sy + 24, sy + sh - 24, plank_spacing):
            pygame.draw.line(self.screen, GRAY, (sx + 24 - cx, y - cy), (sx + sw - 24 - cx, y - cy), 1)
        
        # Draw vertical plank dividers
        for x in range(sx + 24, sx + sw - 24, 80):
            pygame.draw.line(self.screen, LIGHT_GRAY, (x - cx, sy + 24 - cy), (x - cx, sy + sh - 24 - cy), 2)


if __name__ == "__main__":
    game = Game()
    game.run()
