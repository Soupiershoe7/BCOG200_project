from pygame import Vector2
import pygame
from zooma.entities.entity import Entity


class Path(Entity):
    def __init__(self, init_points: list[tuple[float, float]]):
        super().__init__()
        self.points = []
        for point in init_points:
            self.addPoint(point)

    def addPoint(self, point):
        self.points.append(Vector2(point))

    def clear(self):
        self.points = []

    def draw(self, screen):
        for i in range(len(self.points)-1):
            pygame.draw.line(screen, (255,255,255), self.points[i], self.points[i+1], 1)