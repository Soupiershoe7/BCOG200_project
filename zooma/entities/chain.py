from dataclasses import dataclass
from zooma.entities.ball import ChainBall
from zooma.entities.path import Path
from zooma.entities.entity import Entity
from zooma.utils.vector import to_heading
from pygame.color import Color

@dataclass
class BallRecord:
    ball: ChainBall
    target_id: int

def rambow():
    hue = 0
    step = 31
    while True:
        color = Color(0)
        color.hsva = (hue, 100, 100, 100)
        yield color
        hue = (hue + step) % 360

class Chain(Entity):
    def __init__(self, path: Path, balls: list[ChainBall]):
        super().__init__()
        self.path = path
        
        self.color_gen = rambow()
        self.data: list[BallRecord] = []
        for ball in balls:
            id = len(self.data)
            self.data.append(BallRecord(ball.with_id(id).with_color(next(self.color_gen)), 0))

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
