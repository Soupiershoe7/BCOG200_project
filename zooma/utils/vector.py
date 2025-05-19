from pygame import Vector2

# utility function to normalize a vector into a heading

def to_heading(vector: Vector2):
    if vector.length() != 0:
        return vector.normalize()
    return vector
    