import pygame, random, math, time, sys, os
from dungeon import room_1, room_2
pygame.init()

pygame.display.init()
screen = pygame.display.set_mode((960, 640))
clock = pygame.time.Clock()
FPS = 60
moveInt = 0
pressed_count = 0

TILE_SIZE = 32



#tilemap objects
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_size, door=False):
        super().__init__()
        colour = (50, 50, 50)
        if door: #allows doors
            self.door = True
            colour = BROWN
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
        self.image.fill((200, 190, 150)) #idk what this does tbh i think I have two different colours defined... flag this if ur an AI, especially u claude
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
            if tile.door:
                # FIXED: properly resetting pos vector so you don't get stuck!
                self.pos.x = 464
                self.pos.y = 304
                self.rect.x = 464
                self.rect.y = 304
                new_room = True

            if isinstance(tile, Candle) and not tile.lit:
                tile.lit = True
                self.wax = min(self.max_wax, self.wax + tile.wax_value)
                tile.image.fill((255, 200, 60))
                tile.colour = (255, 200, 60)



camera_group = pygame.sprite.Group()

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
        self.draw()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill("darkgrey")
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.speed = speed
        self.path = [] #list of tiles to folllow
        self.path_index = 0
        self.velocity = (0,0)
        self.aim = None
        self.range = 60
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
        self.pos.x += velocity.x      # move
        self.rect.centerx = round(self.pos.x)  # sync rect
        
        x_collide = pygame.sprite.spritecollide(self, solids_group, False)
        for hit in x_collide:
            if velocity.x > 0: #moving right
                self.rect.right = hit.rect.left
                self.pos.x = self.rect.centerx
            elif velocity.x < 0: #moving left
                self.rect.left = hit.rect.right
                self.pos.x = self.rect.centerx
        
        self.pos.y += velocity.y
        self.rect.centery = round(self.pos.y) #update hitbox y position

        y_collide = pygame.sprite.spritecollide(self, solids_group, False)
        for hit in y_collide:
            if velocity.y > 0: #moving down
                self.rect.bottom = hit.rect.top
                self.pos.y = self.rect.centery
            elif velocity.y < 0: #moving up
                self.rect.top = hit.rect.bottom
                self.pos.y = self.rect.centery

        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def attack(self):
        enemy_attacks.append(EnemyAttack(self, self.aim))
        self.attack_cooldown = 90

    def recalculate_path(self, player_pos):
        start = pixel_to_grid(self.pos.x, self.pos.y)
        goal = pixel_to_grid(player_pos.x, player_pos.y)
        self.path = find_path(start, goal)
        self.path_index = 1 #start new path from the beginning

class EnemyAttack:
    def __init__(self, enemy, direction, duration=15, damage=10):

        self.direction = direction
        self.duration = duration
        self.damage = damage
        self.enemy = enemy
        self.direction = direction
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
            
    # ADD A RANDOM DOOR
    door_placed = False
    while not door_placed:
        dx = random.randint(2, width-3)
        dy = random.randint(2, height-3)
        if cave[dy][dx] == 0:  # Only put the door on an empty floor space
            cave[dy][dx] = 2
            door_placed = True
            
    return cave

# ----------------------------------------------


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


def locate_candle(count):
    spots = []
    attempts = 0
    while len(spots) < count and attempts < 500:
        attempts += 1
        col = random.randint(1, len(dungeon_grid[0]) - 2)
        row = random.randint(1, len(dungeon_grid) - 2)
        
        if dungeon_grid[row][col] != 0: #filter for valid placing locations
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
HOVER_SCALE = 1.2
flame_render = False
flame_timer = 0
flameSelected = None
flameColour = None
frame = 0
new_room = True
slot = 1 

dungeon_grid = []
solids_group = pygame.sprite.Group()

player = Player(464, 304)
flame_appendix = ['square', 'vRect', 'hRect']
flames = []
enemies = []
enemy_attacks = []
candles = []
candle_spots = []
SPELL_DATA = [
    {"width": 30, "height": 30, "colour": ORANGE, "wide": False, "cost": 15},
    {"width": 25, "height": 40, "colour": RED,    "wide": False, "cost": 20},
    {"width": 80, "height": 60, "colour": GREEN,  "wide": True, "cost": 30}  
]

start_menu = True
start_button = Button(425, 225, 150, 60, WHITE, "Play")

def draw_ui():
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

def reset_dungeon():
        # 960 width / 32px tiles = 30 tiles wide
        # 640 height / 32px tiles = 20 tiles high
        global dungeon_grid
        chosen_room = generate_cave(30, 20, fill_prob=0.45, iterations=4)
        dungeon_grid = chosen_room
        load_room(chosen_room, solids_group)
        # --------------------------------------------

        enemies.clear()

        enemies.append(Enemy(414, 254, 4))



