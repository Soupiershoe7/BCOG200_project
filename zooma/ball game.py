import pygame
import sys
from pygame import Color
import random

pygame.init()
pygame.font.init() #initialize the font module
font = pygame.font.Font(None, 36) #set the font for the text

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT)) #set the dimensions of the window
pygame.display.set_caption("Simple Pygame Window") #set the title of the window

clock = pygame.time.Clock() #create a clock object to control the frame rate

class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.velocity = 0
        self.shooting = False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def update(self):
        if self.shooting:
            self.y -= self.velocity # Move the ball up
            if self.y < 0:
                return False
            return True
        
    def check_collision(self, other_ball):
        distance = ((self.x - other_ball.x) ** 2 + (self.y - other_ball.y) ** 2) ** 0.5
        return distance < self.radius + other_ball.radius
                
ball_list = [] # List to hold the balls
target_list = [] # List to hold the target balls

#target spawn time
last_spawn_time = 0
target_spawn_time = 1000 # Spawn a target every 1 seconds

# Create a ball
current_ball = Ball(0, 0, 20, Color('red'))
# Create a target ball
target_ball = Ball(50, 50, 20, Color('red'))

hits = 0
shots = 0
spawns = 0

while True:
    #get the current time for ball spawn
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            current_ball.shooting = True
            current_ball.velocity = 10
            ball_list.append(current_ball)
            current_ball = Ball(0, 0, 20, Color('red'))
            shots += 1

    # Update the current ball's position to the mouse position
    if not current_ball.shooting:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        current_ball.x = mouse_x
        current_ball.y = mouse_y

    #spawn target balls
    if current_time - last_spawn_time > target_spawn_time:
        target_x = random.randint(20, WIDTH - 20)
        target_y = random.randint(20, HEIGHT // 2)
        new_target = Ball(target_x, target_y, 20, Color('blue'))
        target_list.append(new_target)
        last_spawn_time = current_time
        spawns += 1

    # Update the balls in the list
    ball_list = [ball for ball in ball_list if ball.update()]

    # Check for collisions
    balls_to_remove = []
    targets_to_remove = []

    for ball in ball_list:
        for target in target_list:
            if ball.check_collision(target):
                balls_to_remove.append(ball)
                targets_to_remove.append(target)
                hits += 1
                break

    # Remove the balls and targets that collided
    for ball in balls_to_remove:
        ball_list.remove(ball)
    for target in targets_to_remove:
        target_list.remove(target)

    # clear the screen
    screen.fill(Color('black')) 

    # Draw all the balls
    for ball in ball_list:
        ball.draw(screen)

    # Draw the current ball
    current_ball.draw(screen) 

    # Draw the target balls
    for target in target_list:
        target.draw(screen)
        
    # Draw the score
    if shots == 0:
        accuracy = 0
    else:
        accuracy = hits / shots
    score_text = font.render(f"Hits: {hits} Shots: {shots} Spawns: {spawns} Accuracy: {accuracy:.2f}", True, Color('white'))
    screen.blit(score_text, (10, 10)) # Draw the score at the top left corner


    # Update the display
    pygame.display.flip() 

    # Cap the frame rate
    clock.tick(60)

