from dataclasses import dataclass
from pygame.math import Vector2

from zooma.entities.entity import Entity
from zooma.entities.ball import ChainBall, Ball
from zooma.entities.path import Path

from zooma.utils.vector import to_heading
from zooma.utils.colors import rainbow
from zooma.utils.distance import get_distance_between

@dataclass
class BallRecord:
    ball: ChainBall
    target_id: int

@dataclass
class InsertionRecord:
    index: int
    target_id:dataclass


class Chain(Entity):
    def __init__(self, path: Path, balls: list[ChainBall]):
        super().__init__()
        self.path = path
        
        self.color_gen = rainbow()
        self.data: list[BallRecord] = []
        for ball in balls:
            id = len(self.data)
            self.data.append(BallRecord(ball.with_id(id).with_color(next(self.color_gen)), 0))

    def check_collision(self, ball: Ball) -> tuple[int, ChainBall] | None:
        for i, record in enumerate(self.data):
            distance = get_distance_between(ball, record.ball)
            if distance <= ball.radius + record.ball.radius:
                return (i, record.ball)
        return None

    def get_insertion_point(self, ball: Ball) -> InsertionRecord | None:
        #whichever segment has the dot product between 0 and 1 is the nearest segment
        #return the index of the nearest segment

        #check if the ball is colliding with the chain
        collision_event = self.check_collision(ball)

        if not collision_event:
            return None

        collision_index, collision_ball = collision_event

        closest_distance = float('inf')
        path_segment_vector = None
        
        #for each path segment, we need to check if its the nearest segment to the ball
        for i in range(len(self.path.points) - 1):
            a = self.path.points[i]
            b = self.path.points[i + 1]
            ab = b - a
            ap = ball.position - a
            #dot product of ap and ab but cap it at 0 and 1
            #constrains point to one path segment
            t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
            point = a + ab * t
            distance = get_distance_between(ball.position, point)
            if distance < closest_distance:
                closest_distance = distance
                path_segment_vector = ab

        # Shouldn't happen
        if path_segment_vector is None:
            return InsertionRecord(collision_index, 0)
        
        impact_vector = (collision_ball.position - ball.position)
        alignment = impact_vector.dot(path_segment_vector)

        if_after = alignment > 0
        insertion_index = collision_index + (1 if if_after else 0)

        target_id = self._compute_target_id(insertion_index)

        return InsertionRecord(insertion_index, target_id)

    def _compute_target_id(self, index: int) -> int:
        if index >= len(self.data):
            index = len(self.data) - 1
        record = self.data[index]
        return record.target_id

    def append_ball(self, ball: ChainBall):
        is_empty = len(self.data) == 0
        if not is_empty:
            # get the target_id of the last ball
            prev_target_id = self.data[-1].target_id
            new_target_id = prev_target_id - 1
            if new_target_id < 0:
                new_target_id = len(self.path.points) - 1
        else:
            new_target_id = 0
        
        id = len(self.data)
        self.data.append(BallRecord(ball.with_id(id).with_color(next(self.color_gen)), new_target_id))

        
    def draw(self, screen):
        for record in self.data:
            record.ball.draw(screen)

    def update(self):
        # No update if no path
        if len(self.path.points) == 0:
            return

        for i in range(len(self.data)):
            self._updateBall(i)

    def _updateBall(self, index, speed: float = None):
        collided = False
        if speed and speed < 0.00001:
            return
        
        record = self.data[index]
        ball = record.ball
        
        if record.target_id >= len(self.path.points):
            record.target_id = 0
            return
        
        # Get this balls target
        target = self.path.points[record.target_id]
        
        if speed is None:
            move_speed = ball.speed
        else:
            move_speed = speed

        #how far away is goal
        vector_to_target = target - ball.position
        distance_to_target = vector_to_target.length()
        
        #what direction is goal
        heading = to_heading(vector_to_target)
        movement_amount = min(move_speed, distance_to_target)
        
        #how much can we move 
        distance_until_collision = 0

        if index > 0: # If there is a ball in front
            other_ball = self.data[index - 1].ball
            combined_radius = ball.radius + other_ball.radius

            vector_to_other_ball = other_ball.position - ball.position
            distance_to_other_ball = vector_to_other_ball.length()
            distance_until_collision = distance_to_other_ball - combined_radius
            
            #we are colliding
            if distance_to_other_ball < combined_radius:
                heading = to_heading(vector_to_other_ball)
                collided = True
                movement_amount = distance_until_collision #is negative in this case
                #actual movement is handled in move section
            else:
                movement_amount = min(movement_amount, distance_until_collision)


        #move        
        ball.position += heading * movement_amount

        # Update target id if we've reached the target
        updated_vector_to_target = target - ball.position
        updated_distance = updated_vector_to_target.length()
        if updated_distance < 0.001:
            # Advance to the next target
            record.target_id += 1
            if record.target_id >= len(self.path.points):
                record.target_id = 0
            
        remaining_movement = move_speed - movement_amount
        if remaining_movement > 0.001 and not collided and movement_amount > 0.001:
            # Try Again
            self._updateBall(index, remaining_movement)
