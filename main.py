import pygame, random, math, time, sys, os, database
pygame.init()
database.init_database()

pygame.display.init()
screen = pygame.display.set_mode((960, 640))
clock = pygame.time.Clock()
FPS = 60

TILE_SIZE = 32



#tilemap objects
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_size, door=False):
        super().__init__()
        colour = (50, 50, 50)
        if door: #allows doors
            self.door = True
            colour = DARK_BROWN
        else:
            self.door = False

        self.image = pygame.Surface((tile_size, tile_size))
        self.image.fill(colour)

        self.rect = self.image.get_rect(topleft = (x, y))


class Candle(pygame.sprite.Sprite):
    def __init__(self, x, y, wax_value=25):
        super().__init__()
        self.x = x
        self.y = y
        self.image = pygame.Surface((32, 32))
        self.image.fill((200, 190, 150))
        self.wax_value = wax_value
        self.rect = pygame.Rect((x - 16), (y - 16), 32, 32)
        self.lit = False
        self.door = False


#basic objects
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        #visuals
        self.image = pygame.Surface((32, 32))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Store position as a Vector2 for smooth float precision
        self.pos = pygame.math.Vector2(x, y)
        self.speed = 7

        self.max_wax = 100
        self.wax = self.max_wax
        self.score = 0
        self.rooms_cleared = 0

    def update(self, walls):
        global new_room
        keys = pygame.key.get_pressed()
        move_vec = pygame.math.Vector2(0, 0)

        # 1. Check Inputs
        if keys[pygame.K_w]:
            move_vec.y -= 1
        if keys[pygame.K_s]:
            move_vec.y += 1
        if keys[pygame.K_a]:
            move_vec.x -= 1
        if keys[pygame.K_d]:
            move_vec.x += 1

        # 2. Normalize diagonal movement
        if move_vec.length() > 0:
            move_vec = move_vec.normalize() * self.speed

        # 3. Apply movement
        self.pos.x += move_vec.x
        self.rect.x = round(self.pos.x) #update hitbox x position

        x_collide = pygame.sprite.spritecollide(self, walls, False)
        for hit in x_collide:
            if move_vec.x > 0: #moving right
                self.rect.right = hit.rect.left
                self.pos.x = self.rect.x
            elif move_vec.x < 0: #moving left
                self.rect.left = hit.rect.right
                self.pos.x = self.rect.x
        
        self.pos.y += move_vec.y
        self.rect.y = round(self.pos.y) #update hitbox y position

        y_collide = pygame.sprite.spritecollide(self, walls, False)
        for hit in y_collide:
            if move_vec.y > 0: #moving down
                self.rect.bottom = hit.rect.top
                self.pos.y = self.rect.y
            elif move_vec.y < 0: #moving up
                self.rect.top = hit.rect.bottom
                self.pos.y = self.rect.y

        # 5. Sync the rect to the new position
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # Check for doors (checking both x and y collisions)
        collisions = x_collide + y_collide
        for tile in collisions:
            if tile.door and len(enemies) == 0:
                self.pos.x = SPAWN_X
                self.pos.y = SPAWN_Y
                self.rect.x = SPAWN_X
                self.rect.y = SPAWN_Y
                new_room = True
                player.rooms_cleared += 1

            if isinstance(tile, Candle) and not tile.lit:
                tile.lit = True
                self.wax = min(self.max_wax, self.wax + tile.wax_value)
                tile.image.fill((255, 200, 60))


