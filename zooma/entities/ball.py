from abc import ABC, abstractmethod
import math
import pygame

from pygame import Color, Vector2
from zooma.entities.entity import Entity


class Ball(Entity):
    def __init__(self, position: Vector2, color):
        self.position = Vector2(position)

        self.radius = 20
        self.color = color
        # TODO: This implies new
        self.is_shot_ball = False
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)
        if hasattr(self, 'id'):
            self.draw_text(screen, str(self.id), self.position)

    def draw_text(self, screen: pygame.Surface, text: str, pos: Vector2):
        text_surface = self.font.render(text, True, Color('black'))
        text_rect = text_surface.get_rect(center=pos)
        screen.blit(text_surface, text_rect)


    def check_collision(self, other_ball):
        distance = self.position.distance_to(other_ball.position)
        return distance < (self.radius + other_ball.radius)

class TargetBall(Ball):
    def __init__(self, position):
        super().__init__(position, Color('red'))

    def update(self):
        pass

class HeldBall(Ball):
    def __init__(self, color: Color):
        position = Vector2(0, 0)
        super().__init__(position, color)

    def set_position(self, position):
        self.position = Vector2(position)

    def update(self):
        pass

class ShotBall(Ball):
    def __init__(self, position, color: Color):
        super().__init__(position, color)

        self.heading = Vector2(0, -1)
        self.speed = 10

    def set_heading(self, heading: Vector2):
        self.heading = heading
        
    def update(self):
        self.position += self.heading * self.speed

class ChainBall(Ball):
    def __init__ (self, position, color: Color):
        super().__init__(position, color)

        # self.heading = Vector2(1, 0)
        self.speed = 2
        self.behind: ChainBall = None
        self.infront: ChainBall = None

    def with_color(self, color):
        self.color = color
        return self

    def append(self, ball: "ChainBall"):
        assert ball is not None, "The fuck you doing man? no ballz"

        self.behind = ball
        ball.infront = self
        ball.set_target(self.position)

    def update(self):
        if self.infront:
            goal_offset = self.infront.position - self.position
            collision_range = self.radius + self.infront.radius
        else:
            # goal_offset = self.target - self.position
            goal_offset = self.target - self.position
            # goal_offset = (self.heading * self.speed)
            collision_range = self.radius * 2

        # how far away is goal
        distance = goal_offset.length()

        # where is goal
        heading = goal_offset
        if heading.length() != 0:
            heading = heading.normalize()
        
        # how close can we go
        max_distance = distance - collision_range

        #move
        self.position += heading * min(self.speed, max_distance)

    def check_collision(self, other_ball: Ball):
        distance = self.position.distance_to(other_ball.position)
        return distance < (self.radius + other_ball.radius)

    def set_target(self, target):
        if isinstance(target, ChainBall):
            target = target.position

        self.target = target

if __name__ == "__main__":
    print("Don't be an idiot and run the ball")