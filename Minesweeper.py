from __future__ import annotations
import pygame
import os
import numpy as np
from itertools import product

class Tile():

    def __init__(self, master:Game, x:int, y:int, tile_size:tuple[int, int], face:pygame.surface):
        self.master = master
        self.map_x = x
        self.map_y = y
        self.screen_x = x * tile_size[0]
        self.screen_y = y * tile_size[1] + master.header_size
        self.bomb = False
        self.number = 0
        self.show_number = 0
        self.hidden = True
        self.flagged = False
        self.face = face
        self.master.screen.blit(self.face, (self.screen_x, self.screen_y))

        self.neighbours = []
        
        pygame.display.flip()
    
    def update_face(self): 
        if self.bomb and not self.hidden:
            self.face = self.master.faces[9]
        elif self.flagged:
            self.face = self.master.faces[10]
        elif self.hidden:
            self.face = self.master.faces[-1]
        else:
            self.face = self.master.faces[self.show_number]
        
        self.master.screen.blit(self.face, (self.screen_x, self.screen_y))
        pygame.display.flip()
    
    def get_neighbours(self):
        self.neighbours = [self.master.map_array[i, j]
            for i in range(max(0, self.map_x - 1), min(self.master.map_size_in_tiles[0], self.map_x + 2))
            for j in range(max(0, self.map_y - 1), min(self.master.map_size_in_tiles[1], self.map_y + 2))
            if (i, j) != (self.map_x, self.map_y)]
    
    def discover_neighbours(self):
        if not self.hidden or self.bomb:
            return

        stack = [self]  # Start with this tile
        while stack:
            tile = stack.pop()
            if tile.hidden and not tile.bomb:
                tile.hidden = False
                tile.update_face()

                # Only add neighbors to the stack if the number is 0
                if tile.show_number == 0:
                    for neighbour in tile.neighbours:
                        if neighbour.hidden and not neighbour.bomb:
                            stack.append(neighbour)
                elif tile not in tile.master.frontier:
                    tile.master.frontier.append(tile)

    def update_number(self):
        for tile in self.neighbours:
            if tile.bomb:
                self.number += 1
    
    def update_show_number(self):
        self.show_number = 0
        for tile in self.neighbours:
            if tile.bomb:
                self.show_number += 1
            if tile.flagged:
                self.show_number -= 1
        if self.show_number == 0 and self in self.master.frontier:
            self.master.frontier.remove(self)
    
    @property
    def is_in_frontier(self) -> bool:
        if self in self.master.frontier: return True
        else: return False
    
    @property
    def free_neighbours(self) -> list:
        return [n for n in self.neighbours if not n.flagged and n.hidden]

    def __str__(self) -> str:
        return f"Tile {self.show_number} at position {self.map_x}, {self.map_y}. Hidden: {self.hidden}. Flagged: {self.flagged}. Bomb: {self.bomb}"
    
class Figure():

    def __init__(self, header:Header, x:int, y:int, face:pygame.surface):
        self.header = header
        self.master = header.master
        self.screen_x = x
        self.screen_y = y
        self.number = 0
        self.face = face

        self.master.screen.blit(self.face, (self.screen_x, self.screen_y))
    
    def update_face(self, new_face:pygame.surface):
        transform = {"0":0,
                     "1":1,
                     "2":2,
                     "3":3,
                     "4":4,
                     "5":5,
                     "6":6,
                     "7":7,
                     "8":8,
                     "9":9,
                     "10":10,
                     "-":-1}
        if type(new_face) == str:
            new_face = transform[new_face]
        self.face = self.header.numbers[new_face]
        self.master.screen.blit(self.face, (self.screen_x, self.screen_y))
        pygame.display.flip()

