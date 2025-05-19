from pygame.math import Vector2
from zooma.entities.ball import Ball

# utility function to for getting the distance between balls and vectors

def get_distance_between(a, b):
    # Support Ball or Vector2 or tuple
    point1 = a.position if isinstance(a, Ball) else Vector2(a)
    point2 = b.position if isinstance(b, Ball) else Vector2(b)
    return point1.distance_to(point2)