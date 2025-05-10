from pygame import Vector2

def to_heading(vector: Vector2):
    if vector.length() != 0:
        return vector.normalize()
    return vector
    