from pygame.color import Color

def rainbow():
    """Yields a sequence of colors cycling through the hue spectrum."""
    hue = 0
    step = 31
    while True:
        color = Color(0)
        color.hsva = (hue, 100, 100, 100)
        yield color
        hue = (hue + step) % 360
