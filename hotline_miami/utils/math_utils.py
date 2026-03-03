"""Math utility functions."""

import math
import random
from pygame.math import Vector2


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation between start and end."""
    return start + (end - start) * t


def lerp_vec(start: Vector2, end: Vector2, t: float) -> Vector2:
    """Linear interpolation between two vectors."""
    return Vector2(
        lerp(start.x, end.x, t),
        lerp(start.y, end.y, t)
    )


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def vec_from_angle(angle_degrees: float, magnitude: float = 1.0) -> Vector2:
    """Create a vector from angle in degrees."""
    angle_rad = math.radians(angle_degrees)
    return Vector2(
        math.cos(angle_rad) * magnitude,
        math.sin(angle_rad) * magnitude
    )


def angle_from_vec(vec: Vector2) -> float:
    """Get angle in degrees from vector."""
    return math.degrees(math.atan2(vec.y, vec.x))


def random_offset(magnitude: float) -> Vector2:
    """Get a random offset vector."""
    angle = random.uniform(0, 360)
    dist = random.uniform(0, magnitude)
    return vec_from_angle(angle, dist)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smooth interpolation between edge0 and edge1."""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
