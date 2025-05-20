from pygame import Vector2
import pygame
from zooma.entities.entity import Entity
from zooma.entities.chain import Chain


class DeathHole(Entity):
    def __init__(self, position: Vector2):
        super().__init__()
        self.position = Vector2(position)
        self.death_radius = 5

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), self.position, 20)
        pygame.draw.circle(screen, (0, 0, 0), self.position, 18)
        pygame.draw.circle(screen, (255, 0, 0), self.position, self.death_radius)


    def check_collision(self, other: Chain):
        if len(other) == 0:
            print("!!!! Warning found empty chain !!!!")
            return False
            
        first_ball = other.get_first_ball()
        distance = self.position.distance_to(first_ball.position)
        return distance < self.death_radius