"""Environment rendering helpers."""

from __future__ import annotations

import random
import pygame

from hotline_miami import config


def draw_dirt_ground(screen: pygame.Surface, camera_offset: pygame.Vector2) -> None:
    cx, cy = camera_offset.x, camera_offset.y

    dirt_rect = pygame.Rect(-cx, -cy, config.WORLD_WIDTH, config.WORLD_HEIGHT)
    pygame.draw.rect(screen, config.DIRT_BROWN, dirt_rect)

    seed = 42
    random.seed(seed)
    for _ in range(400):
        x = random.randint(0, config.WORLD_WIDTH)
        y = random.randint(0, config.WORLD_HEIGHT)
        size = random.randint(3, 12)
        color = random.choice([config.DIRT_LIGHT, config.DIRT_DARK])
        pygame.draw.circle(screen, color, (int(x - cx), int(y - cy)), size)

    for _ in range(150):
        x = random.randint(0, config.WORLD_WIDTH)
        y = random.randint(0, config.WORLD_HEIGHT)
        size = random.randint(2, 4)
        pygame.draw.circle(screen, (90, 85, 80), (int(x - cx), int(y - cy)), size)

    for _ in range(80):
        x = random.randint(0, config.WORLD_WIDTH)
        y = random.randint(0, config.WORLD_HEIGHT)
        color = (60, 80, 40)
        for _ in range(3):
            ox = random.randint(-5, 5)
            oy = random.randint(-5, 5)
            pygame.draw.line(screen, color, (x - cx, y - cy), (x + ox - cx, y + oy - cy), 2)

    random.seed()


def draw_building_floors(
    screen: pygame.Surface,
    camera_offset: pygame.Vector2,
    main_building: tuple,
    small_building: tuple,
) -> None:
    cx, cy = camera_offset.x, camera_offset.y

    mx, my, mw, mh = main_building
    wall_thickness = 28
    floor_rect = pygame.Rect(mx + wall_thickness - cx, my + wall_thickness - cy, mw - wall_thickness * 2, mh - wall_thickness * 2)
    pygame.draw.rect(screen, config.DARK_GRAY, floor_rect)

    plank_spacing = 18
    for y in range(int(floor_rect.top), int(floor_rect.bottom), plank_spacing):
        pygame.draw.line(screen, config.GRAY, (floor_rect.left, y), (floor_rect.right, y), 1)

    for x in range(int(floor_rect.left), int(floor_rect.right), 90):
        pygame.draw.line(screen, config.LIGHT_GRAY, (x, floor_rect.top), (x, floor_rect.bottom), 2)

    sx, sy, sw, sh = small_building
    floor_rect2 = pygame.Rect(sx + wall_thickness - cx, sy + wall_thickness - cy, sw - wall_thickness * 2, sh - wall_thickness * 2)
    pygame.draw.rect(screen, config.DARK_GRAY, floor_rect2)

    for y in range(int(floor_rect2.top), int(floor_rect2.bottom), plank_spacing):
        pygame.draw.line(screen, config.GRAY, (floor_rect2.left, y), (floor_rect2.right, y), 1)

    for x in range(int(floor_rect2.left), int(floor_rect2.right), 90):
        pygame.draw.line(screen, config.LIGHT_GRAY, (x, floor_rect2.top), (x, floor_rect2.bottom), 2)
