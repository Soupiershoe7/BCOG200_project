from abc import ABC, abstractmethod
import math
import pygame

from pygame import Color, Vector2


class Ball(ABC):
    def __init__(self, position: Vector2, color):
        self.position = position

        self.radius = 20
        self.color = color
        # TODO: This implies new
        self.is_shot_ball = False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    @abstractmethod
    def update(self):
        pass
        
    def check_collision(self, other_ball):
        distance = self.position.distance_to(other_ball.position)
        return distance < (self.radius + other_ball.radius)

class TargetBall(Ball):
    def __init__(self, position):
        super().__init__(position, Color('red'))

    def update(self):
        pass

class HeldBall(Ball):
    def __init__(self, position = None):
        if position is None:
            position = Vector2(0, 0)
        super().__init__(position, Color('green'))

    def set_position(self, position):
        self.position = Vector2(position)

    def update(self):
        pass

class MovableBall(Ball):
    def __init__(self, position):
        super().__init__(position, Color('blue'))

        self.heading = Vector2(0, -1)
        self.speed = 10

    def set_heading(self, angle):
        self.heading = Vector2(math.cos(angle), math.sin(angle))
        
    def update(self):
        self.position += self.heading * self.speed