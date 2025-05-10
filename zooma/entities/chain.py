from dataclasses import dataclass
from zooma.entities.ball import ChainBall
from zooma.entities.path import Path
from zooma.entities.entity import Entity
from zooma.utils.vector import to_heading

@dataclass
class BallRecord:
    ball: ChainBall
    target_id: int

class Chain(Entity):
    def __init__(self, path: Path, balls: list[ChainBall]):
        super().__init__()
        self.path = path
        
        self.data: list[BallRecord] = []
        for ball in balls:
            self.data.append(BallRecord(ball, 0))

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
        
        self.data.append(BallRecord(ball, new_target_id))

        
    def draw(self, screen):
        for record in self.data:
            record.ball.draw(screen)

    def update(self):
        # No update if no path
        if len(self.path.points) == 0:
            return

        for i in range(len(self.data)):
            self._updateBall(i)

    def _updateBall(self, index):
        record = self.data[index]
        ball = record.ball
        
        if record.target_id >= len(self.path.points):
            record.target_id = 0
            return
        
        # Get this balls target
        target = self.path.points[record.target_id]
        
        move_speed = ball.speed

        #how far away is goal
        goal_offset = target - ball.position
        
        #what direction is goal
        heading = to_heading(goal_offset)
        
        #how much can we move
        max_distance = goal_offset.length()
         
        #move
        ball.position += heading * min(move_speed, max_distance)

        # Update target id if we've reached the target
        if max_distance < move_speed:
            record.target_id += 1
            if record.target_id >= len(self.path.points):
                record.target_id = 0
