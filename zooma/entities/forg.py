from pygame import Vector2, Color
import pygame
import time

from zooma.entities.entity import Entity
from zooma.entities.ball import Ball, ShotBall, HeldBall
from zooma.utils.colors import LevelColors

SHOOT_COOLDOWN = 500  # in ms

class Forg(Entity):
    def __init__(self, position: Vector2, colors: LevelColors):
        super().__init__()
        self.position = position
        self.color = Color('DarkOliveGreen')
        self.level_colors = colors
        
        self.held_ball: Ball | None = None
        self.reserve_ball: Ball | None = None

        self.radius = 40

        self.heading = Vector2(1,0)
        self.last_shot_time = 0
        
    def _get_held_position(self):
        return Vector2(self.position) + self.heading * self.radius

    def hold(self, ball: Ball):
        self.held_ball = ball

    def reserve(self, ball: Ball):
        self.reserve_ball = ball

    def set_heading(self, position: Vector2):
        position = Vector2(position)
        self.heading = (position - self.position).normalize()

    def swap_ball(self):
        self.held_ball, self.reserve_ball = self.reserve_ball, self.held_ball

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if self.held_ball is None or current_time - self.last_shot_time < SHOOT_COOLDOWN:
            return None
        
        shot_ball = ShotBall(self._get_held_position(), self.held_ball.color)
        shot_ball.set_heading(self.heading)

        self.held_ball = None
        self.last_shot_time = current_time

        return shot_ball

    def update(self):
        if self.held_ball is None and self.reserve_ball is not None:
            self.swap_ball()
        
        current_time = pygame.time.get_ticks()
        if self.reserve_ball is None:
            self.reserve_ball = HeldBall(self.level_colors.get_color())
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)
        
        if self.held_ball:
            self.held_ball.position = self._get_held_position()
            self.held_ball.draw(screen)

        if self.reserve_ball:
            self.reserve_ball.set_position(self.position)
            self.reserve_ball.draw(screen)
            
        