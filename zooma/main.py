import pygame
import random
import sys
from pygame.locals import *

from pygame import Vector2

from zooma.entities.entity import Entity
from zooma.entities.ball import Ball, ChainBall, TargetBall, ShotBall, HeldBall
from zooma.entities.path import Path
from zooma.entities.chain import Chain
from zooma.entities.emitter import Emitter
from zooma.entities.deathHole import DeathHole
from zooma.utils.colors import LevelColors

WIDTH, HEIGHT = 800, 600


class ZoomaGameState:
    def __init__(self):
        self.hits = 0
        self.shots = 0
        self.spawns = 0
        self.score = 0
        self.progress_percent = 0
        self.chain_count = 0
        self.combo_mult = 1

        self.entity_list = []
        self.emitter: Emitter = None
        self.death_hole: DeathHole = None
        
        self.held_ball: HeldBall = None
        self.chain: Chain = None
        self.last_spawn_time = 0

        self.paused = False
        self.draw_mode = False
        self.path: Path = None

        self.level_colors: LevelColors = LevelColors(4)

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
        state.held_ball = HeldBall(state.level_colors.get_color())
        state.path = Path([])
        state.entity_list.append(state.path)

        self.reset_game(state)

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
                if event.key == K_d:
                    self.toggle_draw_mode(state)
                elif event.key == K_p:
                    state.paused = not state.paused
                elif event.key == K_SPACE:
                    self.swap_held_ball(state)
                elif event.key == K_r:
                    self.reset_game(state)
                elif event.key == K_a:
                    ball = ChainBall(Vector2(WIDTH // 2, HEIGHT // 2), state.level_colors.get_color())
                    chain = Chain(state.path, [ball])
                    chain.move_speed = random.uniform(2.4, 2.8)
                    state.entity_list.append(chain)
                elif event.key in (K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9):
                    self.split_chain(state, event.key)


        # Current ball always follows the mouse
        state.held_ball.set_position(pygame.mouse.get_pos())
        # state.chain_ball.set_target(pygame.mouse.get_pos())

    def doTasks(self, state: ZoomaGameState):
        current_time = pygame.time.get_ticks()
        if current_time - state.last_spawn_time > TARGET_SPAWN_INTERVAL:
            # self.spawnTarget(state)
            pass
        if state.draw_mode:
            new_point = pygame.mouse.get_pos()
            
            was_empty = len(state.path.points) == 0
            state.path.addPoint(new_point)

            # Creating first point in path
            if was_empty:
                state.emitter = Emitter(new_point, state.level_colors)
                state.entity_list.append(state.emitter)

        self.try_to_emit_chain(state)

        if state.emitter is not None and state.emitter.is_active() and state.progress_percent >= 1:
            state.emitter.deactivate()
            print("ZOOMA!")
                

    def try_to_emit_chain(self, state: ZoomaGameState):
        emitter = state.emitter
        if emitter is None or not emitter.is_active():
            return

        for entity in state.entity_list:
            if isinstance(entity, Chain) and emitter.check_collision(entity):
                return
        
        new_ball = ChainBall(emitter.position, emitter.get_color())
        chain = Chain(state.path, [new_ball])
        chain.mode_speed = 2
        state.entity_list.append(chain)

    def split_chain(self, state: ZoomaGameState, key: int):
        index = key - K_1 + 1
        print(f"split at {index}")

        first_chain = None
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                first_chain = entity
                break

        if first_chain is None:
            return

        new_chain = first_chain.split(index)
        if new_chain is not None:
            state.entity_list.append(new_chain)
            

    def reset_game(self, state: ZoomaGameState):
        to_remove = []
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                to_remove.append(entity)
        
        for entity in to_remove:
            state.entity_list.remove(entity)

        state.score = 0
        state.progress_percent = 0
        state.chain_count = 0
        state.combo_mult = 1

        if state.emitter is not None:
            state.emitter.activate()


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
            state.death_hole = DeathHole(state.path.points[-1])
            state.entity_list.append(state.death_hole)
        else:
            state.draw_mode = True
            state.path.clear()
            # remove emitter
            if state.emitter != None and state.emitter in state.entity_list:
                state.entity_list.remove(state.emitter)
                state.emitter = None
            if state.death_hole != None and state.death_hole in state.entity_list:
                state.entity_list.remove(state.death_hole)
                state.death_hole = None


    def spawnTarget(self, state: ZoomaGameState):
        target_pos = self._getRandomPosition(True)

        new_target = TargetBall(target_pos)

        state.entity_list.append(new_target)
        state.last_spawn_time = pygame.time.get_ticks()
        state.spawns += 1

    def shootBall(self, state: ZoomaGameState):
        """ Shoot the held ball """
        ball_just_shot = ShotBall(state.held_ball.position, state.held_ball.color)

        state.entity_list.append(ball_just_shot)

        state.held_ball = HeldBall(state.level_colors.get_color())
        
        state.shots += 1

    def swap_held_ball(self, state: ZoomaGameState): 
        # TODO: make swap ball actually swap
        state.held_ball = HeldBall(state.level_colors.get_color())

    def checkOutOfBounds(self, state: ZoomaGameState):
        """ Check for out of bound balls and remove from ball_list """
        def is_in_bounds(ball):
            return 0 < ball.position.x < WIDTH and 0 < ball.position.y < HEIGHT
        
        # Remove Movable balls that are out of bounds
        for entity in state.entity_list:
            if isinstance(entity, ShotBall):
                if not is_in_bounds(entity):
                    state.entity_list.remove(entity)
                    state.chain_count = 0

    def checkCollisions(self, state: ZoomaGameState):
        """ Check for collisions between balls and targets """
        to_remove = set()

        # Do Death first
        for entity in state.entity_list:
            if isinstance(entity, DeathHole):
                for other in state.entity_list:
                    if isinstance(other, Chain) and entity.check_collision(other):
                        other.remove_ball(0)
                        if len(other.data) == 0:
                            to_remove.add(other)

        for remove in to_remove:
            if remove in state.entity_list:
                state.entity_list.remove(remove)

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
            collision_record = entity.check_collision(shot_ball)
            if not collision_record:
                return False
                
            insertion_record = entity.get_insertion_point(shot_ball)


            match_count = 1
            match_list = []
            index = insertion_record.index
            while True:
                ball = entity.get_ball(index)
                if ball is None or ball.color != shot_ball.color:
                    break
                match_count += 1
                match_list.append(index)
                index += 1

            index = insertion_record.index - 1
            while True:
                ball = entity.get_ball(index)
                if ball is None or ball.color != shot_ball.color:
                    break
                match_count += 1
                match_list.append(index)
                index -= 1
            
            if match_count < 3:
                new_ball = ChainBall(shot_ball.position, shot_ball.color)
                entity.insert_ball(new_ball, insertion_record)
                state.chain_count = 0
            else:
                # remove balls
                match_list.sort(reverse=True)
                for index in match_list:
                    entity.remove_ball(index)
                new_entity = entity.split(match_list[-1])
                if new_entity is not None:
                    state.entity_list.append(new_entity)
                if len(entity.data) == 0:
                    state.entity_list.remove(entity)
                    
                #calculate score
                state.chain_count += 1
                chain_mult = max(1, state.chain_count - 3)
                shot_score = match_count * 10 * state.combo_mult * chain_mult 
                state.score += shot_score
                state.progress_percent += shot_score / 1500
                print(f"shot: Balls {match_count}, Combo {state.combo_mult}, Chain {state.chain_count} = {shot_score}")

            
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
            chain2.append_chain(chain1)
            state.entity_list.remove(chain1)
        else:
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

    def draw_progress_bar(self, screen: pygame.Surface, state: ZoomaGameState, pos: tuple[int, int]):
        width = 200
        height = 20

        if isinstance(pos, tuple):
            pos = Vector2(pos)
        
        bg_rect = pygame.Rect(pos.x, pos.y, width, height)
        fill_rect = pygame.Rect(pos.x, pos.y, min(width * state.progress_percent, width), height)
        
        pygame.draw.rect(screen, Color('yellow'), bg_rect)
        pygame.draw.rect(screen, Color('green'), fill_rect)
    
    def drawStatusDisplay(self, state: ZoomaGameState):
        # Draw the score
        if state.shots == 0:
            accuracy = 0
        else:
            accuracy = state.hits / state.shots
        self.draw_text(self.screen, f"Score: {state.score}", (180, 10))
        self.draw_progress_bar(self.screen, state, (420, 10))

    



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