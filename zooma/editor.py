import pygame
import json
from pygame import Vector2
from zooma.entities.path import Path
import os

# This editor was created with the assistance of Windsurf AI to enable creating the data needed
# for the levels used by the Zooma Game.  Most of this code is AI generated.

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zooma Level Editor")
clock = pygame.time.Clock()

# Editor state
class EditorState:
    def __init__(self):
        self.paths = []  # List of paths
        self.current_path = Path([])
        self.drawing = False
        self.last_point = None
        self.show_grid = True
        self.grid_size = 20
        self.last_saved = None
        self.input_active = False
        self.input_text = ""
        self.input_prompt = ""
        self.input_rect = None
        self.input_font = None
        self.input_color = (0, 0, 0)  # Black text
        self.input_active_color = (80, 80, 80)
        self.input_inactive_color = (0, 255, 0)
        self.input_cancelled = False

    def add_path(self):
        """Add the current path to the list and start a new one"""
        if len(self.current_path.points) > 1:  # Only add if path has at least 2 points
            self.paths.append(self.current_path)
        self.current_path = Path([])
        self.last_point = None
        self.drawing = False

    def save_paths(self):
        """Save all paths to a level file"""
        # Add current path to paths list only if it has points
        if len(self.current_path.points) > 1:
            self.paths.append(self.current_path)
        
        # Check if we have any paths to save
        if len(self.paths) == 0:
            print("No paths to save")
            return

        self.input_prompt = "Enter level name (without extension):"
        self.input_is_load = False
        self.input_active = True
        self.input_text = ""
        self.input_cancelled = False

    def load_paths(self):
        """Load paths from a level file"""
        self.input_prompt = "Enter level name (without extension):"
        self.input_is_load = True
        self.input_active = True
        self.input_text = ""
        self.input_cancelled = False

    def handle_input(self, event):
        """Handle keyboard events during input"""
        if not self.input_active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Validate input
                if not self.input_text:
                    print("Level name cannot be empty")
                    return True

                filename = f"zooma/levels/{self.input_text}.json"
                if not self.input_is_load:
                    # Save operation
                    if os.path.exists(filename):
                        print(f"File {filename} already exists. Please choose a different name.")
                        return True

                    data = {
                        "paths": []
                    }
                    # Add all paths from paths list
                    for path in self.paths:
                        if len(path.points) > 1:
                            data["paths"].append({
                                "points": [[int(p.x), int(p.y)] for p in path.points]
                            })
                    
                    # No need to add current_path again since it's already in paths list
                    
                    if len(data["paths"]) == 0:
                        print("No paths to save")
                        return True
                    
                    os.makedirs("zooma/levels", exist_ok=True)
                    with open(filename, "w") as f:
                        json.dump(data, f, indent=4)
                    
                    self.last_saved = pygame.time.get_ticks()
                    print(f"Paths saved to {filename}")
                    self.input_active = False
                    return True
                else:
                    # Load operation
                    try:
                        with open(filename, "r") as f:
                            data = json.load(f)
                            self.paths = []
                            for path_data in data.get("paths", []):
                                path = Path([])
                                for point in path_data.get("points", []):
                                    path.addPoint(point)
                                if len(path.points) > 1:
                                    self.paths.append(path)
                            
                            self.current_path = Path([])
                            self.last_point = None
                            self.drawing = False
                            print(f"Paths loaded from {filename}")
                            self.input_active = False
                            return True
                    except Exception as e:
                        print(f"Error loading file: {e}")
                        return True

            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                self.input_cancelled = True
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if len(self.input_text) < 20:  # Limit input length
                    self.input_text += event.unicode

        return True

    def load_path(self):
        """Load a path from level.json"""
        try:
            with open("level.json", "r") as f:
                data = json.load(f)
                self.path.clear()
                for point in data["points"]:
                    self.path.addPoint(point)
                print("Path loaded from level.json")
        except FileNotFoundError:
            print("No level.json found")

    def toggle_grid(self):
        self.show_grid = not self.show_grid

    def draw_input(self, screen):
        """Draw the input prompt and text"""
        if not self.input_active:
            return

        if self.input_font is None:
            self.input_font = pygame.font.Font(None, 32)

        # Draw prompt
        prompt_surface = self.input_font.render(self.input_prompt, True, self.input_color)
        prompt_rect = prompt_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        screen.blit(prompt_surface, prompt_rect)

        # Draw input text
        text_surface = self.input_font.render(self.input_text, True, 
                                            self.input_active_color if self.input_active else self.input_inactive_color)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)

        # Draw cursor
        if pygame.time.get_ticks() % 1000 < 500 and self.input_active:
            cursor_surface = pygame.Surface((2, text_surface.get_height()))
            cursor_surface.fill(self.input_active_color)
            cursor_rect = cursor_surface.get_rect(left=text_rect.right, centery=text_rect.centery)
            screen.blit(cursor_surface, cursor_rect)

    def clear_paths(self):
        """Clear all paths and start fresh"""
        self.paths = []
        self.current_path = Path([])
        self.last_point = None
        self.drawing = False

    def undo_last_points(self, count=10):
        """Remove the last 'count' points from the path"""
        if len(self.current_path.points) <= 1:
            return
            
        # Keep at least the first point
        points_to_keep = max(1, len(self.current_path.points) - count)
        self.current_path.points = self.current_path.points[:points_to_keep]
        
        # Update last_point if it was removed
        if len(self.current_path.points) > 0:
            self.last_point = self.current_path.points[-1].x, self.current_path.points[-1].y
        else:
            self.last_point = None

    def add_point(self, pos):
        new_point = Vector2(pos)
        if self.last_point is not None:
            distance = new_point.distance_to(Vector2(self.last_point))
            if distance < 5:  # Minimum distance between points
                return
                
            # Add intermediate points if the distance is too large
            if distance > 20:  # Add points every 20 pixels
                direction = new_point - Vector2(self.last_point)
                direction.normalize_ip()
                steps = int(distance / 20)
                for i in range(1, steps):
                    intermediate = Vector2(self.last_point) + direction * (i * 20)
                    self.current_path.addPoint(intermediate)
        
        self.current_path.addPoint(new_point)
        self.last_point = pos
        self.smooth_path()

    def smooth_path(self):
        """Smooth only the last 50 points of the path"""
        if len(self.current_path.points) < 3:
            return

        # Create a new list of smoothed points
        smoothed_points = []
        
        # First point stays the same
        smoothed_points.append(self.current_path.points[0])
        
        # Keep all points except the last 75 unchanged
        for i in range(1, len(self.current_path.points) - 75):
            smoothed_points.append(self.current_path.points[i])
        
        # Smooth the last 75 points
        for i in range(max(1, len(self.current_path.points) - 75), len(self.current_path.points) - 1):
            # Take average of current point and its neighbors
            avg_x = (self.current_path.points[i-1].x + 
                    self.current_path.points[i].x * 2 + 
                    self.current_path.points[i+1].x) / 4
            avg_y = (self.current_path.points[i-1].y + 
                    self.current_path.points[i].y * 2 + 
                    self.current_path.points[i+1].y) / 4
            smoothed_points.append(Vector2(avg_x, avg_y))
        
        # Last point stays the same
        smoothed_points.append(self.current_path.points[-1])
        
        # Update the path with smoothed points
        self.current_path.clear()
        for point in smoothed_points:
            self.current_path.addPoint(point)

