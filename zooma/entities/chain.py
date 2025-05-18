from dataclasses import dataclass
from pygame.math import Vector2

from zooma.entities.entity import Entity
from zooma.entities.ball import ChainBall, Ball, ShotBall
from zooma.entities.path import Path

from zooma.utils.vector import to_heading
from zooma.utils.distance import get_distance_between

@dataclass
class BallRecord:
    ball: ChainBall
    target_id: int

@dataclass
class InsertionRecord:
    index: int
    target_id: int

@dataclass
class ChainCollisionRecord:
    index: int
    ball: ChainBall
    
@dataclass
class CollisionRecord:
    index: int
    ball: Ball
    other: ShotBall | ChainCollisionRecord

append_id = 1

class Chain(Entity):
    def __init__(self, path: Path, balls: list[ChainBall | BallRecord]):
        super().__init__()
        self.path = path
        
        self.data: list[BallRecord] = []
        # TODO: playtest for speed
        self.move_speed = 0

        # Create record for each ball
        for ball in balls:
            if isinstance(ball, ChainBall):
                id = len(self.data)
                new_ball = ball.with_id(id)
                record = BallRecord(new_ball, 0)
            elif isinstance(ball, BallRecord):
                record = ball
            self.data.append(record)

    def check_collision(self, entity: Entity) -> CollisionRecord | None:
        if isinstance(entity, Ball):
            for i, record in enumerate(self.data):
                if record.ball.check_collision(entity):
                    return CollisionRecord(i, record.ball, entity)
        elif isinstance(entity, Chain):
            other_first = entity.data[0].ball
            other_last = entity.data[-1].ball
            my_first = self.data[0].ball
            my_last = self.data[-1].ball

            if my_first.check_collision(other_last):
                return CollisionRecord(0, my_first, ChainCollisionRecord(len(entity.data) - 1, other_last))
            elif my_last.check_collision(other_first):
                return CollisionRecord(len(self.data) - 1, my_last, ChainCollisionRecord(0, other_first))
                
        return None

    def get_target_id(self) -> int:
        return self.data[0].target_id

    def get_last_ball(self) -> ChainBall:
        return self.data[-1].ball

    def get_first_ball(self) -> ChainBall:
        return self.data[0].ball

    def get_ball(self, index: int) -> ChainBall:
        if index >= len(self.data) or index < 0:
            return None
        return self.data[index].ball

    def split(self, index: int) -> "Chain":
        if (index >= len(self.data)):
            print(f"Cannot split chain at index {index} because chain has {len(self.data)} balls")
            return None
        
        print("Splitting chain at index", index)
        print("Chain Before: ", [record.ball.id for record in self.data])
        new_chain = Chain(self.path, self.data[index:])
        self.data = self.data[:index]

        return new_chain
        
        
    def get_insertion_point(self, ball: Ball) -> InsertionRecord | None:
        #whichever segment has the dot product between 0 and 1 is the nearest segment
        #return the index of the nearest segment
    
        #check if the ball is colliding with the chain
        collision_record = self.check_collision(ball)
        
        if not collision_record:
            return None

        

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
            return InsertionRecord(collision_record.index, 0)
        
        impact_vector = (collision_record.ball.position - ball.position)
        alignment = impact_vector.dot(path_segment_vector)

        if_after = alignment > 0
        insertion_index = collision_record.index + (1 if if_after else 0)

        target_id = self._compute_target_id(insertion_index)

        return InsertionRecord(insertion_index, target_id)

    def _compute_target_id(self, index: int) -> int:
        if index >= len(self.data):
            index = len(self.data) - 1
        record = self.data[index]
        return record.target_id

    def insert_ball(self, ball: ChainBall, insertion_record: InsertionRecord):
        id = 0
        ball = ball.with_id(id)
        new_record = BallRecord(ball, insertion_record.target_id)
        self.data.insert(insertion_record.index, new_record)

    def append_chain(self, chain: "Chain"):
        global append_id
        append_id += 1
        last_ball = self.get_last_ball()
        last_ball_id = last_ball.id if last_ball else 0
        for record in chain.data:
            ball_id = last_ball_id + 1
            record.ball.with_id(ball_id)
            print(f"[{append_id}] Append Ball: at {record.target_id}")
            self.data.append(record)

    def remove_ball(self, index: int):
        self.data.pop(index)

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
        
        bonus_speed = 0
        if index > 0:
            gap = self._get_distance_between_ball(index - 1, index)
            bonus_speed = gap * 0.001

        #allow behind balls to catch up to the ball in front of them
        move_speed = speed if speed is not None else self.move_speed + bonus_speed

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
            self._advanceTarget(index)
            
        remaining_movement = move_speed - movement_amount
        if remaining_movement > 0.001 and not collided and movement_amount > 0.001:
            # Try Again
            self._updateBall(index, remaining_movement)

    def _advanceTarget(self, index: int):
        record = self.data[index]

        #suggested by copilot to detect when a ball passes another ball (when the path is a loop)
        def distance_modN(a: int, b: int, n: int) -> int: 
            return (b - a) % n

        previous_ball_target = None
        if index > 0:
            previous_ball_target = self.data[index - 1].target_id

        new_id = (record.target_id + 1) % len(self.path.points)
        if previous_ball_target is None:
            record.target_id = new_id
            return

        distance = distance_modN(new_id, previous_ball_target, len(self.path.points))
        limit = (len(self.path.points) - 1) * .9
            
        if distance < limit:
            record.target_id = new_id

    def _get_distance_between_ball(self, first_id: int, second_id: int) -> int:
        first_record = self.data[first_id]
        second_record = self.data[second_id]

        first_ball = first_record.ball
        first_target = first_record.target_id
        first_radius = first_ball.radius
        second_ball = second_record.ball
        second_target = second_record.target_id
        second_radius = second_ball.radius

        path_length = 0
        index = first_target
        while index != second_target:
            a = self.path.points[index]
            b = self.path.points[(index + 1) % len(self.path.points)]
            path_length += a.distance_to(b)
            index = (index + 1) % len(self.path.points)
            
        first_distance = first_ball.position.distance_to(self.path.points[first_target])
        second_distance = second_ball.position.distance_to(self.path.points[second_target])

        return path_length + first_distance - second_distance - first_radius - second_radius

    def _get_distance_between_target(self, first_id: int, second_id: int) -> int:
        path_length = 0
        index = first_id
        while index != second_id:
            a = self.path.points[index]
            b = self.path.points[(index + 1) % len(self.path.points)]
            path_length += a.distance_to(b)
            index = (index + 1) % len(self.path.points)
        return path_length
        