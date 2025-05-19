from pygame import Vector2, Color
import pygame
import math

from zooma.entities.entity import Entity
from zooma.entities.ball import Ball, ShotBall, HeldBall
from zooma.utils.colors import LevelColors

SHOOT_COOLDOWN = 500  # in ms
DEATH_ANIMATION_TIME = 3000

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

        self.is_dead = False
        self.time_of_death = 0
        
    def _get_held_position(self):
        return Vector2(self.position) + self.heading * self.radius

    def set_heading(self, position: Vector2):
        if self.is_dead:
            return
        position = Vector2(position)
        self.heading = (position - self.position).normalize()

    def swap_ball(self):
        self.held_ball, self.reserve_ball = self.reserve_ball, self.held_ball

    def shoot(self):
        if self.is_dead:
            return None
        
        current_time = pygame.time.get_ticks()
        if self.held_ball is None or current_time - self.last_shot_time < SHOOT_COOLDOWN:
            return None
        
        shot_ball = ShotBall(self._get_held_position(), self.held_ball.color)
        shot_ball.set_heading(self.heading)

        self.held_ball = None
        self.last_shot_time = current_time

        return shot_ball

    def die(self):
        self.is_dead = True
        self.time_of_death = pygame.time.get_ticks()

    def reset(self):
        self.is_dead = False
        self.time_of_death = 0

    def update(self):
        if self.is_dead:
            # get angle from heading
            angle = math.degrees(math.atan2(self.heading.y, self.heading.x))
            spin_rate = 1440 / 60
            elapsed_time = pygame.time.get_ticks() - self.time_of_death
            animation_progress = min(1, elapsed_time / DEATH_ANIMATION_TIME)
            easing_progress = (1 - (1 - animation_progress) ** 3)
            angle += max(0, spin_rate - (spin_rate * easing_progress))
            self.heading = Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
            return
        
        if self.held_ball is None and self.reserve_ball is not None:
            self.swap_ball()
        
        current_time = pygame.time.get_ticks()
        if self.reserve_ball is None:
            self.reserve_ball = HeldBall(self.level_colors.get_color())

        if not self.level_colors.is_valid_color(self.reserve_ball.color):
            self.reserve_ball.color = self.level_colors.get_color()

        if self.held_ball is not None and not self.level_colors.is_valid_color(self.held_ball.color):
            self.held_ball.color = self.level_colors.get_color()
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)
        
        if self.held_ball:
            self.held_ball.position = self._get_held_position()
            self.held_ball.draw(screen)

        if self.reserve_ball:
            pygame.draw.circle(screen, self.reserve_ball.color, self.position, 8)
            
        