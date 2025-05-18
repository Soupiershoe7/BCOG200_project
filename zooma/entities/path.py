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
        new_point = Vector2(point)
        is_empty = len(self.points) == 0

        if is_empty or (self.points[-1].distance_to(new_point) > 5):
            self.points.append(new_point)

    def clear(self):
        self.points = []

    def distance_between_point_and_position(self, goal_id: int, position: Vector2) -> float:
        """
        Return the distance between some position near a path segment and a 
        point (index) on the path segment.
        """
        goal_id = goal_id % len(self.points)

        segment_point_start = 0
        segment_point_end = 0
        closest_distance = float('inf')
        projected_point = Vector2(0, 0)

        for i in range(len(self.points) - 1):
            a = self.points[i]
            b = self.points[i + 1]
            ab = b - a
            ap = position - a
            t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
            point = a + ab * t
            distance = point.distance_to(position)
            if distance < closest_distance:
                closest_distance = distance
                projected_point = point
                segment_point_start = i
                segment_point_end = i + 1
                
        
        if goal_id <= segment_point_start:
            segment_point_id = segment_point_start
        else:
            segment_point_id = segment_point_end

        distance_between_points = self.distance_between_points(goal_id, segment_point_id)

        return distance_between_points + projected_point.distance_to(self.points[segment_point_id])
        
        

    def distance_between_points(self, p1: int, p2: int) -> float:
        """
        Return the distance between two points along the path.
        """
        path_length = 0
        if p1 < p2:
            index = p1
            end = p2
        else:
            index = p2
            end = p1

        while index != end:
            a = self.points[index]
            b = self.points[(index + 1) % len(self.points)]
            path_length += a.distance_to(b)
            index = (index + 1) % len(self.points)
        return path_length

    def draw(self, screen):
        for i in range(len(self.points)-1):
            pygame.draw.line(screen, (255,255,255), self.points[i], self.points[i+1], 1)