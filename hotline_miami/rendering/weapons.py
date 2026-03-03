"""Rendering helpers for weapons."""

from __future__ import annotations

import math
import pygame

from hotline_miami import config


def draw_bat_sprite(screen: pygame.Surface, center: pygame.Vector2, angle: float, offset: pygame.Vector2, scale: float = 1.0) -> None:
    """Draw a cleaner bat sprite using a shaft + barrel + grip."""
    length = 28 * scale
    barrel = 10 * scale
    grip = 6 * scale
    thickness = 6 * scale

    direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    perp = pygame.Vector2(-direction.y, direction.x)

    shaft_start = center - direction * (length * 0.6)
    shaft_end = center + direction * (length * 0.3)

    shaft_points = [
        (shaft_start + perp * (thickness * 0.35)),
        (shaft_start - perp * (thickness * 0.35)),
        (shaft_end - perp * (thickness * 0.35)),
        (shaft_end + perp * (thickness * 0.35)),
    ]
    pygame.draw.polygon(
        screen,
        config.BROWN,
        [(p.x - offset.x, p.y - offset.y) for p in shaft_points],
    )

    barrel_center = center + direction * (length * 0.55)
    barrel_radius = barrel * 0.55
    pygame.draw.circle(
        screen,
        config.DARK_BROWN,
        (int(barrel_center.x - offset.x), int(barrel_center.y - offset.y)),
        int(barrel_radius),
    )

    grip_center = center - direction * (length * 0.75)
    pygame.draw.circle(
        screen,
        config.DARK_BROWN,
        (int(grip_center.x - offset.x), int(grip_center.y - offset.y)),
        int(grip * 0.4),
    )


def draw_pipe_sprite(screen: pygame.Surface, center: pygame.Vector2, angle: float, offset: pygame.Vector2, scale: float = 1.0) -> None:
    """Draw a metallic pipe with a bright highlight."""
    length = 30 * scale
    thickness = 5 * scale

    direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    perp = pygame.Vector2(-direction.y, direction.x)
    start = center - direction * (length * 0.6)
    end = center + direction * (length * 0.6)

    pipe_points = [
        (start + perp * thickness),
        (start - perp * thickness),
        (end - perp * thickness),
        (end + perp * thickness),
    ]
    pygame.draw.polygon(
        screen,
        config.METAL_GRAY,
        [(p.x - offset.x, p.y - offset.y) for p in pipe_points],
    )

    highlight = [
        (start + perp * (thickness * 0.4)),
        (start + perp * (thickness * 0.1)),
        (end + perp * (thickness * 0.1)),
        (end + perp * (thickness * 0.4)),
    ]
    pygame.draw.polygon(
        screen,
        (200, 205, 220),
        [(p.x - offset.x, p.y - offset.y) for p in highlight],
    )
    pygame.draw.circle(
        screen,
        config.DARK_METAL,
        (int(end.x - offset.x), int(end.y - offset.y)),
        max(1, int(thickness * 0.6)),
    )
