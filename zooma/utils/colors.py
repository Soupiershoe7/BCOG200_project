from pygame.color import Color
import random

def rainbow():
    """Yields a sequence of colors cycling through the hue spectrum."""
    hue = 0
    step = 31
    while True:
        color = Color(0)
        color.hsva = (hue, 100, 100, 100)
        yield color
        hue = (hue + step) % 360

DEFAULT_COLORS = [
    Color('red'),
    Color('green'),
    Color('blue'),
    Color('yellow'),
    Color('purple'),
    Color('white')
]

class LevelColors:
    def __init__(self, difficulty: int, color_set: list[Color] = DEFAULT_COLORS):
        self.colors = color_set[:difficulty]
        self.color_cluster_sizes = [1, 2, 3]

    def get_color(self):
        return random.choice(self.colors)

    def set_colors(self, colors: list[Color]):
        self.colors = colors

    def set_difficulty(self, difficulty: int):
        self.colors = DEFAULT_COLORS[:difficulty]

    def is_valid_color(self, color: Color):
        return color in self.colors
        
    def get_color_generator(self):
        last_color = None
        while True:
            cluster_size = random.choice(self.color_cluster_sizes)
            color = random.choice(self.colors)
            if color == last_color:
                continue
            last_color = color
            for _ in range(cluster_size):
                yield color
    