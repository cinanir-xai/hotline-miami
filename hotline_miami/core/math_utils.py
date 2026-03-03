"""Math helpers for geometry checks."""

from __future__ import annotations

import math
import pygame


def line_segments_intersect(p1: pygame.Vector2, p2: pygame.Vector2, q1: pygame.Vector2, q2: pygame.Vector2) -> bool:
    def ccw(a: pygame.Vector2, b: pygame.Vector2, c: pygame.Vector2) -> bool:
        return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)

    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))


def angle_difference(a: float, b: float) -> float:
    return (a - b + math.pi) % (2 * math.pi) - math.pi
