import json
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
from zooma.entities.forg import Forg

WIDTH, HEIGHT = 1000, 800


class ZoomaGameState:
    def __init__(self):
        self.current_level = 0
        self.level_name = ""

        self.hits = 0
        self.shots = 0
        self.spawns = 0
        self.score = 0
        self.progress_percent = 0
        self.chain_count = 0
        self.combo_mult = 1

        self.entity_list = []
        self.forg: Forg = None

        self.paused = True
        self.draw_mode = False
        self.path: Path = None
        self.last_message = ""
        self.base_chain_speed = 0.5
        self.did_zooma = False
        self.game_over = False

        self.difficulty = 6
        self.level_colors: LevelColors = LevelColors(self.difficulty)


class ZoomaGame:
    def __init__(self):
        """ Initialize game state"""

        pygame.init()
        pygame.font.init() #initialize the font module
        pygame.mixer.init()

        pygame.display.set_caption("Zooma (not quite deluxe)") #set the title of the window

        # Set up the display
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT)) #set the dimensions of the window
        #create a clock object to control the frame rate
        self.clock = pygame.time.Clock() 

        self.font = pygame.font.Font(None, 36) #set the font for the text

        self.zooma_sound = pygame.mixer.Sound("zooma/sounds/zooma.wav")
        self.data = None

        self.state: ZoomaGameState = None
        

    def run(self):
        """ Run the game loop """

        self.init_game()

        self.state = self.load_level(self.state.current_level, self.state)

        self.start_level(self.state)

        while True:
            self.process_inputs(self.state)

            self.do_tasks(self.state)

            self.update_entities(self.state)

            self.update_display(self.state)

            # Currently capped at 120fps
            self.clock.tick(120) 

    def init_game(self):
        with open("zooma/levels/levels.json", "r") as f:
            data = json.load(f)

        self.data = data

        self.state = ZoomaGameState()
        
    def load_level(self, level: int, state: ZoomaGameState) -> ZoomaGameState:
        try:
            level_data = self.data["levels"][level]

            state.difficulty = level_data["difficulty"]
            state.level_colors = LevelColors(state.difficulty)

            state.level_name = level_data["name"]
            
            # Reset level data
            state.paused = True
            state.chain_count = 0
            state.combo_mult = 1
            state.progress_percent = 0
            state.did_zooma = False
            state.last_message = ""

            # Clear entities
            state.entity_list.clear()

            # Load Level Entities
            map_name = level_data["map"]
            with open(f"zooma/levels/{map_name}", "r") as f:
                map_data = json.load(f)

            for path_obj in map_data["paths"]:
                points = path_obj["points"]
                if len(points) < 2:
                    print("Level map has invalid path")
                    continue

                path = Path(points)
                state.path = path
                state.entity_list.append(path)

                start_point = points[0]
                end_point = points[-1]
                
                emitter = Emitter(Vector2(start_point), state.level_colors)
                state.entity_list.append(emitter)

                death_hole = DeathHole(Vector2(end_point))
                state.entity_list.append(death_hole)

            forg_data = map_data["turret"]
            forg = Forg(Vector2(forg_data["position"]), state.level_colors)
            state.forg = forg
            state.entity_list.append(forg)
        except Exception as e:
            print(f"Failed to load level {level}: {e}")
            return None
        
        return state
    
    def start_level(self, state: ZoomaGameState):
        state.paused = False
        state.forg.reset()
        for entity in state.entity_list:
            if isinstance(entity, Emitter):
                entity.activate()

    def end_level(self, state: ZoomaGameState):
        #add prompt
        state.paused = True
        state.last_message = "Level Complete!"
        
    def advance_level(self, state: ZoomaGameState):
        state.paused = True

        next_level = state.current_level + 1

        if next_level >= len(self.data["levels"]):
            print("You win!")
            return

        print("Advancing to level", next_level + 1)
        state.current_level += 1

        self.state = self.load_level(state.current_level, state)

        self.start_level(self.state)

    def end_game(self, state: ZoomaGameState, failure: bool = False):
        if state.game_over:
            return
        
        state.game_over = True
        print("Game Over")
        # play a sound?

        if failure:
            # self.death_sound.play()
            for entity in state.entity_list:
                if isinstance(entity, Emitter):
                    entity.deactivate()
            state.forg.die()
        else:
            # self.win_sound.play()
            self.end_level(state)

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
        state.did_zooma = False
        state.game_over = False
        state.level_colors.set_difficulty(state.difficulty)
        state.forg.reset()

        for entity in state.entity_list:
            if isinstance(entity, Emitter):
                entity.activate()

    def process_inputs(self, state: ZoomaGameState):
        """ Process user inputs """
        for event in pygame.event.get():
            # print(f"Got event: {event}")
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pressed_buttons = pygame.mouse.get_pressed()
                if pressed_buttons[0]:
                    self.shoot_ball(state)
            elif event.type == pygame.KEYDOWN:
                # exit game
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                # toggle draw mode
                if event.key == K_d: 
                    self.toggle_draw_mode(state)
                
                # toggle pause
                elif event.key == K_p: 
                    state.paused = not state.paused

                # advance level
                elif event.key == K_n: 
                    self.advance_level(state)

                # swap held ball
                elif event.key == K_SPACE: 
                    self.swap_held_ball(state)
                
                # reset game
                elif event.key == K_r: 
                    self.reset_game(state)
                
                # split at i
                elif event.key in (K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9): 
                    self.split_chain(state, event.key)

                # change chain speed
                elif event.key in (K_0, K_MINUS, K_EQUALS):
                    if event.key == K_0:
                        state.base_chain_speed = 0.5
                    elif event.key == K_MINUS:
                        state.base_chain_speed -= 0.05
                    elif event.key == K_EQUALS:
                        state.base_chain_speed += 0.05

        # Current ball always follows the mouse
        state.forg.set_heading(Vector2(pygame.mouse.get_pos()))

    def do_tasks(self, state: ZoomaGameState):
        self.task_check_win(state)
        self.task_draw_mode(state)
        self.task_emit_chain(state)
        self.task_motivate_chains(state)
        self.task_check_colors(state)

    def task_check_win(self, state: ZoomaGameState):
        if not state.did_zooma:
            return

        ball_count = 0
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                ball_count += len(entity.data)

        if ball_count == 0:
            self.end_level(state)

    def task_draw_mode(self, state: ZoomaGameState):
        # add points to drawing
        if state.draw_mode:
            new_point = pygame.mouse.get_pos()
            
            was_empty = len(state.path.points) == 0
            state.path.addPoint(new_point)

            # Creating first point in path
            if was_empty:
                emitter = Emitter(new_point, state.level_colors)
                state.entity_list.append(emitter)

    def task_emit_chain(self, state: ZoomaGameState):
        self.try_to_emit_chain(state)

        if state.progress_percent >= 1 and not state.did_zooma:
            state.did_zooma = True
            self.zooma_sound.play()

            # Disable emitters
            for entity in state.entity_list:
                if isinstance(entity, Emitter):
                    entity.deactivate()

    def try_to_emit_chain(self, state: ZoomaGameState):
        for entity in state.entity_list:
            if isinstance(entity, Emitter):
                emitter = entity
                
                if not emitter.is_active():
                    continue

                can_emit = True
                for entity in state.entity_list:
                    # emitter blocked
                    if isinstance(entity, Chain) and emitter.check_collision(entity):
                        can_emit = False
                        break
                
                if can_emit:
                    new_ball = ChainBall(emitter.position, emitter.get_color())
                    chain = Chain(state.path, [new_ball])
                    chain.shut_the_fuck_up = True
                    state.entity_list.append(chain)

    def task_motivate_chains(self, state: ZoomaGameState):
        pusher_chain = None
        distance_to_start = float('inf')

        for entity in state.entity_list:
            if isinstance(entity, Chain):
                if state.game_over:
                    entity.move_speed = state.base_chain_speed * 10
                else:
                    first_ball = entity.get_first_ball()
                    d = state.path.distance_between_point_and_position(0, first_ball.position)
                    if d < distance_to_start:
                        distance_to_start = d
                        pusher_chain = entity
        
        if not state.game_over and pusher_chain is not None:
            pusher_chain.move_speed = state.base_chain_speed

    def task_check_colors(self, state: ZoomaGameState):
        if not state.did_zooma:
            return

        colors = set()
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                chain = entity
                for i in range(len(chain)):
                    ball = chain.get_ball(i)
                    if ball:
                        color_tuple = tuple(ball.color)
                        colors.add(color_tuple)

        if len(colors) > 0:
            state.level_colors.set_colors([Color(c) for c in colors])

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
            print("special split move speed lost motivations", first_chain.get_first_ball().id)
            first_chain.move_speed = 0
            


    def update_entities(self, state: ZoomaGameState):
        if state.paused:
            return

        # Update all the balls
        for entity in state.entity_list:
            entity.update()

        # Cleanup out of bound balls
        self.check_out_of_bounds(state)

        # Check for collisions
        self.check_collisions(state)

    def _get_random_position(self, top_half_only: bool = False):
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

            death_hole = DeathHole(state.path.points[-1])
            state.entity_list.append(death_hole)

            # Start game
            state.paused = False
        else:
            state.draw_mode = True
            state.paused = True
            state.path.clear()

            to_remove = []
            # remove emitter and death hole
            for entity in state.entity_list:
                if isinstance(entity, DeathHole):
                    to_remove.append(entity)
                elif isinstance(entity, Emitter):
                    to_remove.append(entity)
            
            for entity in to_remove:
                state.entity_list.remove(entity)

            self.reset_game(state)

    def shoot_ball(self, state: ZoomaGameState):
        """ Shoot the held ball """
        ball_just_shot = state.forg.shoot()
        if ball_just_shot is None:
            return
        state.entity_list.append(ball_just_shot)

        state.shots += 1

    def swap_held_ball(self, state: ZoomaGameState): 
        state.forg.swap_ball()

    def check_out_of_bounds(self, state: ZoomaGameState):
        """ Check for out of bound balls and remove from ball_list """
        def is_in_bounds(ball):
            return 0 < ball.position.x < WIDTH and 0 < ball.position.y < HEIGHT
        
        # Remove Movable balls that are out of bounds
        for entity in state.entity_list:
            if isinstance(entity, ShotBall):
                if not is_in_bounds(entity):
                    state.entity_list.remove(entity)
                    state.chain_count = 0

    def check_collisions(self, state: ZoomaGameState):
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

                        if not state.game_over:
                            self.end_game(state, failure=True)

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
                        collision = self.check_shot_ball_collision(state, entity, other)
                        if collision:
                            to_remove.add(entity)
                            break
                        
                    elif isinstance(entity, Chain) and isinstance(other, Chain):
                        collision = self.check_chain_collision(state, entity, other)
        
        for remove in to_remove:
            if remove in state.entity_list:
                state.entity_list.remove(remove)

    def check_shot_ball_collision(self, state: ZoomaGameState, shot_ball: ShotBall, entity: Entity):
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
                print("Splitting chain at", match_list[-1])
                new_entity = entity.split(match_list[-1])
                if new_entity is not None:
                    state.entity_list.append(new_entity)
                
                if len(entity.data) == 0:
                    state.entity_list.remove(entity)
                else:
                    print("First chain lost motivation", entity.get_first_ball().id)
                    entity.move_speed = 0
                    
                #calculate score
                self.score_update(state, match_count, is_shot=True)
                # Do chains match... entity and new_entity
                self.scan_chain_matches(state)
            
            return True

        else:
            print("Unhandled Collision with non-chain entity")
    
        return False

    def check_chain_collision(self, state: ZoomaGameState, chain1: Chain, chain2: Chain):
        collision_record = chain1.check_collision(chain2)
        if not collision_record:
            return False

        if chain1.is_reversed():
            print("Reversed chain collision")
            if not self._do_chains_match(state, chain1, chain2):
                print("Chains do not match")
                state.combo_mult = 1
                self._merge_chains(state, chain1, chain2)
                return False
            
            print("Chains match")
            match_count = 0
            matches1 = []
            matches2 = []
            color = chain1.get_last_ball().color
            print("      Color is", color)

            index = len(chain1) - 1
            while True:
                ball = chain1.get_ball(index)
                if ball is not None:
                    print("      Ball", ball.get_label(), ball.color)
                else:
                    print("      Ball is None")
                if ball is None or ball.color != color:
                    break
                match_count += 1
                matches1.append(index)
                index -= 1

            index = 0
            while True:
                ball = chain2.get_ball(index)
                if ball is not None:
                    print("      Ball", ball.get_label(), ball.color)
                else:
                    print("      Ball is None")
                if ball is None or ball.color != color:
                    break
                match_count += 1
                matches2.append(index)
                index += 1

            if match_count < 3:     
                print("Match count too low", match_count)      
                self._merge_chains(state, chain1, chain2)
            else:
                print("Scoring match", match_count)
                matches1.sort(reverse=True)
                matches2.sort(reverse=True)

                for index in matches1:
                    chain1.remove_ball(index)
                for index in matches2:
                    chain2.remove_ball(index)

                if len(chain1.data) == 0:
                    state.entity_list.remove(chain1)
                if len(chain2.data) == 0:
                    state.entity_list.remove(chain2)

                print("Scoring combo")
                self.score_update(state, match_count, is_combo=True)
        else:
            if not (hasattr(chain1, 'shut_the_fuck_up') or hasattr(chain2, 'shut_the_fuck_up')):
                print("Normal chain collision")
            self._merge_chains(state, chain1, chain2)
        
        return False

    def _merge_chains(self, state: ZoomaGameState, chain1: Chain, chain2: Chain):
        chain1_distance = state.path.distance_between_point_and_position(-1, chain1.get_first_ball().position)
        chain2_distance = state.path.distance_between_point_and_position(-1, chain2.get_first_ball().position)
        
        if chain1_distance > chain2_distance:
            chain1, chain2 = chain2, chain1

        chain_1_speed = chain1.move_speed
        chain_2_speed = chain2.move_speed

        merging_chain = chain2
        remaining_chain = chain1

        if not (hasattr(merging_chain, 'shut_the_fuck_up') or hasattr(remaining_chain, 'shut_the_fuck_up')):
            print(f"Append chain {merging_chain.id} to chain {remaining_chain.id}")
        remaining_chain.append_chain(merging_chain)
        state.entity_list.remove(merging_chain)
        remaining_chain.move_speed = max(chain_1_speed, chain_2_speed)
    
    def score_update(self, state: ZoomaGameState, match_count: int, is_combo: bool = False, is_shot: bool = False):
        if is_shot:
            state.chain_count += 1
        if is_combo:
            state.combo_mult += 1

        combo_mult = max(1, state.combo_mult)
        chain_mult = max(1, state.chain_count - 3)
        

        score = match_count * 10 * combo_mult * chain_mult
        state.score += score
        state.progress_percent += score / 1500

        score_message = f"+{score}"
        if chain_mult > 1:
            score_message += f" Chain x{chain_mult}"
        if combo_mult > 1:
            score_message += f" Combo x{combo_mult}"

        state.last_message = score_message
        print(f"Score: {score_message}")
        
        
    def scan_chain_matches(self, state: ZoomaGameState):
        chains = [entity for entity in state.entity_list if isinstance(entity, Chain)]

        def chain_sort_key(chain: Chain):
            return state.path.distance_between_point_and_position(-1, chain.get_first_ball().position)

        chains.sort(key=chain_sort_key)

        for i in range(len(chains) - 1):
            chain1 = chains[i]
            chain2 = chains[i + 1]
            
            if self._do_chains_match(state, chain1, chain2):
                chain1.reverse(state.base_chain_speed * 3)

    def _do_chains_match(self, state: ZoomaGameState, chain1: Chain, chain2: Chain):
        chain1_distance = state.path.distance_between_point_and_position(-1, chain1.get_first_ball().position)
        chain2_distance = state.path.distance_between_point_and_position(-1, chain2.get_first_ball().position)
        
        # Make chain 1 the chain closer to the death hole
        if chain1_distance > chain2_distance:
            chain1, chain2 = chain2, chain1
        
        a = chain1.get_last_ball()
        b = chain2.get_first_ball()
        
        return a.color == b.color

    def update_display(self, state: ZoomaGameState):
        """ all the draws of python objects should occur here"""
        
        # clear the screen
        self.screen.fill(Color('black'))

        self.draw_balls(state)
        self.draw_status_display(state)

        # Update the display
        pygame.display.flip()

    def draw_balls(self, state: ZoomaGameState):
        # Draw all the balls
        for entity in state.entity_list:
            entity.draw(self.screen)

    def draw_text(self, screen: pygame.Surface, text: str, pos: tuple[int, int], centered: bool = False, centered_x: bool = False):
        text_surface = self.font.render(text, True, Color('white'))
        if centered:
            pos = (pos[0] - text_surface.get_width() / 2, pos[1] - text_surface.get_height() / 2)
        if centered_x:
            pos = (pos[0] - text_surface.get_width() / 2, pos[1])
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
    
    def draw_status_display(self, state: ZoomaGameState):
        # Draw the score
        if state.shots == 0:
            accuracy = 0
        else:
            accuracy = state.hits / state.shots

        center_x = WIDTH / 2
        self.draw_text(self.screen, f"Score: {state.score}", (center_x - 250, 10))
        self.draw_text(self.screen, state.level_name, (center_x, 10), centered_x=True)
        if state.last_message:
            self.draw_text(self.screen, state.last_message, (center_x, 50), centered=True)
        self.draw_progress_bar(self.screen, state, (center_x + 100, 10))

    



def main():
    game = ZoomaGame()
    game.run()

if __name__ == "__main__":
    main()