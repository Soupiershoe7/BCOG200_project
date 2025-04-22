import pygame
import random
import sys
from pygame.locals import *

from pygame import Vector2

from zooma.entities.ball import Ball, TargetBall, MovableBall, HeldBall


WIDTH, HEIGHT = 800, 600

class ZoomaGameState:
    def __init__(self):
        self.hits = 0
        self.shots = 0
        self.spawns = 0

        self.ball_list = []
        self.target_list = []

        self.held_ball = None
        self.target_ball = None



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


        #target spawn time
        last_spawn_time = 0
        target_spawn_time = 1000 # Spawn a target every 1 seconds

        state = ZoomaGameState()
        state.held_ball = HeldBall()
        # TODO: remove ??
        state.target_ball = TargetBall(Vector2(50, 50))

        while True:
            #get the current time for ball spawn
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # TODO: make this shootBall??

                    ball_just_shot = MovableBall(state.held_ball.position)

                    state.ball_list.append(ball_just_shot)

                    state.held_ball = HeldBall()
                    state.shots += 1

            # Current ball always follows the mouse
            state.held_ball.set_position(pygame.mouse.get_pos())

            #spawn target balls
            if current_time - last_spawn_time > target_spawn_time:
                rand_x = random.randint(20, WIDTH - 20)
                rand_y = random.randint(20, HEIGHT // 2)
                target_pos = Vector2(rand_x, rand_y)

                new_target = TargetBall(target_pos)

                state.target_list.append(new_target)
                last_spawn_time = current_time
                state.spawns += 1

            # Update the balls in the list
            [b.update() for b in state.ball_list]

            # Check for out of bound balls and remove from ball_list
            def is_in_bounds(ball):
                return 0 < ball.position.x < WIDTH and 0 < ball.position.y < HEIGHT
            state.ball_list = [b for b in state.ball_list if is_in_bounds(b)]
            #state.ball_list = filter(state.ball_list, is_in_bounds)
            
            # TODO: check if ball is out of bounds

            # Check for collisions
            balls_to_remove = []
            targets_to_remove = []

            for ball in state.ball_list:
                for target in state.target_list:
                    if ball.check_collision(target):
                        balls_to_remove.append(ball)
                        targets_to_remove.append(target)
                        state.hits += 1
                        break

            # Remove the balls and targets that collided
            for ball in balls_to_remove:
                state.ball_list.remove(ball)
            for target in targets_to_remove:
                state.target_list.remove(target)

            self.updateDisplay(state)

            # Cap the frame rate
            self.clock.tick(60)

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
        for ball in state.ball_list:
            ball.draw(self.screen)

        # Draw the current ball
        state.held_ball.draw(self.screen) 

        # Draw the target balls
        for target in state.target_list:
            target.draw(self.screen)

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