class Header():

    def __init__(self, master:Game):
        self.master = master
        self.max_time = master.max_time
        self.size = self.master.header_size
        directory = os.path.join(os.path.dirname(__file__), "Sprites")
        tilesheet = pygame.image.load(os.path.join(directory, "NUMBERS.png")).convert_alpha()

        original_ts = 50
        ts = int(self.size/2)
        self.numbers = []
        for i in range(13):
            rect = pygame.Rect(i*original_ts, 0, original_ts, original_ts*2)
            number_surface = pygame.Surface((original_ts, original_ts*2), pygame.SRCALPHA)
            number_surface.blit(tilesheet, (0, 0), rect)
            number_surface = pygame.transform.scale(number_surface, (ts, self.size))
            self.numbers.append(number_surface)
        self.master.screen.blit(self.numbers[11], (self.master.screen_x - ts, 0))
        self.master.screen.blit(self.numbers[11], (0, 0))
        
        self.number_of_figures = len(str(self.master.number_of_bombs))
        self.figures = []
        for i in range(self.number_of_figures):
            face = self.numbers[int((str(self.master.number_of_bombs)[-i-1]))]
            self.figures.append(Figure(self, self.master.screen_x - ts * (i + 2), 0, face))
        self.figures.reverse()
        self.clock = []
        for j in range(5):
            self.clock.append(Figure(self, 0 + ts * (j+1), 0, self.numbers[0]))
        self.clock.reverse()
        j += 1
        while j * ts < self.master.screen_x - ts * (i + 2):
            self.master.screen.blit(self.numbers[11], (j * ts, 0))
            j += 1
        
        self.score_font = pygame.font.SysFont(None, int(self.size * 0.8))
        self.score_message = self.score_font.render(f"SCORE: {self.master.score}", True, (255, 36, 7))
        self.score_rect = self.score_message.get_rect(center = ((ts * 6 + (self.master.screen_x - (ts * (len(self.figures) + 1))))/2, ts))
        self.master.screen.blit(self.score_message, self.score_rect)

        self.update_header()
        pygame.display.flip()
    
    def update_header(self):
        self.update_time()
        self.update_bomb_number()
        self.update_score()
    
    def update_bomb_number(self):
        remaining = str(self.master.number_of_bombs - self.master.number_of_flags)
        for i in range(len(remaining)):
            self.figures[i].update_face(remaining[i])
        i += 1
        while i in range(len(self.figures)):
            self.figures[i].update_face(10)
            i += 1
    
    def update_time(self):
        if self.master.start_time is None:
            self.elapsed_seconds = 0
        else:
            elapsed_ms = pygame.time.get_ticks() - self.master.start_time
            self.elapsed_seconds = elapsed_ms // 1000  # convert ms to seconds

        if self.max_time < 0:
            # Clamp to 5 digits max
            time = min(self.elapsed_seconds, 99999)
        else:
            time = self.max_time - self.elapsed_seconds

        str_time = str(time)[::-1]

        # Update the 5 clock digits
        for i in range(len(str_time)):
            self.clock[i].update_face(str_time[i])
        
        i += 1
        while i in range(len(self.clock)):
            self.clock[i].update_face(10)
            i += 1
        
        if time == 0 and self.master.start_time is not None and self.max_time > 0:
            self.master.game_over()

    def update_score(self):
        self.master.screen.fill((127, 127, 127), self.score_rect)
        ts = int(self.master.header_size/2)
        self.score_message = self.score_font.render(f"SCORE: {self.master.score}", True, (255, 36, 7))
        self.score_rect = self.score_message.get_rect(center = ((ts * 6 + (self.master.screen_x - (ts * (len(self.figures) + 1))))/2, ts))
        self.master.screen.blit(self.score_message, self.score_rect)
        