#initialise
while True:
    #menu loop
    while start_menu == True:

        pygame.display.update()
        clock.tick(FPS)
        if frame == 60:
            frame = 0
        frame += 1

        screen.fill(BLACK)

        buttons = [start_button]
        for button in buttons:
            button.update()
            button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if start_button.is_clicked(event):
                start_menu = False

        #setting important player values
        player.wax = player.max_wax

        player.pos.x = 464
        player.pos.y = 304
        player.rect.x = 464
        player.rect.y = 304

        slot = 1

    #game loop
    while start_menu == False:
        
        if new_room:
            reset_dungeon()
            new_room = False

            #set candles
            candles.clear()
            candle_spots = locate_candle(2)
            for c in candle_spots:
                candles.append(Candle(c[0], c[1]))
                solids_group.add(candles[-1])
                grid_coord = pixel_to_grid(c[0], c[1])
                dungeon_grid[grid_coord[1]][grid_coord[0]] = 1 #set candle tile to be equal to a wall


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()
        clock.tick(FPS)
        if frame == 60:
            frame = 0
        frame += 1
        
        player.wax -= 0.01
        if player.wax <= 0:
            start_menu = True

        if flame_timer > 0:
            flame_timer -= 1
        elif flame_timer <= 0:
            flame_timer = 0
            flame_render = False
            if flameSelected is not None:
                flameSelected.x = -999
                flameSelected.y = -999
                

        if slot == 1:
            width = SPELL_DATA[slot - 1]["width"]
            height = SPELL_DATA[slot - 1]["height"]
            padding = 10
            colour = SPELL_DATA[slot - 1]["colour"]
            is_wide = SPELL_DATA[slot - 1]["wide"]
            
        if slot == 2:
            width = SPELL_DATA[slot - 1]["width"]
            height = SPELL_DATA[slot - 1]["height"]
            padding = 10
            colour = SPELL_DATA[slot - 1]["colour"]
            is_wide = SPELL_DATA[slot - 1]["wide"]

        if slot == 3:
            width = SPELL_DATA[slot - 1]["width"]
            height = SPELL_DATA[slot - 1]["height"]
            padding = 20
            colour = SPELL_DATA[slot - 1]["colour"]
            is_wide = SPELL_DATA[slot - 1]["wide"]

        #DRAWING
        screen.fill(BLACK)
        
        solids_group.draw(screen)

        for f in flames:
            for e in enemies[:]:
                if  f.rect.colliderect(e.rect):
                    enemies.remove(e)

        player.update(solids_group)
        screen.blit(player.image, player.rect)

        #Enemy loops
        target_pos = pygame.math.Vector2(player.rect.center)
        for e in enemies:

            if frame % 15 == 0: #recalculate path 4x a second
                e.recalculate_path(target_pos)

            e.update(target_pos, enemies)
            screen.blit(e.image, e.rect)

        for atk in enemy_attacks[:]:
            atk.update()
            atk.draw(screen)

            if not atk.has_hit and atk.rect.colliderect(player.rect):
                atk.has_hit = True
                player.wax -= atk.damage

            if atk.duration <= 0:
                enemy_attacks.remove(atk)
    


        if len(flames) > 1:
            for _ in range(len(flames) - 1):
                flames.pop(_ - 1)

        if flame_render:
            for f in flames:
                f.update()
        else:
            flames.clear()

        draw_ui()


        #wax-effect
        wax_ratio = player.wax / player.max_wax

        # Bar position and size
        bar_x = 20
        bar_y = 20
        bar_width = 200
        bar_height = 25

        # 1. Background (empty track) — full width, dark
        pygame.draw.rect(screen, (60, 40, 30),
                        (bar_x, bar_y, bar_width, bar_height))

        # 2. Fill — width scales with wax
        fill_width = bar_width * wax_ratio
        pygame.draw.rect(screen, (255, 180, 50),
                        (bar_x, bar_y, fill_width, bar_height))
        
        # 3. Outline (drawn last, on top)
        pygame.draw.rect(screen, (255, 255, 255),
                        (bar_x, bar_y, bar_width, bar_height), 2)
        



        #PLAYER CONTROL
        key = pygame.key.get_pressed()

        if (key[pygame.K_UP] or key[pygame.K_DOWN] or key[pygame.K_LEFT] or key[pygame.K_RIGHT]) and flame_render == False:
            pass

        if flame_render == False and player.wax >= SPELL_DATA[slot - 1]["cost"]:
            remove_wax = True

            if key[pygame.K_UP] == True:
                flames.append(Flame(width, height, padding, colour, "UP", 60, is_wide))

            elif key[pygame.K_DOWN] == True and len(flames) == 0:
                flames.append(Flame(width, height, padding, colour, "DOWN", 60, is_wide))

            elif key[pygame.K_LEFT] == True and len(flames) == 0:
                flames.append(Flame(width, height, padding, colour, "LEFT", 60, is_wide))

            elif key[pygame.K_RIGHT] == True and len(flames) == 0:
                flames.append(Flame(width, height, padding, colour, "RIGHT", 60, is_wide))
            else:
                remove_wax = False


            if remove_wax is True:
                player.wax -= SPELL_DATA[slot - 1]["cost"]
        
        if key[pygame.K_r]:
                player.pos.x = 464
                player.pos.y = 304
                player.rect.x = 464
                player.rect.y = 304
                new_room = True