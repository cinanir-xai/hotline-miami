"""Player entity with detailed animations."""

import pygame
import math
from pygame.math import Vector2
from typing import Optional, Callable

from .entity import Entity
from config import (
    PLAYER_SIZE, PLAYER_SPEED, PLAYER_ACCEL, PLAYER_DECEL,
    PLAYER_ATTACK_RANGE, PLAYER_ATTACK_COOLDOWN, PLAYER_ATTACK_DAMAGE,
    PUNCH_DURATION, PUNCH_EXTEND_DISTANCE, Colors,
    SCREEN_WIDTH, SCREEN_HEIGHT
)
from utils.math_utils import lerp, clamp, angle_from_vec, vec_from_angle


class Player(Entity):
    """Player character with top-down view and punch animations."""
    
    def __init__(self, x: float, y: float):
        super().__init__(x, y, PLAYER_SIZE)
        
        # Movement
        self.target_velocity = Vector2(0, 0)
        self.facing = Vector2(0, 1)  # Default facing down
        self.move_input = Vector2(0, 0)
        
        # Combat
        self.attack_cooldown = 0.0
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_hand = "right"  # alternates between right and left
        self.attack_angle = 0.0
        self.on_punch_callback: Optional[Callable] = None
        
        # Animation
        self.bob_offset = 0.0
        self.arm_extension = 0.0
        
        # Visual
        self.head_radius = 14
        self.shoulder_width = 28
        self.shoulder_height = 18
        
    def set_punch_callback(self, callback: Callable):
        """Set callback for punch effects."""
        self.on_punch_callback = callback
        
    def handle_input(self, keys, mouse_pos: Vector2, mouse_clicked: bool, 
                     camera_offset: Vector2):
        """Process input for this frame."""
        # Movement input
        self.move_input = Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.move_input.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.move_input.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.move_input.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.move_input.x += 1
            
        # Normalize movement input
        if self.move_input.length_squared() > 0:
            self.move_input = self.move_input.normalize()
            
        # Calculate facing direction (towards mouse)
        screen_pos = self.position - camera_offset
        mouse_delta = mouse_pos - screen_pos
        if mouse_delta.length_squared() > 0:
            self.facing = mouse_delta.normalize()
            
        # Attack input
        if mouse_clicked and self.attack_cooldown <= 0 and not self.is_attacking:
            self.start_attack()
    
    def start_attack(self):
        """Start a punch attack."""
        self.is_attacking = True
        self.attack_timer = PUNCH_DURATION
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
        self.attack_angle = angle_from_vec(self.facing)
        
        # Alternate hands
        self.attack_hand = "left" if self.attack_hand == "right" else "right"
    
    def update(self, dt: float):
        """Update player state."""
        super().update(dt)
        
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        # Handle attack animation
        if self.is_attacking:
            prev_timer = self.attack_timer
            self.attack_timer -= dt
            
            # Trigger effect at peak of punch
            if prev_timer > PUNCH_DURATION * 0.5 and self.attack_timer <= PUNCH_DURATION * 0.5:
                if self.on_punch_callback:
                    punch_pos = self.position + vec_from_angle(self.attack_angle, PLAYER_ATTACK_RANGE * 0.6)
                    self.on_punch_callback(punch_pos.x, punch_pos.y, self.attack_angle)
            
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.arm_extension = 0.0
            else:
                # Punch animation curve (extend then retract)
                progress = 1.0 - (self.attack_timer / PUNCH_DURATION)
                # Sine curve for punch: 0 -> 1 -> 0
                self.arm_extension = math.sin(progress * math.pi) * PUNCH_EXTEND_DISTANCE
        
        # Smooth acceleration/deceleration
        if self.move_input.length_squared() > 0:
            # Accelerate towards target velocity
            target = self.move_input * PLAYER_SPEED
            self.velocity = Vector2(
                lerp(self.velocity.x, target.x, 1 - math.exp(-PLAYER_ACCEL * dt)),
                lerp(self.velocity.y, target.y, 1 - math.exp(-PLAYER_ACCEL * dt))
            )
            self.state = "moving"
        else:
            # Decelerate to stop
            self.velocity = Vector2(
                lerp(self.velocity.x, 0, 1 - math.exp(-PLAYER_DECEL * dt)),
                lerp(self.velocity.y, 0, 1 - math.exp(-PLAYER_DECEL * dt))
            )
            if self.velocity.length_squared() < 1:
                self.velocity = Vector2(0, 0)
                self.state = "idle"
        
        # Apply movement
        self.position += self.velocity * dt
        
        # Head bob animation when moving
        if self.state == "moving":
            self.bob_offset = math.sin(self.animation_time * 15) * 2
        else:
            self.bob_offset = lerp(self.bob_offset, 0, dt * 10)
    
    def draw(self, surface: pygame.Surface, camera_offset: Vector2):
        """Draw the player with detailed top-down view."""
        pos = self.position - camera_offset
        
        # Draw shadow
        self.draw_shadow(surface, camera_offset, radius=16, alpha=50)
        
        # Calculate positions
        head_center = Vector2(pos.x, pos.y - 8 + self.bob_offset) + self.facing * 2
        shoulder_y = pos.y + 5 + self.bob_offset * 0.5
        
        # Get arm positions based on facing direction
        arm_offset = self._get_arm_offsets(pos, shoulder_y)
        
        # Draw arms (behind body)
        self._draw_arms(surface, arm_offset, behind=True)
        
        # Draw shoulders/body
        self._draw_shoulders(surface, pos, shoulder_y)
        
        # Draw head
        self._draw_head(surface, head_center)
        
        # Draw arms (in front of body)
        self._draw_arms(surface, arm_offset, behind=False)
        
        # Draw attack range indicator when attacking
        if self.is_attacking:
            self._draw_attack_indicator(surface, pos)
        
        # Draw subtle aim indicator when idle
        if not self.is_attacking:
            self._draw_aim_indicator(surface, pos)
    
    def _draw_attack_indicator(self, surface: pygame.Surface, screen_pos: Vector2):
        """Draw a subtle attack indicator."""
        angle_rad = math.radians(self.attack_angle)
        end_x = screen_pos.x + math.cos(angle_rad) * PLAYER_ATTACK_RANGE
        end_y = screen_pos.y + math.sin(angle_rad) * PLAYER_ATTACK_RANGE
        
        # Very subtle line
        pygame.draw.line(surface, (255, 255, 255, 30), (screen_pos.x, screen_pos.y), (end_x, end_y), 1)

    def _draw_aim_indicator(self, surface: pygame.Surface, screen_pos: Vector2):
        """Draw a subtle aim indicator when idle."""
        angle_rad = math.radians(angle_from_vec(self.facing))
        end_x = screen_pos.x + math.cos(angle_rad) * 20
        end_y = screen_pos.y + math.sin(angle_rad) * 20
        pygame.draw.line(surface, (255, 255, 255, 20), (screen_pos.x, screen_pos.y), (end_x, end_y), 1)
    
    def _get_arm_offsets(self, pos: Vector2, shoulder_y: float) -> dict:
        """Calculate arm positions based on facing direction."""
        angle = angle_from_vec(self.facing)
        
        # Base shoulder positions (relative to center)
        shoulder_left = Vector2(-self.shoulder_width * 0.4, shoulder_y - pos.y)
        shoulder_right = Vector2(self.shoulder_width * 0.4, shoulder_y - pos.y)
        
        # If attacking, extend the attacking arm
        if self.is_attacking:
            extend_vec = vec_from_angle(self.attack_angle, self.arm_extension)
            if self.attack_hand == "right":
                shoulder_right += extend_vec
            else:
                shoulder_left += extend_vec
        
        # Slight offset based on facing (arms show more on sides when facing left/right)
        facing_angle = angle_from_vec(self.facing)
        side_factor = abs(math.cos(math.radians(facing_angle))) * 3
        
        if 90 < facing_angle < 270:  # Facing left
            shoulder_left.x -= side_factor
            shoulder_right.x -= side_factor * 0.5
        else:  # Facing right
            shoulder_left.x += side_factor * 0.5
            shoulder_right.x += side_factor
        
        return {
            'left': Vector2(pos.x + shoulder_left.x, pos.y + shoulder_left.y),
            'right': Vector2(pos.x + shoulder_right.x, pos.y + shoulder_right.y)
        }
    
    def _draw_shoulders(self, surface: pygame.Surface, pos: Vector2, shoulder_y: float):
        """Draw the shoulders and upper body."""
        # Main body (jacket)
        body_width = self.shoulder_width
        body_height = self.shoulder_height
        
        # Create gradient effect for jacket
        body_rect = pygame.Rect(
            pos.x - body_width / 2,
            shoulder_y - body_height / 2,
            body_width,
            body_height
        )
        
        # Draw jacket with slight gradient
        pygame.draw.ellipse(surface, Colors.JACKET_BROWN, body_rect)
        
        # Inner shirt (white V-neck visible from top)
        shirt_rect = pygame.Rect(
            pos.x - body_width * 0.25,
            shoulder_y - body_height * 0.3,
            body_width * 0.5,
            body_height * 0.6
        )
        pygame.draw.ellipse(surface, Colors.SHIRT_WHITE, shirt_rect)
        
        # Shirt shadow/depth
        pygame.draw.ellipse(surface, Colors.SHIRT_SHADOW, 
                           (pos.x - 2, shoulder_y - 2, 4, 4))
        
        # Jacket collar details
        collar_points = [
            (pos.x - body_width * 0.3, shoulder_y - body_height * 0.4),
            (pos.x, shoulder_y - body_height * 0.1),
            (pos.x + body_width * 0.3, shoulder_y - body_height * 0.4),
        ]
        pygame.draw.lines(surface, Colors.JACKET_DARK, False, collar_points, 2)
    
    def _draw_head(self, surface: pygame.Surface, head_center: Vector2):
        """Draw the head with detailed features from top-down view."""
        # Head base (skin)
        head_rect = pygame.Rect(
            head_center.x - self.head_radius,
            head_center.y - self.head_radius,
            self.head_radius * 2,
            self.head_radius * 2
        )
        
        # Draw head with slight oval shape (slightly taller than wide)
        pygame.draw.ellipse(surface, Colors.SKIN_LIGHT, head_rect)
        
        # Face direction indicator (nose/chin shadow area)
        facing_angle = angle_from_vec(self.facing)
        nose_offset = vec_from_angle(facing_angle, self.head_radius * 0.55)
        nose_pos = (head_center.x + nose_offset.x, head_center.y + nose_offset.y)
        
        # Subtle nose shadow
        pygame.draw.ellipse(surface, Colors.SKIN_SHADOW,
                           (nose_pos[0] - 3, nose_pos[1] - 2, 6, 4))
        
        # Directional brow shadow to emphasize facing
        brow_offset = vec_from_angle(facing_angle, self.head_radius * 0.25)
        pygame.draw.arc(surface, Colors.SKIN_SHADOW,
                       (head_center.x - self.head_radius + brow_offset.x * 0.2,
                        head_center.y - self.head_radius + brow_offset.y * 0.2,
                        self.head_radius * 2, self.head_radius * 2),
                       math.radians(facing_angle - 50),
                       math.radians(facing_angle + 50), 2)
        
        # Hair - drawn based on facing direction
        self._draw_hair(surface, head_center, facing_angle)
        
        # Ears (visible from sides when facing left/right)
        self._draw_ears(surface, head_center, facing_angle)
        
        # Eyes (subtle, visible from top when looking up/down)
        self._draw_eyes(surface, head_center, facing_angle)
    
    def _draw_hair(self, surface: pygame.Surface, head_center: Vector2, 
                   facing_angle: float):
        """Draw hair with direction-based styling."""
        hair_color = Colors.HAIR_BROWN
        hair_dark = Colors.HAIR_DARK
        
        # Hair is always on the back of the head relative to facing
        back_angle = facing_angle + 180
        hair_center = vec_from_angle(back_angle, self.head_radius * 0.3)
        hair_x = head_center.x + hair_center.x
        hair_y = head_center.y + hair_center.y
        
        # Main hair mass
        hair_radius = self.head_radius * 0.85
        hair_rect = pygame.Rect(
            hair_x - hair_radius,
            hair_y - hair_radius,
            hair_radius * 2,
            hair_radius * 2
        )
        pygame.draw.ellipse(surface, hair_color, hair_rect)
        
        # Hair texture/detail
        for i in range(5):
            angle_offset = (i - 2) * 15
            detail_angle = back_angle + angle_offset
            detail_vec = vec_from_angle(detail_angle, hair_radius * 0.7)
            detail_x = hair_x + detail_vec.x
            detail_y = hair_y + detail_vec.y
            pygame.draw.ellipse(surface, hair_dark,
                              (detail_x - 2, detail_y - 2, 4, 4))
        
        # Hairline/forehead shadow
        forehead_vec = vec_from_angle(facing_angle, self.head_radius * 0.6)
        pygame.draw.arc(surface, hair_dark,
                       (head_center.x - self.head_radius, head_center.y - self.head_radius,
                        self.head_radius * 2, self.head_radius * 2),
                       math.radians(facing_angle - 60),
                       math.radians(facing_angle + 60), 2)
    
    def _draw_ears(self, surface: pygame.Surface, head_center: Vector2,
                   facing_angle: float):
        """Draw ears visible from the sides."""
        ear_width = 4
        ear_height = 6
        
        # Left ear (visible when not facing directly right)
        if not (45 < facing_angle < 135):  # Not facing down
            left_ear_x = head_center.x - self.head_radius - ear_width * 0.5
            left_ear_y = head_center.y
            pygame.draw.ellipse(surface, Colors.SKIN_MID,
                              (left_ear_x - ear_width/2, left_ear_y - ear_height/2,
                               ear_width, ear_height))
        
        # Right ear (visible when not facing directly left)
        if not (225 < facing_angle < 315):  # Not facing up
            right_ear_x = head_center.x + self.head_radius + ear_width * 0.5
            right_ear_y = head_center.y
            pygame.draw.ellipse(surface, Colors.SKIN_MID,
                              (right_ear_x - ear_width/2, right_ear_y - ear_height/2,
                               ear_width, ear_height))
    
    def _draw_eyes(self, surface: pygame.Surface, head_center: Vector2,
                   facing_angle: float):
        """Draw eyes visible when facing up or down."""
        eye_size = 2
        eye_offset_x = 5
        eye_offset_y = 3
        
        # Eyes are visible when facing mostly up or down
        vertical_factor = abs(math.cos(math.radians(facing_angle)))
        
        if vertical_factor > 0.3:
            # Determine eye Y position based on facing
            if 0 <= facing_angle <= 180:  # Facing down-ish
                eye_y = head_center.y + eye_offset_y
            else:  # Facing up-ish
                eye_y = head_center.y - eye_offset_y
            
            # Left eye
            pygame.draw.circle(surface, Colors.WHITE,
                             (head_center.x - eye_offset_x, eye_y), eye_size)
            pygame.draw.circle(surface, Colors.BLACK,
                             (head_center.x - eye_offset_x, eye_y), eye_size - 0.5)
            
            # Right eye
            pygame.draw.circle(surface, Colors.WHITE,
                             (head_center.x + eye_offset_x, eye_y), eye_size)
            pygame.draw.circle(surface, Colors.BLACK,
                             (head_center.x + eye_offset_x, eye_y), eye_size - 0.5)
    
    def _draw_arms(self, surface: pygame.Surface, arm_offset: dict, behind: bool):
        """Draw arms."""
        arm_width = 8
        arm_length = 12
        
        for hand, arm_pos in arm_offset.items():
            # Determine if this arm should be drawn now based on facing
            is_right = hand == "right"
            
            # Simple depth sorting: when facing left, right arm is behind, etc.
            facing_angle = angle_from_vec(self.facing)
            arm_behind = False
            
            if 90 < facing_angle < 270:  # Facing left
                arm_behind = is_right
            else:  # Facing right
                arm_behind = not is_right
            
            if arm_behind == behind:
                # Draw arm
                arm_rect = pygame.Rect(
                    arm_pos.x - arm_width / 2,
                    arm_pos.y - arm_length / 2,
                    arm_width,
                    arm_length
                )
                pygame.draw.ellipse(surface, Colors.JACKET_BROWN, arm_rect)
                
                # Hand (skin color at end of arm)
                hand_offset = vec_from_angle(angle_from_vec(self.facing), arm_length * 0.3)
                if self.is_attacking and hand == self.attack_hand:
                    # Extended hand during punch
                    hand_offset = vec_from_angle(self.attack_angle, 
                                                 arm_length * 0.3 + self.arm_extension * 0.3)
                
                hand_pos = (arm_pos.x + hand_offset.x, arm_pos.y + hand_offset.y)
                pygame.draw.circle(surface, Colors.SKIN_MID, hand_pos, 4)
                
                # Fist detail when attacking
                if self.is_attacking and hand == self.attack_hand:
                    pygame.draw.circle(surface, Colors.SKIN_LIGHT, hand_pos, 3)
