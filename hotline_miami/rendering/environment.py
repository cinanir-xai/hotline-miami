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
    floor_rect = pygame.Rect(mx + 24 - cx, my + 24 - cy, mw - 48, mh - 48)
    pygame.draw.rect(screen, config.DARK_GRAY, floor_rect)

    plank_spacing = 20
    for y in range(my + 24, my + mh - 24, plank_spacing):
        pygame.draw.line(screen, config.GRAY, (mx + 24 - cx, y - cy), (mx + mw - 24 - cx, y - cy), 1)

    for x in range(mx + 24, mx + mw - 24, 80):
        pygame.draw.line(screen, config.LIGHT_GRAY, (x - cx, my + 24 - cy), (x - cx, my + mh - 24 - cy), 2)

    sx, sy, sw, sh = small_building
    floor_rect2 = pygame.Rect(sx + 24 - cx, sy + 24 - cy, sw - 48, sh - 48)
    pygame.draw.rect(screen, config.DARK_GRAY, floor_rect2)

    for y in range(sy + 24, sy + sh - 24, plank_spacing):
        pygame.draw.line(screen, config.GRAY, (sx + 24 - cx, y - cy), (sx + sw - 24 - cx, y - cy), 1)

    for x in range(sx + 24, sx + sw - 24, 80):
        pygame.draw.line(screen, config.LIGHT_GRAY, (x - cx, sy + 24 - cy), (x - cx, sy + sh - 24 - cy), 2)
