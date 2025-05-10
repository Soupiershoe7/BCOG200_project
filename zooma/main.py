import pygame
import random
import sys
from pygame.locals import *

from pygame import Vector2

from zooma.entities.ball import Ball, ChainBall, TargetBall, ShotBall, HeldBall
from zooma.entities.path import Path


WIDTH, HEIGHT = 800, 600

class ZoomaGameState:
    def __init__(self):
        self.hits = 0
        self.shots = 0
        self.spawns = 0

        self.entity_list = []
        
        self.held_ball = None
        self.chain_ball = None
        self.last_spawn_time = 0

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

        # state.chain_ball = ChainBall(self._getRandomPosition())
        state.chain_ball = ChainBall(Vector2(WIDTH // 2, HEIGHT // 2))
        state.entity_list.append(state.chain_ball)
    

        while True:
            self.processInputs(state)

            self.doTasks(state)

            self.updateEntities(state)

            self.updateDisplay(state)

            # Currently capped at 60fps
            self.clock.tick(60) 

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
                elif pressed_buttons[2]:
                    self.appendChainBall(state)
            elif event.type == pygame.KEYDOWN:
                if event.key == K_p:
                    self.toggle_draw_mode(state)


        # Current ball always follows the mouse
        state.held_ball.set_position(pygame.mouse.get_pos())
        state.chain_ball.set_target(pygame.mouse.get_pos())

    def doTasks(self, state: ZoomaGameState):
        current_time = pygame.time.get_ticks()
        if current_time - state.last_spawn_time > TARGET_SPAWN_INTERVAL:
            self.spawnTarget(state)
        if state.draw_mode:
            state.path.addPoint(pygame.mouse.get_pos())


    def updateEntities(self, state: ZoomaGameState):
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

    def appendChainBall(self, state: ZoomaGameState):
        new_chain_ball = ChainBall(self._getRandomPosition())
        state.entity_list.append(new_chain_ball)

        # Append the new chain ball to the chain
        append_at = state.chain_ball
        while append_at.behind is not None:
            append_at = append_at.behind

        append_at.append(new_chain_ball)


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
            can_collide = isinstance(entity, ShotBall) or isinstance(entity, ChainBall)
            if can_collide:
                # Check for collisions with other balls
                for other in state.entity_list:
                    if entity != other and isinstance(other, TargetBall):
                        if entity.check_collision(other):
                            to_remove.add(other)
                            if isinstance(entity, ShotBall):
                                to_remove.add(entity)
                            state.hits += 1

        
        for remove in to_remove:
            if remove in state.entity_list:
                state.entity_list.remove(remove)

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


    def drawStatusDisplay(self, state: ZoomaGameState):
        # Draw the score
        if state.shots == 0:
            accuracy = 0
        else:
            accuracy = state.hits / state.shots
        score_text = self.font.render(f"Hits: {state.hits} Shots: {state.shots} Spawns: {state.spawns} Accuracy: {accuracy:.2f}", True, Color('white'))
        self.screen.blit(score_text, (10, 10)) # Draw the score at the top left corner


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