class Automation():

    def __init__(self, master:Game):
        self.master = master
        self.frontier = master.frontier
    
    def automate(self):
        can_automate = True
        easy_automation = True
        while can_automate and not self.master.go:
                can_automate = False
                while easy_automation:
                    easy_automation = False
                    self.check_completed()
                    easy_automation = self.equal_spaces_as_mines()
                    easy_automation |= self.pair_constraint_logic()
                can_automate = self.hard_constraints_logic()
                
    def check_completed(self):
        for tile in self.master.flat:
            if self.master.go: break
            if not tile.hidden and tile.show_number == 0 and tile.number != 0:
                self.master.left_click_handler(tile)

    def equal_spaces_as_mines(self) -> bool:
        easy = False
        for tile in self.master.frontier:
            if self.master.go: break
            free_neighbours = [n for n in tile.neighbours if n.hidden and not n.flagged]
            if len(free_neighbours) == tile.show_number:
                easy = True
                for n in free_neighbours:
                    self.master.right_click_handler(n)
        return easy
    
    def pair_constraint_logic(self) -> bool:
        constraints = []
        to_be_flagged = set()
        to_be_clicked = set()
        easy = False
        for tile in self.master.frontier:
            if tile.free_neighbours:
                constraints.append((set(tile.free_neighbours), tile.show_number, tile))

        for i in range(len(constraints)):
            UA, MA, A = constraints[i]
            for j in range(len(constraints)):
                if i == j:
                    continue
                UB, MB, B = constraints[j]

                if A not in B.neighbours:
                    continue

                common = UA & UB
                only_A = UA - UB
                only_B = UB - UA

                if not common and not only_A and not only_B:
                    continue

                y_min = max(0, MA - len(only_A), MB - len(only_B))
                y_max = min(len(common), MA, MB)

                if y_min == y_max:
                    y = y_min
                    x = MA - y
                    z = MB - y
                    if x == 0:
                        for cell in only_A:
                            to_be_clicked.add(cell)
                            easy = True
                    elif x == len(only_A):
                        for cell in only_A:
                            to_be_flagged.add(cell)
                            easy = True

                    if z == 0:
                        for cell in only_B:
                            to_be_clicked.add(cell)
                            easy = True
                    elif z == len(only_B):
                        for cell in only_B:
                            to_be_flagged.add(cell)
                            easy = True

        for cell in to_be_flagged:
            self.master.right_click_handler(cell)
        for cell in to_be_clicked:
            self.master.left_click_handler(cell)
            if self.master.go: break
        return easy

    def hard_constraints_logic(self) -> bool:
        frontier = [tile for tile in self.master.frontier if tile.free_neighbours]
        if not frontier:
            return False

        # Divide frontier into connected components
        components = self.divide_frontier_into_components()
        made_progress = False

        for component in components:
            tiles_in_component = set()
            tile_constraints = []

            # Collect all free neighbors and constraints
            for tile in component:
                free_neighbors = set(tile.free_neighbours)
                if free_neighbors:
                    tiles_in_component.update(free_neighbors)
                    tile_constraints.append((free_neighbors, tile.show_number))

            tiles_in_component = list(tiles_in_component)
            n = len(tiles_in_component)
            if n == 0 or n >= 12:
                continue

            # Generate all valid bomb placements
            valid_placements = []

            for mask in product([0, 1], repeat=n):
                placement = set()
                for i, val in enumerate(mask):
                    if val:
                        placement.add(tiles_in_component[i])
                
                # Check if placement satisfies all constraints
                valid = True
                for free_neighbors, number in tile_constraints:
                    count = len(placement & free_neighbors)
                    if count != number:
                        valid = False
                        break
                if valid:
                    valid_placements.append(placement)

            if not valid_placements:
                continue

            # Determine tiles that are always bombs or always safe
            all_bombs = set.intersection(*valid_placements)
            all_safe = set(tiles_in_component) - set.union(*valid_placements)

            for tile in all_bombs:
                if not tile.flagged:
                    self.master.right_click_handler(tile)
                    made_progress = True

            for tile in all_safe:
                if tile.hidden and not tile.flagged:
                    self.master.left_click_handler(tile)
                    if self.master.go: break
                    made_progress = True

        return made_progress

    def divide_frontier_into_components(self) -> list[list[Tile]]:
        frontier = set(self.master.frontier)
        components = []
        
        while frontier:
            tile = frontier.pop()
            component = [tile]
            queue = [tile]
            
            while queue:
                current = queue.pop()
                for neighbour in current.neighbours:
                    if neighbour in frontier:
                        frontier.remove(neighbour)
                        queue.append(neighbour)
                        component.append(neighbour)
            components.append(component)
        return components

