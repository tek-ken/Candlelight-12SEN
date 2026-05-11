import pygame, random, math, time, sys, os
from dungeon import room_1, room_2
pygame.init()

pygame.display.init()
screen = pygame.display.set_mode((960, 640))
clock = pygame.time.Clock()
FPS = 60
moveInt = 0
pressed_count = 0



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


#basic objects
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        #visuals
        self.image = pygame.Surface((50, 50))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Store position as a Vector2 for smooth float precision
        self.pos = pygame.math.Vector2(x, y)
        self.speed = 7

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

    def update(self, player_pos, other_enemies):
        direction = player_pos - self.pos
        velocity = pygame.math.Vector2(0, 0)
        
        if direction.length() > 5:
            velocity = direction.normalize() * self.speed

        separation = pygame.math.Vector2(0, 0)
        for other in other_enemies:
            if other == self: continue 
            
            dist = self.pos.distance_to(other.pos)
            if 0 < dist < 40: 
                diff = self.pos - other.pos
                separation += diff.normalize() / dist 

        velocity += separation * 50
        
        if velocity.length() > 0:
            velocity = velocity.normalize() * self.speed

        self.pos += velocity
        self.rect.center = (round(self.pos.x), round(self.pos.y))


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

wall_group = pygame.sprite.Group()

player = Player(464, 304)
flame_appendix = ['square', 'vRect', 'hRect']
flames = []
enemies = []
enemies.append(Enemy(500, 500, 4))
SPELL_DATA = [
    {"width": 30, "height": 30, "colour": ORANGE, "wide": False},
    {"width": 25, "height": 40, "colour": RED,    "wide": False},
    {"width": 80, "height": 60, "colour": GREEN,  "wide": True}  
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


#start loop
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


#game loop
while True:
    
    if new_room:
        # ---- IMPLEMENTED CELLULAR AUTOMATA HERE ----
        # 960 width / 32px tiles = 30 tiles wide
        # 640 height / 32px tiles = 20 tiles high
        chosen_room = generate_cave(30, 20, fill_prob=0.45, iterations=4)
        load_room(chosen_room, wall_group)
        new_room = False
        # --------------------------------------------

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()
    clock.tick(FPS)
    if frame == 60:
        frame = 0
    frame += 1

    if flame_timer > 0:
        flame_timer -= 1
    elif flame_timer <= 0:
        flame_timer = 0
        flame_render = False
        try:
            flameSelected.x = -999
            flameSelected.y = -999
        except AttributeError:
            pass

    if slot == 1:
        width = 30
        height = width
        padding = 10
        colour = ORANGE
        is_wide = None
    if slot == 2:
        width = 25
        height = 40
        padding = 10
        colour = RED
        is_wide = None
    if slot == 3:
        width = 80
        height = 60
        padding = 20
        colour = GREEN
        is_wide = True

    screen.fill(BLACK)
    
    wall_group.draw(screen)

    for f in flames:
        for e in enemies:
            if  f.rect.colliderect(e.rect):
                enemies.remove(e)

    player.update(wall_group)
    screen.blit(player.image, player.rect)

    target_pos = pygame.math.Vector2(player.rect.center)
    for e in enemies:
        e.update(target_pos, enemies)
        screen.blit(e.image, e.rect)
    
    if frame % 60 == 0 and 1 == 0:
        enemies.append(Enemy(random.randint(0, 1000), random.randint(0, 600), random.randint(1, 4)))

    if len(flames) > 1:
        for _ in range(len(flames) - 1):
            flames.pop(_ - 1)

    if flame_render:
        for f in flames:
            f.update()
    else:
        flames.clear()

    draw_ui()

    key = pygame.key.get_pressed()

    if (key[pygame.K_UP] or key[pygame.K_DOWN] or key[pygame.K_LEFT] or key[pygame.K_RIGHT]) and flame_render == False:
        pass

    if flame_render == False:
        if key[pygame.K_UP] == True:
            flames.append(Flame(width, height, padding, colour, "UP", 60, is_wide))

        if key[pygame.K_DOWN] == True and len(flames) == 0:
            flames.append(Flame(width, height, padding, colour, "DOWN", 60, is_wide))

        if key[pygame.K_LEFT] == True and len(flames) == 0:
            flames.append(Flame(width, height, padding, colour, "LEFT", 60, is_wide))

        if key[pygame.K_RIGHT] == True and len(flames) == 0:
            flames.append(Flame(width, height, padding, colour, "RIGHT", 60, is_wide))
    
    if key[pygame.K_r]:         
            # FIXED: properly resetting pos vector so you don't get stuck!
            player.pos.x = 464
            player.pos.y = 304
            player.rect.x = 464
            player.rect.y = 304
            new_room = True