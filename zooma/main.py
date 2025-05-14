import pygame
import random
import sys
from pygame.locals import *

from pygame import Vector2

from zooma.entities.entity import Entity
from zooma.entities.ball import Ball, ChainBall, TargetBall, ShotBall, HeldBall
from zooma.entities.path import Path
from zooma.entities.chain import Chain

WIDTH, HEIGHT = 800, 600


class ZoomaGameState:
    def __init__(self):
        self.hits = 0
        self.shots = 0
        self.spawns = 0

        self.entity_list = []
        
        self.held_ball: HeldBall = None
        self.chain: Chain = None
        self.last_spawn_time = 0

        self.paused = False
        self.draw_mode = False
        self.path: Path = None

# Spawn a target every 1 second.
TARGET_SPAWN_INTERVAL = 1000

class ZoomaGame:
    def __init__(self):
        """ Initialize game state"""
        # Set up the display
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT)) #set the dimensions of the window
        #create a clock object to control the frame rate
        self.clock = pygame.time.Clock() 

        self.font = pygame.font.Font(None, 36) #set the font for the text

    def run(self):
        """ Run the game loop """

        state = ZoomaGameState()
        state.held_ball = HeldBall()
        state.path = Path([])
        state.entity_list.append(state.path)

        self._reset_chain(state)

        while True:
            self.processInputs(state)

            self.doTasks(state)

            self.updateEntities(state)

            self.updateDisplay(state)

            # Currently capped at 60fps
            self.clock.tick(120) 

    def processInputs(self, state: ZoomaGameState):
        """ Process user inputs """
        for event in pygame.event.get():
            # print(f"Got event: {event}")
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pressed_buttons = pygame.mouse.get_pressed()
                if pressed_buttons[0]:
                    self.shootBall(state)
            elif event.type == pygame.KEYDOWN:
                if event.key == K_p:
                    self.toggle_draw_mode(state)
                elif event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()  
                elif event.key == K_SPACE:
                    state.paused = not state.paused
                elif event.key == K_r:
                    self._reset_chain(state)


        # Current ball always follows the mouse
        state.held_ball.set_position(pygame.mouse.get_pos())
        # state.chain_ball.set_target(pygame.mouse.get_pos())

    def doTasks(self, state: ZoomaGameState):
        current_time = pygame.time.get_ticks()
        if current_time - state.last_spawn_time > TARGET_SPAWN_INTERVAL:
            # self.spawnTarget(state)
            pass
        if state.draw_mode:
            state.path.addPoint(pygame.mouse.get_pos())

    def _reset_chain(self, state: ZoomaGameState):
        to_remove = []
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                to_remove.append(entity)
        
        for entity in to_remove:
            state.entity_list.remove(entity)
        
        # Create chain 1
        ball = ChainBall(Vector2(WIDTH // 2, HEIGHT // 2))
        chain = Chain(state.path, [ball])
        chain.move_speed = 2.3
        state.entity_list.append(chain)

        # Create chain 2
        ball = ChainBall(Vector2(0, 0))
        chain = Chain(state.path, [ball])
        state.entity_list.append(chain)

    def updateEntities(self, state: ZoomaGameState):
        if state.paused:
            return
        # Update all the balls
        for entity in state.entity_list:
            entity.update()

        # Cleanup out of bound balls
        self.checkOutOfBounds(state)

        # Check for collisions
        self.checkCollisions(state)

    def _getRandomPosition(self, top_half_only: bool = False):
        """ Get a random position on the screen """
        rand_x = random.randint(20, WIDTH - 20)
        if top_half_only:
            rand_y = random.randint(20, HEIGHT // 2)
        else:
            rand_y = random.randint(20, HEIGHT - 20)

        return Vector2(rand_x, rand_y)

    def toggle_draw_mode(self, state: ZoomaGameState):
        if state.draw_mode:
            state.draw_mode = False
        else:
            state.draw_mode = True
            state.path.clear()


    def spawnTarget(self, state: ZoomaGameState):
        target_pos = self._getRandomPosition(True)

        new_target = TargetBall(target_pos)

        state.entity_list.append(new_target)
        state.last_spawn_time = pygame.time.get_ticks()
        state.spawns += 1

    def shootBall(self, state: ZoomaGameState):
        """ Shoot the held ball """
        ball_just_shot = ShotBall(state.held_ball.position)

        state.entity_list.append(ball_just_shot)

        state.held_ball = HeldBall()
        
        state.shots += 1


    def checkOutOfBounds(self, state: ZoomaGameState):
        """ Check for out of bound balls and remove from ball_list """
        def is_in_bounds(ball):
            return 0 < ball.position.x < WIDTH and 0 < ball.position.y < HEIGHT
        
        # Remove Movable balls that are out of bounds
        for entity in state.entity_list:
            if isinstance(entity, ShotBall):
                if not is_in_bounds(entity):
                    state.entity_list.remove(entity)

    def checkCollisions(self, state: ZoomaGameState):
        """ Check for collisions between balls and targets """
        to_remove = set()

        for entity in state.entity_list:
            can_collide = isinstance(entity, ShotBall) or isinstance(entity, Chain)
            if can_collide:
                # Check for collisions with other balls
                for other in state.entity_list:
                    if entity == other:
                        continue

                    if isinstance(entity, ShotBall) and isinstance(other, Chain):
                        collision = self.checkShotBallCollision(state, entity, other)
                        if collision:
                            to_remove.add(entity)
                    elif isinstance(entity, Chain) and isinstance(other, Chain):
                        collision = self.checkChainCollision(state, entity, other)
        
        for remove in to_remove:
            if remove in state.entity_list:
                state.entity_list.remove(remove)

    def checkShotBallCollision(self, state: ZoomaGameState, shot_ball: ShotBall, entity: Entity):
        if isinstance(entity, Chain):
            #TODO check if collision ball color matches entity
            collision_record = entity.check_collision(shot_ball)
            if not collision_record:
                return False

            insertion_record = entity.get_insertion_point(shot_ball)

            new_ball = ChainBall(shot_ball.position)
            entity.insert_ball(new_ball, insertion_record)
            return True
        else:
            print("Unhandled Collision with non-chain entity")
    
        return False

    def checkChainCollision(self, state: ZoomaGameState, chain1: Chain, chain2: Chain):
        collision_record = chain1.check_collision(chain2)
        if not collision_record:
            return False
        
        chain1_target_id = chain1.get_target_id()
        chain2_target_id = chain2.get_target_id()
        
        if chain1_target_id < chain2_target_id:
            print("Appending chain 1 to chain 2", collision_record)
            chain2.append_chain(chain1)
            state.entity_list.remove(chain1)
        else:
            print("Appending chain 2 to chain 1", collision_record)
            chain1.append_chain(chain2)
            state.entity_list.remove(chain2)

        
        return False
        

    def updateDisplay(self, state: ZoomaGameState):
        """ all the draws of python objects should occur here"""
        
        # clear the screen
        self.screen.fill(Color('black'))

        self.drawBalls(state)
        self.drawStatusDisplay(state)

        # Update the display
        pygame.display.flip()

    def drawBalls(self, state: ZoomaGameState):
        # Draw all the balls
        for entity in state.entity_list:
            entity.draw(self.screen)

        # Held ball is still a special baby.
        state.held_ball.draw(self.screen)

    def draw_text(self, screen: pygame.Surface, text: str, pos: tuple[int, int]):
        text_surface = self.font.render(text, True, Color('white'))
        screen.blit(text_surface, pos)
    
    def drawStatusDisplay(self, state: ZoomaGameState):
        # Draw the score
        if state.shots == 0:
            accuracy = 0
        else:
            accuracy = state.hits / state.shots
        self.draw_text(self.screen, f"Hits: {state.hits} Shots: {state.shots} Spawns: {state.spawns} Accuracy: {accuracy:.2f}", (10, 10))
        self.draw_text(self.screen, "Press p to pause", (10, 40))
        self.draw_text(self.screen, "Press ESC to quit", (10, 100))
        self.draw_text(self.screen, "Press d to toggle draw mode", (10, 130))


def main():

    pygame.init()
    pygame.font.init() #initialize the font module

    pygame.display.set_caption("Simple Pygame Window") #set the title of the window


    print("Welcome to Zooma! This is a Zuma clone game.")

    game = ZoomaGame()
    game.run()    
    while True:
        checkInputs()
        updateObjects()
        drawObjects()
        flip()
        tick()

if __name__ == "__main__":
    main()