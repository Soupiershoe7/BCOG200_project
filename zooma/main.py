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
        self.score = 0
        self.progress_percent = 0
        self.chain_count = 0
        self.combo_mult = 1

        self.entity_list = []
        self.forg: Forg = None

        self.paused = True
        self.draw_mode = False
        self.last_message = ""
        self.base_chain_speed = 0.5
        self.did_zooma = False
        self.game_over = False
        self.level_complete = False
        self.show_game_over = False
        self.did_reset_boost = False
        self.start_time = 0
        self.game_start_boost_mult = 10
        self.game_start_boost_time = 1500

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
            state.did_reset_boost = False
            state.last_message = ""
            state.level_complete = False

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
                state.entity_list.append(path)

                start_point = points[0]
                end_point = points[-1]
                
                emitter = Emitter(Vector2(start_point), path, state.level_colors)
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
        state.start_time = pygame.time.get_ticks()
        state.paused = False
        state.forg.reset()
        for entity in state.entity_list:
            if isinstance(entity, Emitter):
                entity.activate()

    def end_level(self, state: ZoomaGameState):
        #add prompt
        state.paused = True
        state.last_message = "Level Complete!"
        state.level_complete = True
        
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
        self.end_level(state)
        state.show_game_over = False
        state.game_over = False
        state.score = 0
        state.current_level = 0

        self.state = self.load_level(state.current_level, state)
        self.start_level(self.state)

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
                    if state.level_complete:
                        self.advance_level(state)
                    else:
                        self.shoot_ball(state)

            elif event.type == pygame.KEYDOWN:
                # exit game
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                elif event.key == K_RETURN:
                    if state.level_complete:
                        self.advance_level(state)
                
                # toggle pause
                elif event.key == K_p: 
                    state.paused = not state.paused

                # advance level
                elif event.key == K_n: 
                    self.advance_level(state)

                # swap held ball
                elif event.key == K_SPACE: 
                    self.swap_held_ball(state)
                
                # reset level
                elif event.key == K_r: 
                    self.reset_game(state)

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
        self.task_emit_chain(state)
        self.task_motivate_chains(state)
        self.task_check_colors(state)

    def task_check_win(self, state: ZoomaGameState):
        ball_count = 0
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                ball_count += len(entity.data)

        if ball_count == 0:
            if state.game_over:
                state.show_game_over = True
            elif state.did_zooma:
                self.end_level(state)


    def task_emit_chain(self, state: ZoomaGameState):
        self.try_to_emit_chain(state)

        # See if progress is complete and stop emitters
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
                last_chain = None
                best_distance = float('inf')

                for entity in state.entity_list:
                    # emitter blocked
                    if isinstance(entity, Chain):
                        if entity.path != emitter.path:
                            continue
                        
                        d = emitter.path.distance_between_point_and_position(
                            0,
                            entity.get_last_ball().position
                        )

                        if d < best_distance:
                            best_distance = d
                            last_chain = entity
                            
                        if emitter.check_collision(entity):
                            can_emit = False
                            break
                
                if can_emit:
                    new_ball = ChainBall(emitter.position, emitter.get_color())
                    chain = Chain(emitter.path, [new_ball])
                    chain.shut_the_fuck_up = True

                    if (last_chain is not None and
                        best_distance < last_chain.get_last_ball().radius * 3):
                        last_chain.append_chain(chain)
                    else:
                        state.entity_list.append(chain)

    # I got help from a tutor for functionality for multiple pushers
    def task_motivate_chains(self, state: ZoomaGameState):
        path_distances = {}
        path_pushers = {}

        should_boost = (pygame.time.get_ticks() - state.start_time) < state.game_start_boost_time

        for entity in state.entity_list:
            if isinstance(entity, Chain):
                if state.game_over:
                    entity.move_speed = state.base_chain_speed * 10
                else:
                    first_ball = entity.get_first_ball()
                    path = entity.path
                    d = path.distance_between_point_and_position(0, first_ball.position)
                    path_current_best_distance = path_distances.get(path, float('inf'))
                    if d < path_current_best_distance:
                        path_distances[path] = d
                        path_pushers[path] = entity
        
        if not should_boost and not state.did_reset_boost:
            state.did_reset_boost = True
            for entity in state.entity_list:
                if isinstance(entity, Chain):
                    entity.move_speed = min(entity.move_speed, state.base_chain_speed)

        if not state.game_over:
            for pusher in path_pushers.values():
                if should_boost:
                    pusher.move_speed = state.base_chain_speed * state.game_start_boost_mult
                else:
                    pusher.move_speed = state.base_chain_speed
            
            self.scan_chain_matches(state)

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

        if len(first_chain) == 0:
            state.entity_list.remove(first_chain)
            


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

    def shoot_ball(self, state: ZoomaGameState):
        """ Shoot the held ball """
        ball_just_shot = state.forg.shoot()
        if ball_just_shot is None:
            return
        state.entity_list.append(ball_just_shot)

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
        path1 = chain1.path
        path2 = chain2.path
        
        if path1 != path2:
            print("!!!! ERROR: Merging chains on different paths")
            return
        
        chain1_distance = path1.distance_between_point_and_position(-1, chain1.get_first_ball().position)
        chain2_distance = path2.distance_between_point_and_position(-1, chain2.get_first_ball().position)
        
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
        path_chains = {}
        
        for entity in state.entity_list:
            if isinstance(entity, Chain):
                path = entity.path
                if path not in path_chains:
                    path_chains[path] = []
                path_chains[path].append(entity)

        def chain_sort_key(chain: Chain):
            path = chain.path
            return path.distance_between_point_and_position(-1, chain.get_first_ball().position)

        for path, chains in path_chains.items():
            chains.sort(key=chain_sort_key)

            for i in range(len(chains) - 1):
                chain1 = chains[i]
                chain2 = chains[i + 1]
                
                if self._do_chains_match(state, chain1, chain2):
                    if not chain1.is_reversed():
                        chain1.reverse(state.base_chain_speed * 3)
                else:
                    if chain1.is_reversed():
                        chain1.move_speed = 0
    
    def _do_chains_match(self, state: ZoomaGameState, chain1: Chain, chain2: Chain):
        path1 = chain1.path
        path2 = chain2.path
        
        if path1 != path2:
            print("!!!! ERROR: Comparing chains on different paths")
            return False
        
        chain1_distance = path1.distance_between_point_and_position(-1, chain1.get_first_ball().position)
        chain2_distance = path2.distance_between_point_and_position(-1, chain2.get_first_ball().position)
        
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

        self.draw_entities(state)
        self.draw_status_display(state)

        if state.show_game_over:
            self.draw_game_over(state)
        elif state.level_complete:
            self.draw_level_complete(state)
        

        # Update the display
        pygame.display.flip()

    def draw_entities(self, state: ZoomaGameState):
        # Draw all the entities
        for entity in state.entity_list:
            entity.draw(self.screen)

    def draw_text(self, screen: pygame.Surface, 
                  text: str, pos: tuple[int, int], 
                  color: Color = Color('white'), 
                  centered: bool = False, 
                  centered_x: bool = False):
        text_surface = self.font.render(text, True, color)
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
        
        center_x = WIDTH / 2
        self.draw_text(self.screen, f"Score: {state.score}", (center_x - 250, 10))
        self.draw_text(self.screen, state.level_name, (center_x, 10), centered_x=True)
        if state.last_message:
            self.draw_text(self.screen, state.last_message, (center_x, 50), centered=True)
        self.draw_progress_bar(self.screen, state, (center_x + 100, 10))

    def draw_game_over(self, state: ZoomaGameState):
        if state.show_game_over:
            dimensions = Vector2(700, 350)
            center = Vector2(WIDTH / 2, HEIGHT / 2)
            rect = pygame.Rect(center.x - dimensions.x / 2, center.y - dimensions.y / 2, dimensions.x, dimensions.y)
            pygame.Surface.fill(self.screen, Color('#8e7c78'), rect)
            
            self.draw_text(self.screen, "Game Over", (center.x, center.y - 50), centered=True)
            self.draw_text(self.screen, f"Final score: {state.score}", (center.x, center.y), centered=True)
            self.draw_text(self.screen, "Press Escape to exit or R to restart", (center.x, center.y + 50), centered=True)

    def draw_level_complete(self, state: ZoomaGameState):

        
        if state.current_level >= len(self.data["levels"]):
            dimensions = Vector2(700, 350)
            center = Vector2(WIDTH / 2, HEIGHT / 2)
            rect = pygame.Rect(center.x - dimensions.x / 2, center.y - dimensions.y / 2, dimensions.x, dimensions.y)
            pygame.Surface.fill(self.screen, Color('#8e7c78'), rect)
            
            self.draw_text(self.screen, "You win!", (center.x, center.y - 50), centered=True)
            self.draw_text(self.screen, f"Final score: {state.score}", (center.x, center.y), centered=True)
            self.draw_text(self.screen, "Press Escape to exit or R to restart", (center.x, center.y + 50), centered=True)
            return
        
        dimensions = Vector2(500, 250)
        center = Vector2(WIDTH / 2, HEIGHT / 2)
        rect = pygame.Rect(center.x - dimensions.x / 2, center.y - dimensions.y / 2, dimensions.x, dimensions.y)

        pygame.Surface.fill(self.screen, Color('#8e7c78'), rect)

        self.draw_text(self.screen, "Level Complete", (center.x, center.y - 50), centered=True)
        self.draw_text(self.screen, f"Score: {state.score}", (center.x, center.y), centered=True)
        self.draw_text(self.screen, "Press Enter or click to continue", (center.x, center.y + 50), centered=True)
        



def main():
    game = ZoomaGame()
    game.run()

if __name__ == "__main__":
    main()