class Game():

    def __init__(self, screen:pygame.display, data:list):
        self.start_time = None
        self.firstclick = True
        self.go = False
        self.won = False
        self.data = data
        self.max_time = data[2]
        self.screen = screen
        self.screen_x, self.screen_y = self.screen.size
        self.map_size_in_tiles = data[0]
        self.number_of_bombs = int(self.map_size_in_tiles[0] * self.map_size_in_tiles[1] * data[1])
        self.number_of_flags = 0
        self.header_size = int(min(100, self.screen_y / 10))
        self.tile_size = self.screen_x/self.map_size_in_tiles[0], (self.screen_y - self.header_size)/self.map_size_in_tiles[1]

        self.mine_area = ((0, self.header_size), 
                          (self.map_size_in_tiles[0]*self.tile_size[0], self.header_size + self.map_size_in_tiles[1]*self.tile_size[1]))
        self.font = pygame.font.SysFont(None, 48)

        directory = os.path.join(os.path.dirname(__file__), "Sprites")
        tilesheet = pygame.image.load(os.path.join(directory, "TILES ALL.png")).convert_alpha()
        ts = 20
        self.faces = []
        self.frontier = []
        for i in range(3):
            for j in range(4):
                rect = pygame.Rect(j * ts, i * ts, ts, ts)
                tile_surface = pygame.Surface((ts, ts), pygame.SRCALPHA)
                tile_surface.blit(tilesheet, (0, 0), rect)
                tile_surface = pygame.transform.scale(tile_surface, self.tile_size)
                self.faces.append(tile_surface)
        
        self.map_array = np.empty(self.map_size_in_tiles, dtype = object)

        self.header = Header(self)

        for i in range(self.map_size_in_tiles[0]):
            for j in range(self.map_size_in_tiles[1]):
                self.map_array[i, j] = Tile(self, i, j, self.tile_size, self.faces[-1])
        self.flat = self.map_array.flatten()
        self.automation = Automation(self)

    def decide_bombs(self, to_avoid:Tile):

        filtered = np.array([x for x in self.flat if x not in [to_avoid] + to_avoid.neighbours])
        self.bombs = np.random.choice(filtered, size = self.number_of_bombs, replace = False)
        
        for tile in self.bombs:
            tile.bomb = True

        for tile in self.flat:
            tile.update_number()
            tile.update_show_number()
    
    def neighbours(self):
        for tile in self.flat:
            tile.get_neighbours()

    def game_over(self):
        for tile in self.bombs:
            tile.hidden = False
            tile.update_face()
        game_over_surface = self.font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_surface.get_rect(center=(self.screen_x//2, self.screen_y//2))
        self.screen.blit(game_over_surface, text_rect)
        self.go = True
        self.header.update_score()
        pygame.display.flip()
        pygame.time.delay(2000)

    def check_winning_condition(self):
        win = True
        for tile in self.flat:
            if (not tile.bomb and tile.hidden) or (tile.bomb and not tile.flagged):
                win = False
        if win:
            game_over_surface = self.font.render("YOU WON", True, (255, 0, 0))
            text_rect = game_over_surface.get_rect(center=(self.screen_x//2, self.screen_y//2))
            self.won = True
            for tile in self.flat:
                tile.show_number = tile.number
                tile.update_face()
            self.screen.blit(game_over_surface, text_rect)
            self.header.update_score()
            pygame.display.flip()
            pygame.time.delay(2000)

    def left_click_handler(self, current_tile:Tile):
        if self.firstclick:
            self.decide_bombs(current_tile)
            self.firstclick = False
            self.start_time = pygame.time.get_ticks()
        
        if current_tile.bomb and not current_tile.flagged:
            self.game_over()
        
        if current_tile.number != 0 and current_tile.show_number == 0:
            for tile in current_tile.neighbours:
                if not tile.flagged:
                    tile.discover_neighbours()
            for tile in current_tile.neighbours:
                if tile.bomb and not tile.flagged:
                    self.game_over()
                
        current_tile.discover_neighbours()
        self.check_winning_condition()
    
    def right_click_handler(self, current_tile:Tile):
        if current_tile.hidden:
            if not current_tile.flagged:
                current_tile.flagged = True
                self.number_of_flags += 1
            else:
                current_tile.flagged = False
                self.number_of_flags -= 1
            current_tile.update_face()  

        for neighbour in current_tile.neighbours:
            neighbour.update_show_number()
            neighbour.update_face()

        self.header.update_header()
        self.check_winning_condition()
    
    def update_debug(self):
        for tile in self.map_array.flatten():
            tile.hidden = False
            tile.update_face()

    @property
    def score(self):
        if self.start_time is None:
            return 0

        # Time
        elapsed = self.header.elapsed_seconds

        # Board
        width, height = self.map_size_in_tiles
        A = width * height
        B = self.number_of_bombs
        D = B / A

        # Difficulty
        difficulty_score = A * (1 + 3 * D)

        # Time factor
        if self.max_time > 0:
            time_bonus = (1 + 3600 / self.max_time) * (self.max_time - elapsed) * 0.85
            time_factor = 1 / (1 + elapsed / A)
        else:
            time_bonus = 0
            time_factor = 1 / (1 + 1 / A)

        # Efficiency
        revealed = sum(1 for t in self.flat if (not t.hidden or t.flagged))

        efficiency = revealed / A
        won_bonus = 1.5 if self.won else 1
        return int(difficulty_score * time_factor * efficiency * won_bonus + time_bonus)

class Button():
    def __init__(self, menu:Menu, rect: pygame.Rect, options:list[list], title:str, font: pygame.font.Font, colors: tuple):
        self.rect = rect
        self.options = options
        self.title = title
        self.font = font
        self.colors = colors
        self.menu = menu
        self.screen = self.menu.screen
        self.num = 0
        self.text = self.options[self.num][0]
        self.data = self.options[self.num][1]
    
    def draw(self):
        pygame.draw.rect(self.screen, self.colors[0], self.rect)
        text_surf = self.font.render(self.text, True, self.colors[1])
        text_rect = text_surf.get_rect(center=self.rect.center)
        self.screen.blit(text_surf, text_rect)

        text_title = self.font.render(self.title, True, self.colors[2])
        text_rect = text_title.get_rect(center = (self.rect.centerx, self.rect.y - self.font.get_height() - 5))
        self.screen.blit(text_title, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def update(self):
        self.num %= (len(self.options))
        self.text = self.options[self.num][0]
        self.data = self.options[self.num][1]
        self.draw()

class Menu():

    def __init__(self):
        
        self.score_file = os.path.join(os.path.dirname(__file__), "scores.txt")
        
        pygame.init()
        bg = os.path.join(os.path.dirname(__file__), "Sprites", "background.png")
        self.background = pygame.image.load(bg)
        self.monitor_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        scale = (0.9, 0.9)
        self.screen_size = (self.monitor_size[0]*scale[0], self.monitor_size[1]*scale[1])
        if self.screen_size[0] > self.background.get_width() or self.screen_size[1] > self.background.get_height():
            self.background = pygame.transform.scale(self.background, self.screen_size)

        self.screen = pygame.display.set_mode(self.screen_size)
        self.toggles = ["Map Size", "Difficulty", "Max Time"]
        self.options = {
            "Map Size":[["Small", (10, 10)], ["Medium", (20, 20)], ["Big", (30, 30)],  ["Bigger", (40, 40)], ["Massive", (50,40)]],
            "Difficulty":[["Easiest", 0.05], ["Easy", 0.1], ["Medium", 0.15], ["Hard", 0.2], ["Harder", 0.25], ["Impossible", 0.4]],
            "Max Time":[["Unlimited", -1], ["1 Hour", 3600], ["30 Mins", 1800], ["15 Mins", 900], ["10 Mins", 600], ["5 Mins", 300], ["1 Min", 60], ["30 Sec", 30], ["MADMAN", 10]]
        }
        self.buttons = []
        spaces = len(self.toggles) * 2 + 1
        width = self.screen_size[0]/spaces

        for i in range(len(self.toggles)):
            face = pygame.Rect(width + width * i * 2, self.screen_size[1]/3*2, width, self.screen_size[1]/10)
            self.buttons.append(Button(self, face, self.options[self.toggles[i]], self.toggles[i], pygame.font.SysFont(None, 28), ((87, 87, 87), (0, 0, 0), (255, 255, 255))))

        self.main_menu()
            
    def main_menu(self):
        self.get_high_score()
        self.screen.blit(self.background, (0, 0))
        font_title = pygame.font.SysFont(None, 72)
        font_prompt = pygame.font.SysFont(None, 48)
        score_font = pygame.font.SysFont(None, 32)
        
        self.title_surface = font_title.render("MINESWEEPER", True, (255, 255, 255))
        self.prompt_surface = font_prompt.render("PRESS ENTER TO BEGIN", True, (255, 255, 255))
        self.score_surface = score_font.render(f"HIGH SCORE: {self.high_score}", True, (255, 255, 255))
        
        # Get rects for centering
        self.title_rect = self.title_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 - 50))
        self.prompt_rect = self.prompt_surface.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 + 50))
        self.score_rect = self.score_surface.get_rect(center = (self.screen_size[0]//2, self.screen_size[1] // 2))
        
        self.screen.blit(self.title_surface, self.title_rect)
        self.screen.blit(self.prompt_surface, self.prompt_rect)
        for button in self.buttons:
            button.draw()
            
        running = True
        while running:
            self.score_surface = score_font.render(f"HIGH SCORE: {self.high_score}", True, (255, 255, 255))
            self.screen.blit(self.score_surface, self.score_rect)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for button in self.buttons:
                        if button.is_clicked(pos):
                            if event.button == 1:
                                button.num +=1
                            if event.button == 3:
                                button.num -= 1
                            button.update()
                            break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.screen.fill((0, 0, 0))
                        self.data = []
                        for button in self.buttons:
                            self.data.append(button.data)
                            #Map Size, Difficulty, Max Time
                        running = self.run_game()

    def run_game(self):
        self.G = Game(self.screen, self.data)
        self.G.neighbours()
        #Main Game Loop
        while not self.G.go and not self.G.won:
            self.G.header.update_header()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = pygame.mouse.get_pos()
                        if self.G.mine_area[0][0] <= x <= self.G.mine_area[1][0] and self.G.mine_area[0][1] <= y <=self.G.mine_area[1][1]:
                            row, col = int((y- self.G.header_size)/self.G.tile_size[1]), int(x/self.G.tile_size[0])
                            current_tile = self.G.map_array[col, row]
                            if event.button == 1:
                                self.G.left_click_handler(current_tile)
                            
                            if event.button == 3:
                                self.G.right_click_handler(current_tile)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        self.G.update_debug()
                        pygame.time.delay(2000)
                        self.G.go = True

                    if event.key == pygame.K_a:
                        self.G.automation.automate()

        self.save_score(self.G.score)
        self.get_high_score()
        
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.title_surface, self.title_rect)
        self.screen.blit(self.prompt_surface, self.prompt_rect)
        for button in self.buttons:
            button.draw()
        return True

    def save_score(self, score):
        with open(self.score_file, "a", encoding="utf-8") as f:
            f.write(f"{score}\n")
    
    def get_high_score(self):
        with open(self.score_file, "r", encoding="utf-8") as f:
            scores = [int(line.strip()) for line in f if line.strip().isdigit()]
            self.high_score = max(scores)

M = Menu()
