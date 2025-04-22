import pygame
import math
import random
import sys

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
BALL_RADIUS = 16
BALL_COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
SHOT_SPEED = 8

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Path: A simple curved path made from points
PATH_POINTS = [(100 + x * 5, 300 + int(100 * math.sin(x * 0.05))) for x in range(120)]

def draw_path(surface):
    pygame.draw.lines(surface, (100, 100, 100), False, PATH_POINTS, 3)

def draw_rotated_rect_line(surface, color, start_pos, end_pos, width):
    start = pygame.Vector2(start_pos)
    end = pygame.Vector2(end_pos)
    direction = (end - start).normalize()
    perp = pygame.Vector2(-direction.y, direction.x) * (width / 2)

    points = [
        start + perp,
        start - perp,
        end - perp,
        end + perp
    ]
    pygame.draw.polygon(surface, color, points)

def random_ball():
    x = random.randint(50, WIDTH - 50)
    y = random.randint(50, HEIGHT // 2)
    color = random.choice(BALL_COLORS)
    return Ball((x, y), color)

class Ball:
    def __init__(self, pos, color):
        self.pos = pygame.Vector2(pos)
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos, BALL_RADIUS)

class Shooter:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.angle = 0
        self.loaded_color = random.choice(BALL_COLORS)

    def update(self, mouse_pos):
        direction = pygame.Vector2(mouse_pos) - self.pos
        self.angle = math.atan2(direction.y, direction.x)

    def draw(self, surface):
        # Draw cannon base
        pygame.draw.circle(surface, (50, 50, 50), self.pos, 30)
        # Draw cannon barrel
        barrel_length = 90
        end_x = self.pos.x + barrel_length * math.cos(self.angle)
        end_y = self.pos.y + barrel_length * math.sin(self.angle)
        # draw_rotated_rect_line(surface, (200, 200, 200), self.pos, (end_x, end_y), 6)
        pygame.draw.line(surface, (200, 200, 200), self.pos, (end_x, end_y), 6)
        # draw_rotated_rect_line(surface, (200, 200, 200), self.pos, (end_x, end_y), 6)
        # Draw loaded ball
        pygame.draw.circle(surface, self.loaded_color, self.pos, BALL_RADIUS*1.5)

    def shoot(self):
        direction = pygame.Vector2(math.cos(self.angle), math.sin(self.angle))
        return ShotBall(self.pos, direction, self.loaded_color)

class ShotBall(Ball):
    def __init__(self, pos, direction, color):
        super().__init__(pos, color)
        self.velocity = direction * SHOT_SPEED

    def update(self):
        self.pos += self.velocity

def main():
    shooter = Shooter((WIDTH // 2, HEIGHT - 60))
    shot_balls = []
    static_balls = [random_ball() for _ in range(5)]  # Add 5 balls

    running = True
    autoshoot = False
    show_autoshoot = False
    while running:
        dt = clock.tick(FPS) / 1000
        screen.fill((20, 20, 20))

        # Write the number of shot_balls on the top left corner
        font = pygame.font.Font(None, 36)
        text = font.render(f"Shot Balls: {len(shot_balls)}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        # Show autoshoot status
        if show_autoshoot:
            text = font.render(f"Autoshoot: {'ON' if autoshoot else 'OFF'}", True, (255, 255, 255))
            screen.blit(text, (10, 40))

        did_already_shoot = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                did_already_shoot = True
                shot_balls.append(shooter.shoot())
                shooter.loaded_color = random.choice(BALL_COLORS)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    autoshoot = not autoshoot
                    show_autoshoot = True

        if autoshoot and not did_already_shoot:
            shot_balls.append(shooter.shoot())
            shooter.loaded_color = random.choice(BALL_COLORS)

        mouse_pos = pygame.mouse.get_pos()
        shooter.update(mouse_pos)

        #draw_path(screen)
        shooter.draw(screen)

        # Update and draw shot balls
        for shot in shot_balls[:]:
            shot.update()
            shot.draw(screen)

            # Collision detection with static balls
            for target in static_balls[:]:
                if shot.pos.distance_to(target.pos) <= BALL_RADIUS * 2:
                    static_balls.remove(target)
                    static_balls.append(random_ball())
                    shot_balls.remove(shot)
                    break  # Stop checking once hit

        # Draw static balls
        for ball in static_balls:
            ball.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()