class Button:
    def __init__(self, x, y, width, height, color, text=""):
        self.original_rect = pygame.Rect(x, y, width, height)
        self.rect = self.original_rect.copy()  # Copy for scaling
        self.color = color
        self.hovered = False
        self.text = text
        self.font = pygame.font.Font(None, 36)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
        
        if self.text:
            text_surface = self.font.render(self.text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()

        # Hover effect
        if self.original_rect.collidepoint(mouse_pos):
            if not self.hovered:
                self.hovered = True
                self.rect.inflate_ip(self.original_rect.width * (HOVER_SCALE - 1), 
                                     self.original_rect.height * (HOVER_SCALE - 1))
                self.rect.center = self.original_rect.center  
        else:
            if self.hovered:
                self.hovered = False
                self.rect = self.original_rect.copy()  

    def is_clicked(self, event):
        """Returns True if the button is clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):  # Left-click
                return True
        return False
    
class Flame: #main spell class
    def __init__(self, width, height, buffer, colour, direction, duration, wide=False, x=-999, y=-999):
        global flame_render, flame_timer, flameSelected, slot
        self.identity = flameSelected
        self.width = width
        self.height = height
        self.buffer = buffer
        self.colour = colour
        self.direction = direction
        self.duration = duration
        self.wide = wide
        self.x = x
        self.y = y
        self.true_width = self.width
        self.true_height = self.height
        self.growth = 1.1
        flame_timer = duration
        flame_render = True
        if slot < 3:
            slot += 1
        else:
            slot = 1
        self.rect = pygame.rect.Rect(x, y, width, height)

    def orientate(self):
        if self.direction == "UP":
            self.rect.centerx = player.rect.centerx
            self.rect.bottom = player.rect.top - self.buffer
        elif self.direction == "DOWN":
            self.rect.centerx = player.rect.centerx
            self.rect.top = player.rect.bottom + self.buffer
        elif self.direction == "LEFT":
            if (self.height > self.width and not self.wide) or (self.height < self.width and self.wide):
                self.rect = pygame.rect.Rect(self.x, self.y, self.height, self.width)
            self.rect.right = player.rect.left - self.buffer
            self.rect.centery = player.rect.centery
        elif self.direction == "RIGHT":
            if (self.height > self.width and not self.wide) or (self.height < self.width and self.wide): 
                self.rect = pygame.rect.Rect(self.x, self.y, self.height, self.width)
            self.rect.left = player.rect.right + self.buffer
            self.rect.centery = player.rect.centery
    
    def draw(self):
        if flame_render:
            self.orientate()
            pygame.draw.rect(screen, self.colour, self.rect)
    
    def update(self):
        #flicker effect
        if flame_timer == 5*(self.duration / 6):
            self.width = self.true_width * self.growth
            self.height = self.true_height * self.growth
        elif flame_timer == 4*(self.duration / 6):
            self.width = self.true_width * self.growth ** 2
            self.height = self.true_height * self.growth ** 2
        elif flame_timer == 3*(self.duration / 6):
            self.width = self.true_width * self.growth ** 2
            self.height = self.true_height * self.growth ** 2
        elif flame_timer == 2*(self.duration / 6):
            self.width = self.true_width * self.growth
            self.height = self.true_height * self.growth
        elif flame_timer == (self.duration / 6):
            self.width = self.true_width
            self.height = self.true_height
        
        try:
            self.rect = pygame.rect.Rect(self.x, self.y, self.width, self.height)
        except UnboundLocalError:
            pass

        self.orientate()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        data = ENEMY_DATA[type]

        self.name = data["name"]
        self.speed = data["speed"]
        self.range = data["range"]
        self.damage = data["damage"]

        size = data["size"]
        self.image = pygame.Surface((size, size))
        self.image.fill(data["colour"])
        self.rect = self.image.get_rect(center=(x, y))

        self.pos = pygame.math.Vector2(x, y)
        self.path = [] #list of tiles to folllow
        self.path_index = 0
        self.aim = None
        self.attack_cooldown = 0

    def update(self, player_pos, other_enemies):

        velocity = pygame.math.Vector2(0, 0)

        #aim + attack
        to_player = player_pos - self.pos

        if to_player.length() > 0:
            if abs(to_player.x) > abs(to_player.y):
                self.aim = "RIGHT" if to_player.x > 0 else "LEFT"
            else:
                self.aim = "DOWN" if to_player.y > 0 else "UP"

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if to_player.length() < self.range and self.attack_cooldown == 0:
            self.attack()


        if self.path and self.path_index < len(self.path):
            target_tile = self.path[self.path_index]
            #convert target to pixel coords
            target_px, target_py, = grid_to_pixel(target_tile[0], target_tile[1])
            target = pygame.math.Vector2(target_px, target_py)

            to_target = target - self.pos

            if to_target.length() < self.speed:
                self.path_index += 1

            else:
                velocity = to_target.normalize() * self.speed

        #enemy collision
        self.pos.x += velocity.x
        self.rect.centerx = round(self.pos.x)

        x_collide = pygame.sprite.spritecollide(self, solids_group, False)
        if x_collide and velocity.x != 0:
            if velocity.x > 0:
                # moving right — stop at the leftmost wall we hit
                self.rect.right = min(hit.rect.left for hit in x_collide)
            else:
                # moving left — stop at the rightmost wall we hit
                self.rect.left = max(hit.rect.right for hit in x_collide)
            self.pos.x = self.rect.centerx

        #y collision
        self.pos.y += velocity.y
        self.rect.centery = round(self.pos.y)

        y_collide = pygame.sprite.spritecollide(self, solids_group, False)
        if y_collide and velocity.y != 0:
            if velocity.y > 0:
                self.rect.bottom = min(hit.rect.top for hit in y_collide)
            else:
                self.rect.top = max(hit.rect.bottom for hit in y_collide)
            self.pos.y = self.rect.centery

        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def attack(self):
        enemy_attacks.append(EnemyAttack(self, self.aim, damage=self.damage))
        self.attack_cooldown = 90

    def recalculate_path(self, player_pos):
        start = pixel_to_grid(self.pos.x, self.pos.y)
        goal = pixel_to_grid(player_pos.x, player_pos.y)
        self.path = find_path(start, goal)
        self.path_index = 1 #start new path from [1]

class EnemyAttack:
    def __init__(self, enemy, direction, duration=15, damage=10):

        self.direction = direction
        self.duration = duration
        self.damage = damage
        self.enemy = enemy
        self.has_hit = False        # so one swipe can't hit twice
        self.colour = (200, 40, 40)

        # size: long across the swipe, thin along it
        if direction in ("UP", "DOWN"):
            self.rect = pygame.Rect(0, 0, 40, 24)
        else:
            self.rect = pygame.Rect(0, 0, 24, 40)


    def update(self):
        self.duration -= 1

        buffer = 4
        if self.direction == "UP":
            self.rect.centerx = self.enemy.rect.centerx
            self.rect.bottom = self.enemy.rect.top - buffer
        elif self.direction == "DOWN":
            self.rect.centerx = self.enemy.rect.centerx
            self.rect.top = self.enemy.rect.bottom + buffer
        elif self.direction == "LEFT":
            self.rect.centery = self.enemy.rect.centery
            self.rect.right = self.enemy.rect.left - buffer
        elif self.direction == "RIGHT":
            self.rect.centery = self.enemy.rect.centery
            self.rect.left = self.enemy.rect.right + buffer


    def draw(self, surface):
        pygame.draw.rect(surface, self.colour, self.rect)


# --- CELLULAR AUTOMATA GENERATION FUNCTIONS ---

def generate_noise_map(width, height, fill_prob=0.45):
    """Fills grid with noise. Returns as [row][col] to match pygame rendering."""
    map_grid = []
    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                row.append(1) # Solid outer border
            else:
                row.append(1 if random.random() < fill_prob else 0)
        map_grid.append(row)
    return map_grid

def get_surrounding_wall_count(map_grid, grid_x, grid_y, width, height):
    wall_count = 0
    for neighbor_y in range(grid_y - 1, grid_y + 2):
        for neighbor_x in range(grid_x - 1, grid_x + 2):
            if 0 <= neighbor_x < width and 0 <= neighbor_y < height:
                if neighbor_x != grid_x or neighbor_y != grid_y:
                    wall_count += map_grid[neighbor_y][neighbor_x]
            else:
                wall_count += 1
    return wall_count

def smooth_map(map_grid, width, height):
    new_grid = [[0 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            neighbor_walls = get_surrounding_wall_count(map_grid, x, y, width, height)
            if neighbor_walls > 4:
                new_grid[y][x] = 1
            elif neighbor_walls < 4:
                new_grid[y][x] = 0
            else:
                new_grid[y][x] = map_grid[y][x]
    return new_grid

def generate_cave(width, height, fill_prob=0.45, iterations=4):
    cave = generate_noise_map(width, height, fill_prob)
    for _ in range(iterations):
        cave = smooth_map(cave, width, height)
        
    # FORCE CLEAR SPAWN AREA so player doesn't spawn in a wall
    # Player spawns at pixel 464, 304 -> Roughly column 14, row 9
    for sy in range(8, 12):
        for sx in range(13, 17):
            cave[sy][sx] = 0
            
    return cave

def place_door(reachable): #places exit door on valid tile
    candidates = [t for t in reachable if dungeon_grid[t[1]][t[0]] == 0]
    if not candidates:
        return False

    col, row = random.choice(candidates)
    dungeon_grid[row][col] = 2
    return True


def load_room(room_data, target_group):
    target_group.empty()
    tile_size = 32

    for row_index, row in enumerate(room_data):
        for col_index, tile in enumerate(row):

            x = col_index * 32
            y = row_index * 32

            if tile == 1:
                new_wall = Wall(x, y, tile_size)
                target_group.add(new_wall)
            elif tile == 2:
                new_door = Wall(x, y, tile_size, True)
                target_group.add(new_door)

#A* & helper functions
def pixel_to_grid(pixel_x, pixel_y):
    col = int(pixel_x // TILE_SIZE)
    row = int(pixel_y // TILE_SIZE)
    return(col, row)

def grid_to_pixel(col, row):
    pixel_x = col * TILE_SIZE + TILE_SIZE // 2
    pixel_y = row * TILE_SIZE + TILE_SIZE // 2
    return(pixel_x, pixel_y) #returns pixel coords of center of tile

def is_walkable(col, row):
    if row < 0 or row >= len(dungeon_grid):
        return False
    if col < 0 or col >= len(dungeon_grid[0]):
        return False
    return dungeon_grid[row][col] == 0

def heuristic(tile_a, tile_b):
    (col_a, row_a) = tile_a
    (col_b, row_b) = tile_b
    return abs(col_a - col_b) + abs(row_a - row_b)

def find_path(start, goal):
    #open set = tiles discovered but not explored [(f_cost, tile)]
    open_set = [(0, start)]

    #came from = tiles walked so we can reconstruct path {a tile, tile came from}
    came_from = {}

    #g cost = total steps taken to goal {tile, number of steps}
    g_cost = {start: 0}

    while len(open_set) > 0:
        #find open_set with least f_cost
        open_set.sort()
        current_f, current = open_set.pop(0)

        #at goal, reconstruct path
        if current == goal:
            return reconstruct_path(came_from, current)
        
        #check neighbours
        (col, row) = current
        neighbours = [(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)]

        for nb in neighbours:
            (n_col, n_row) = nb

            if not is_walkable(n_col, n_row):
                continue

            #nb cost = current cost + 1
            tentative_g = g_cost[current] + 1

            if nb not in  g_cost or tentative_g < g_cost[nb]:
                #record better route if we know neighbouring route
                came_from[nb] = current
                g_cost[nb] = tentative_g
                #f = g (real cost so far) + h (estimated cost to goal)
                f_cost = tentative_g + heuristic(nb, goal)
                open_set.append((f_cost, nb))

    #open set emptied w/o solution = no path exists
    return []

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse() #we found the backwards path - now we store the true path
    return path


def locate_candle(count, reachable):
    spots = []
    attempts = 0
    while len(spots) < count and attempts < 500:
        attempts += 1
        col = random.randint(1, len(dungeon_grid[0]) - 2)
        row = random.randint(1, len(dungeon_grid) - 2)

        #filters for valid placing locations
        if dungeon_grid[row][col] != 0: 
            continue
        if (col, row) not in reachable:
            continue

        wall_neighbours = 0
        if dungeon_grid[row-1][col] == 1:
            wall_neighbours += 1
        if dungeon_grid[row+1][col] == 1:
            wall_neighbours += 1
        if dungeon_grid[row][col-1] == 1:
            wall_neighbours += 1
        if dungeon_grid[row][col+1] == 1:
            wall_neighbours += 1


        if wall_neighbours >= 1 and wall_neighbours < 4:
            px, py = grid_to_pixel(col, row)
            spots.append((px, py))

    return spots

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 120, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BROWN = (150, 80, 0)
DARK_BROWN = (70, 40, 10)
HOVER_SCALE = 1.2
flame_render = False
flame_timer = 0
flameSelected = None
frame = 0
new_room = True
slot = 1 
paused = False
gameOver = False
showDebug = False
showASTAR = False

dungeon_grid = []
solids_group = pygame.sprite.Group()

SPAWN_X = 464
SPAWN_Y = 304
player = Player(SPAWN_X, SPAWN_Y)
flames = []
enemies = []
enemy_attacks = []
candles = []
SPELL_DATA = [
    {"width": 30, "height": 30, "colour": ORANGE, "wide": False, "cost": 15},
    {"width": 25, "height": 40, "colour": RED,    "wide": False, "cost": 20},
    {"width": 80, "height": 60, "colour": GREEN,  "wide": True, "cost": 30}  
]
ENEMY_DATA = [
    {"name": "shade",   "colour": (90, 90, 110),  "speed": 5, "damage": 8,  "range": 50,  "size": 32},
    {"name": "brute",   "colour": (140, 70, 70),  "speed": 2, "damage": 20, "range": 70,  "size": 40},
    {"name": "wisp",    "colour": (70, 130, 140), "speed": 7, "damage": 5,  "range": 45,  "size": 26},
]
PATH_COLOURS = [
    (0, 200, 255),    # cyan
    (255, 120, 200),  # pink
    (150, 255, 120),  # lime
    (255, 200, 60),   # gold
    (180, 140, 255),  # violet
]

start_menu = True
start_button = Button(425, 225, 150, 60, WHITE, "Play")

#subroutines
def draw_queue(): #draws a spell queue in the bottom left
    slot_size = 50
    padding = 10
    ui_y = screen.get_height() - 70
    scale = 0.4 

    for i, data in enumerate(SPELL_DATA):
        box_rect = pygame.Rect(20 + i * (slot_size + padding), ui_y, slot_size, slot_size)
        pygame.draw.rect(screen, (40, 40, 40), box_rect) 
        
        border_col = (255, 255, 255) if (i + 1) == slot else (80, 80, 80)
        pygame.draw.rect(screen, border_col, box_rect, 2)

        mini_w = data["width"] * scale
        mini_h = data["height"] * scale
        
        mini_rect = pygame.Rect(0, 0, mini_w, mini_h)
        mini_rect.center = box_rect.center
        
        pygame.draw.rect(screen, data["colour"], mini_rect)

def draw_wax(): #draws the player's current wax bar in top left corner
    wax_ratio = max(0, player.wax / player.max_wax)
    bar_x, bar_y = 20, 20
    bar_width, bar_height = 200, 25

    pygame.draw.rect(screen, (60, 40, 30), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (255, 180, 50), (bar_x, bar_y, bar_width * wax_ratio, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

def draw_hud(): #combines hud/ui components into one callable function
    draw_queue()
    draw_wax()

def check_quit(event): #exits if window closed
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

def handle_menu_events(): #processes various menu events
    for event in pygame.event.get():
        check_quit(event)
        if start_button.is_clicked(event):
            return True
    return False

def handle_game_events(): #processes gameplay events
    global paused, showDebug, showASTAR
    for event in pygame.event.get():
        check_quit(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            paused = not paused

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            showDebug = not showDebug

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F4 and showDebug:
                    showASTAR = not showASTAR
        

def get_current_spell(): #returns stats of currently selected spell
    data = SPELL_DATA[slot - 1]
    padding = 20 if slot == 3 else 10
    return data["width"], data["height"], padding, data["colour"], data["wide"]

def handle_spell_casting(): #casts spell in chozen direction if requirements met

    if flame_render:
        return                      # already casting, ignore input

    cost = SPELL_DATA[slot - 1]["cost"]
    if player.wax < cost:
        return                      # can't afford it

    width, height, padding, colour, is_wide = get_current_spell()
    key = pygame.key.get_pressed()

    direction = None
    if key[pygame.K_UP]:
        direction = "UP"
    elif key[pygame.K_DOWN]:
        direction = "DOWN"
    elif key[pygame.K_LEFT]:
        direction = "LEFT"
    elif key[pygame.K_RIGHT]:
        direction = "RIGHT"

    if direction is not None:
        flames.append(Flame(width, height, padding, colour, direction, 60, is_wide))
        player.wax -= cost

def draw_world(): #draws dungeon, player, enemies and attacks
    screen.fill(BLACK)
    solids_group.draw(screen)
    screen.blit(player.image, player.rect)

    for e in enemies:
        screen.blit(e.image, e.rect)

    for atk in enemy_attacks:
        atk.draw(screen)

    if flame_render:
        for f in flames:
            f.update()
            f.draw()

def update_timers(): #updates various game timers
    global frame, flame_timer, flame_render, flameSelected

    frame += 1
    if frame >= 60:
        frame = 0

    player.wax -= 0.01

    if flame_timer > 0:
        flame_timer -= 1
    else:
        flame_timer = 0
        flame_render = False
        flames.clear()
        if flameSelected is not None:
            flameSelected.x = -999
            flameSelected.y = -999

def update_entities(): #updates player, enemies and active attacks
    player.update(solids_group)

    target_pos = pygame.math.Vector2(player.rect.center)
    for e in enemies:
        if frame % 30 == 0:
            e.recalculate_path(target_pos)
        e.update(target_pos, enemies)

    for atk in enemy_attacks[:]:
        atk.update()
        if atk.duration <= 0:
            enemy_attacks.remove(atk)

def check_collisions(): #handles player/enemy to flame interactions
    # flames damaging enemies
    for f in flames:
        for e in enemies[:]:
            if f.rect.colliderect(e.rect):
                enemies.remove(e)
                player.score += 10

    # flames damaging the player
    for atk in enemy_attacks:
        if not atk.has_hit and atk.rect.colliderect(player.rect):
            atk.has_hit = True
            player.wax -= atk.damage

def reset_dungeon(): #resets dungeon map and entities
    global dungeon_grid, door_locked

    chosen_room = generate_cave(30, 20, fill_prob=0.45, iterations=4)
    dungeon_grid = chosen_room

    spawn_col, spawn_row = pixel_to_grid(SPAWN_X, SPAWN_Y)
    reachable = find_reachable_tiles(spawn_col, spawn_row)

    enemy_count = 2 + (player.rooms_cleared // 2) #+1 every 2 rooms
    enemy_count = min(enemy_count, 8)

    place_door(reachable)
    spawn_enemies(enemy_count, reachable)

    load_room(chosen_room, solids_group)#build sprites after everything is placed
    place_candles(2, reachable) #candles overlay the dungeon layout

def place_candles(count, reachable): #generates candles in wall nooks and adds collision
    candles.clear()
    for spot in locate_candle(count, reachable):
        candle = Candle(spot[0], spot[1])
        candles.append(candle)
        solids_group.add(candle)
        col, row = pixel_to_grid(spot[0], spot[1])
        dungeon_grid[row][col] = 1      # block pathfinding through the candle

def spawn_enemies(count, reachable): #clear enemies and begin new wave
    enemies.clear()

    spots = []
    attempts = 0
    while len(spots) < count and attempts < 500:
        attempts += 1
        enemy_type = random.randint(0, len(ENEMY_DATA) - 1)#choose enemy type
        col = random.randint(1, len(dungeon_grid[0]) - 2)
        row = random.randint(1, len(dungeon_grid) - 2)

        # oversized enemies need clear neighbouring tiles to fit
        if ENEMY_DATA[enemy_type]["size"] > TILE_SIZE:
            neighbours_clear = (
                is_walkable(col + 1, row) and
                is_walkable(col - 1, row) and
                is_walkable(col, row + 1) and
                is_walkable(col, row - 1)
            )
            if not neighbours_clear:
                continue

        #filter for valid placing locations
        if dungeon_grid[row][col] != 0:
            continue
        if (col, row) not in reachable:
            continue

        px, py = grid_to_pixel(col, row)
        spots.append((px, py, enemy_type))

    for spot in spots:
        enemies.append(Enemy(spot[0], spot[1], spot[2]))

def check_death():
    return player.wax <= 0

def debug_reset(): #allows for debug reset
    global new_room
    if pygame.key.get_pressed()[pygame.K_r]:
        player.pos.x = SPAWN_X
        player.pos.y = SPAWN_Y
        player.rect.x = SPAWN_X
        player.rect.y = SPAWN_Y
        new_room = True

def draw_stats(): #draws relevant player scores
    font = pygame.font.Font(None, 28)
    score_text = font.render(f"Score: {player.score}", True, WHITE)
    rooms_text = font.render(f"Rooms: {player.rooms_cleared}", True, WHITE)

    screen.blit(score_text, (screen.get_width() - 150, 20))
    screen.blit(rooms_text, (screen.get_width() - 150, 50))

def draw_pause_menu(): #draws overlay with controls and player stats
    overlay = pygame.Surface((screen.get_width(), screen.get_height()))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    font_large = pygame.font.Font(None, 64)
    font_small = pygame.font.Font(None, 28)

    title = font_large.render("PAUSED", True, (255, 200, 60))
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 100)))

    profile = database.get_profile()

    lines = [
        "WASD - Move",
        "Arrow Keys - Cast spell in that direction",
        "Spells rotate automatically after each cast",
        "Walk into a dowsed candle to relight it and restore wax",
        "Your wax is both your health and your mana",
        "ESC - Resume",
        "",
        f"Best score: {profile['highscore']}   Total runs: {profile['total_runs']}",
    ]

    y = 190
    for line in lines:
        text = font_small.render(line, True, WHITE)
        screen.blit(text, text.get_rect(center=(screen.get_width() // 2, y)))
        y += 36

def draw_game_over(): #draws end-run screen with final stats
    overlay = pygame.Surface((screen.get_width(), screen.get_height()))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    font_large = pygame.font.Font(None, 72)
    font_small = pygame.font.Font(None, 32)

    title = font_large.render("EXTINGUISHED", True, (200, 40, 40))
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 180)))

    lines = [
        f"Final score: {player.score}",
        f"Rooms cleared: {player.rooms_cleared}",
        "",
        "Press SPACE to return to menu",
    ]

    y = 280
    for line in lines:
        text = font_small.render(line, True, WHITE)
        screen.blit(text, text.get_rect(center=(screen.get_width() // 2, y)))
        y += 40

def draw_debug(): #displays runtime diagnostics, toggled by F3
    font = pygame.font.Font(None, 22)

    player_tile = pixel_to_grid(player.pos.x, player.pos.y)

    lines = [
        f"FPS: {clock.get_fps():.1f}",
        f"Entities: {len(enemies)} enemies, {len(flames)} flames, {len(enemy_attacks)} attacks",
        f"Candles: {sum(1 for c in candles if c.lit)}/{len(candles)} lit",
        f"Player tile: {player_tile}",
        f"Wax: {player.wax:.1f} / {player.max_wax}",
        f"Spell slot: {slot}",
        f"To display A*, hit F4",
    ]

    x = screen.get_width() - 260
    y = 5
    for line in lines:
        text = font.render(line, True, (0, 255, 0))
        screen.blit(text, (x, y))
        y += 20

def draw_ASTAR(): #draws each enemy's A* path as connected by line segments
    for i, e in enumerate(enemies):
        if e.path_index >= len(e.path):
            continue

        colour = PATH_COLOURS[i % len(PATH_COLOURS)]
        remaining = [grid_to_pixel(t[0], t[1]) for t in e.path[e.path_index:]]

        # route from the enemy through its remaining waypoints
        route = [(int(e.pos.x), int(e.pos.y))] + remaining
        if len(route) > 1:
            pygame.draw.lines(screen, colour, False, route, 2)

        # marker on the destination
        pygame.draw.circle(screen, colour, remaining[-1], 5, 2)

def colour_door():
        locked = len(enemies) > 0
        for tile in solids_group:
            if getattr(tile, "door", False):
                tile.image.fill(DARK_BROWN if locked else BROWN)

def find_reachable_tiles(start_col, start_row): #returns set of tiles reachable from start tile
    reachable = set()
    frontier = [(start_col, start_row)]

    while frontier:
        col, row = frontier.pop()
        if (col, row) in reachable:
            continue
        if not is_walkable(col, row):
            continue

        reachable.add((col, row))
        frontier.append((col + 1, row))
        frontier.append((col - 1, row))
        frontier.append((col, row + 1))
        frontier.append((col, row - 1))

    return reachable

#initialise
while True:
    #menu loop
    while start_menu == True:

        screen.fill(BLACK)

        buttons = [start_button]
        for button in buttons:
            button.update()
            button.draw(screen)

        if handle_menu_events():
            start_menu = False

        #setting important player values
        player.wax = player.max_wax
        player.score = 0
        player.rooms_cleared = 0

        player.pos.x = SPAWN_X
        player.pos.y = SPAWN_Y
        player.rect.x = SPAWN_X
        player.rect.y = SPAWN_Y

        slot = 1

        pygame.display.update()
        clock.tick(FPS)
        if frame == 60:
            frame = 0
            frame += 1

    #game loop
    while start_menu == False:

        if new_room:
            reset_dungeon()
            new_room = False

        handle_game_events()

        if not paused:
            update_timers()
            handle_spell_casting()
            update_entities()
            check_collisions()
            colour_door()

        draw_world()
        draw_hud()

        if paused:
            draw_pause_menu()
            draw_stats()

        if showDebug:
            draw_debug()
            debug_reset()
            if showASTAR:
                draw_ASTAR()

        if check_death():
            database.record_run(player.score, player.rooms_cleared)
            start_menu = True
            gameOver = True

        pygame.display.update()
        clock.tick(FPS)
        

    while gameOver:
        for event in pygame.event.get():
            check_quit(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                gameOver = False
                start_menu = True

        draw_game_over()
        pygame.display.update()
        clock.tick(FPS)