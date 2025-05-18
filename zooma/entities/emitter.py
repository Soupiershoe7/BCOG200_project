from pygame import Vector2, Color
import pygame

from zooma.entities.entity import Entity
from zooma.entities.chain import Chain
from zooma.utils.colors import LevelColors

class Emitter (Entity):
    def __init__(self, position: Vector2, level_colors: LevelColors):
        super().__init__()
        self.position = Vector2(position)
        self.level_colors = level_colors
        self.color_generator = self.level_colors.get_color_generator()
        self.active = True

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def is_active(self):
        return self.active

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), self.position, 20)

    def get_color(self):
        return next(self.color_generator)
        
    def check_collision(self, other: Chain):
        last_ball = other.get_last_ball()
        distance = self.position.distance_to(last_ball.position)
        return distance < last_ball.radius * 2 - 5
        
        