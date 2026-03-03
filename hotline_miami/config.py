"""Game configuration and constants."""

import pygame
from pygame.math import Vector2

# Window settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "Hotline Miami - Top Down Shooter"

# Colors
class Colors:
    # Ground
    DIRT_BASE = (101, 67, 33)
    DIRT_LIGHT = (139, 90, 43)
    DIRT_DARK = (80, 50, 25)
    
    # Player
    SKIN_LIGHT = (255, 220, 177)
    SKIN_MID = (240, 190, 140)
    SKIN_SHADOW = (200, 150, 100)
    
    # Hair
    HAIR_BROWN = (60, 40, 20)
    HAIR_DARK = (30, 20, 10)
    
    # Clothing
    SHIRT_WHITE = (240, 240, 240)
    SHIRT_SHADOW = (180, 180, 180)
    JACKET_BROWN = (139, 90, 43)
    JACKET_DARK = (100, 60, 30)
    
    # Effects
    SHADOW = (0, 0, 0, 80)
    BLOOD_RED = (180, 30, 30)
    
    # UI
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)

# Player settings
PLAYER_SIZE = 48
PLAYER_SPEED = 280  # pixels per second
PLAYER_ACCEL = 1200  # acceleration
PLAYER_DECEL = 800  # deceleration
PLAYER_ATTACK_RANGE = 60
PLAYER_ATTACK_COOLDOWN = 0.3  # seconds
PLAYER_ATTACK_DAMAGE = 25

# Animation settings
ANIMATION_FPS = 12
PUNCH_DURATION = 0.25  # seconds
PUNCH_EXTEND_DISTANCE = 25  # how far arm extends

# Camera settings
CAMERA_SMOOTHNESS = 0.1  # lower = smoother but more lag

# Ground tile settings
TILE_SIZE = 64
GROUND_VARIATION = 8  # number of dirt variations
