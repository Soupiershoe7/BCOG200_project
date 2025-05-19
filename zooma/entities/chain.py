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
chain_id = 1

class Chain(Entity):
    def __init__(self, path: Path, entries: list[ChainBall | BallRecord]):
        super().__init__()
        global chain_id
        self.id = chain_id
        chain_id += 1
        
        self.path = path
        
        self.data: list[BallRecord] = []
        # TODO: playtest for speed
        self.move_speed = 0

        # Create record for each ball
        for entry in entries:
            if isinstance(entry, ChainBall):
                id = len(self.data)
                new_ball = entry.with_id(id).with_chain_id(self.id)
                record = BallRecord(new_ball, 0)
            elif isinstance(entry, BallRecord):
                record = entry
                record.ball.with_chain_id(self.id)
            self.data.append(record)

        self.pending_insertions: list[InsertionRecord] = []

    def __len__(self):
        return len(self.data)
    
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
                if not (hasattr(entity, 'shut_the_fuck_up') or hasattr(self, 'shut_the_fuck_up')):
                    print("Collision between chains", self.id, entity.id)
                return CollisionRecord(0, my_first, ChainCollisionRecord(len(entity.data) - 1, other_last))
            elif my_last.check_collision(other_first):
                if not (hasattr(entity, 'shut_the_fuck_up') or hasattr(self, 'shut_the_fuck_up')):
                    print("Collision between chains", self.id, entity.id)
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
        ball = ball.with_id(id).with_chain_id(self.id)
        new_record = BallRecord(ball, insertion_record.target_id)
        self.data.insert(insertion_record.index, new_record)
        self.pending_insertions.append(insertion_record)

    def append_chain(self, chain: "Chain"):
        global append_id
        append_id += 1
        last_ball = self.get_last_ball()
        last_ball_id = last_ball.id if last_ball else 0
        for record in chain.data:
            ball_id = last_ball_id + 1
            record.ball.with_id(ball_id).with_chain_id(self.id)
            self.data.append(record)

    def remove_ball(self, index: int):
        self.data.pop(index)

    def reverse(self, speed: float):
        self.move_speed = -speed
        for record in self.data:
            record.target_id = max(0, record.target_id - 1)

    def is_reversed(self):
        return self.move_speed < 0
    
    def draw(self, screen):
        for record in self.data:
            record.ball.draw(screen)


    def _is_pushed_by_insertion_record(self, index: int) -> bool:
        for record in self.pending_insertions:
            if record.index > index:
                return True
        return False

    def _get_insertion_record(self, index: int) -> InsertionRecord | None:
        for record in self.pending_insertions:
            if record.index == index:
                return record
        return None

    def _delete_insertion_record(self, index: int):
        for i, record in enumerate(self.pending_insertions):
            if record.index == index:
                self.pending_insertions.pop(i)
                return

    def _forward_push(self, index: int):
        for i in range(index, -1, -1):
            self._update_ball(i)

    def update(self):
        # No update if no path
        if len(self.path.points) == 0:
            return
        if self.move_speed >= 0:
            leader = self.get_first_ball()
            # print("Forward Chain: ", leader.get_label(), " -> ", self.data[0].target_id)
            for i in range(len(self.data)):
                self._update_ball(i)
        else:
            leader = self.get_last_ball()
            # print("Backward Chain: ", leader.get_label(), " -> ", self.data[-1].target_id)
            for i in range(len(self.data) - 1, -1, -1):
                self._update_ball(i)

    def _update_ball(self, index, speed: float = None):
        collided = False
        # if given speed still exists and is small, return
        if speed and speed < 0.00001:
            return
        
        record = self.data[index]
        ball = record.ball
        is_reversing = self.move_speed < 0
        
        # Get this balls target
        target = self.path.points[record.target_id]
        
        bonus_speed = 0
        can_boost = index > 0 if not is_reversing else index < len(self.data) - 1
        if can_boost:
            previous_ball_index = index - 1 if not is_reversing else index + 1
            gap = self._get_distance_between_ball(previous_ball_index, index)
            bonus_speed = gap * 0.001

        if self._is_pushed_by_insertion_record(index):
            bonus_speed += .1

        #allow behind balls to catch up to the ball in front of them
        if speed is not None:
            move_speed = speed
        else:
            move_speed = abs(self.move_speed) + bonus_speed

        #how far away is goal
        vector_to_target = target - ball.position
        distance_to_target = vector_to_target.length()
        
        #what direction is goal
        heading = to_heading(vector_to_target)
        movement_amount = min(move_speed, distance_to_target)
        
        #how much can we move 
        distance_until_collision = 0

        has_prev_ball = index > 0 if not is_reversing else index < len(self.data) - 1
        prev_ball_index = index - 1 if not is_reversing else index + 1

        if has_prev_ball: # If there is a ball in front
            prev_ball_insertion_record = self._get_insertion_record(prev_ball_index)
            prev_ball = self.data[prev_ball_index].ball

            distance_until_collision = self._get_collision_distance(index, prev_ball_index)
            
            #we are colliding
            if distance_until_collision < 0:
                heading = to_heading(prev_ball.position - ball.position)
                collided = True
                movement_amount = distance_until_collision #is negative in this case
                # The previous ball is inserting, we'll wait here
                # TODO: Figure out a cleaner way to push the ball that is in front of us
                # but has already updated.
                if prev_ball_insertion_record:
                    # TODO: forward push should only push as much as we have collision
                    movement_amount = 0
                    self._forward_push(prev_ball_index)
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
            self._update_ball(index, remaining_movement)

    def _get_collision_distance(self, first_index: int, second_index: int) -> float:
        if first_index < 0 or first_index >= len(self.data):
            return 0
        if second_index < 0 or second_index >= len(self.data):
            return 0
        
        first_record = self.data[first_index]
        second_record = self.data[second_index]

        first_ball = first_record.ball
        second_ball = second_record.ball

        return first_ball.position.distance_to(second_ball.position) - first_ball.radius - second_ball.radius

    def _advanceTarget(self, index: int):
        record = self.data[index]
        
        insertion_record = self._get_insertion_record(index)
        if insertion_record:
            follower_index = index + 1 if self.move_speed >= 0 else index - 1
            if self._get_collision_distance(index, follower_index) >= 0:
                self._delete_insertion_record(index)

        has_prev_ball = index > 0 if self.move_speed >= 0 else index < len(self.data) - 1
        prev_ball_index = index - 1 if self.move_speed >= 0 else index + 1
        
        previous_ball_target = None
        if has_prev_ball:
            previous_ball_target = self.data[prev_ball_index].target_id

        if self.move_speed >= 0:
            new_target_id = min(record.target_id + 1, len(self.path.points) - 1)
            if previous_ball_target is not None:
                new_target_id = min(new_target_id, previous_ball_target)
            record.target_id = new_target_id
        else:
            new_target_id = max(record.target_id - 1, 0)
            if previous_ball_target is not None:
                new_target_id = max(new_target_id, previous_ball_target)
            record.target_id = new_target_id

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

        