def main():
    """Main entry point for the level editor"""
    # Initialize editor
    state = EditorState()

    # Main loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if state.input_active:
                    # Only handle input events when input is active
                    if not state.handle_input(event):
                        # If handle_input returns False, it means we should process other events
                        if event.key == pygame.K_c:
                            state.clear_paths()
                        elif event.key == pygame.K_g:
                            state.toggle_grid()
                        elif event.key == pygame.K_u:
                            state.undo_last_points()
                        elif event.key == pygame.K_n:
                            state.add_path()
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                else:
                    # Only process shortcuts when input is not active
                    if event.key == pygame.K_s:
                        state.save_paths()
                    elif event.key == pygame.K_l:
                        state.load_paths()
                    elif event.key == pygame.K_c:
                        state.clear_paths()
                    elif event.key == pygame.K_g:
                        state.toggle_grid()
                    elif event.key == pygame.K_u:
                        state.undo_last_points()
                    elif event.key == pygame.K_n:
                        state.add_path()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    state.drawing = True
                    state.add_point(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    state.drawing = False
            
            elif event.type == pygame.MOUSEMOTION:
                if state.drawing:
                    state.add_point(event.pos)

        # Draw everything
        screen.fill(WHITE)
        
        # Draw grid if enabled
        if state.show_grid:
            for x in range(0, WIDTH, state.grid_size):
                pygame.draw.line(screen, (200, 200, 200), (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, state.grid_size):
                pygame.draw.line(screen, (200, 200, 200), (0, y), (WIDTH, y))

        # Draw all paths
        for i, path in enumerate(state.paths):
            color = (100 + (i * 50) % 155, 100 + (i * 30) % 155, 100 + (i * 70) % 155)
            if len(path.points) > 1:
                pygame.draw.lines(screen, color, False, path.points, 3)
                
                # Draw points
                for j, point in enumerate(path.points):
                    point_color = GREEN if j == 0 else RED if j == len(path.points) - 1 else color
                    pygame.draw.circle(screen, point_color, point, 5)
        
        # Draw current path
        if len(state.current_path.points) > 1:
            pygame.draw.lines(screen, BLUE, False, state.current_path.points, 3)
            
            # Draw points
            for i, point in enumerate(state.current_path.points):
                color = GREEN if i == 0 else RED if i == len(state.current_path.points) - 1 else BLUE
                pygame.draw.circle(screen, color, point, 5)

        # Draw status text
        font = pygame.font.Font(None, 24)
        text = f"Points: {len(state.current_path.points)} | {'Drawing' if state.drawing else 'Not drawing'}"
        if state.last_saved is not None:
            time_since_save = (pygame.time.get_ticks() - state.last_saved) / 1000
            text += f" | Last saved: {time_since_save:.1f}s ago"
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (10, 10))

        # Draw input if active
        state.draw_input(screen)

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
