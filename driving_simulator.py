from ursina import *
import random
from ursina.vec3 import Vec3
from math import radians, degrees, atan2, sin, cos
app = Ursina()
engine_sound = None
gear_shift_sound = None
def play_engine_sound(speed):
    global engine_sound
    if engine_sound is None:
        try:
            engine_sound = Audio('engine', loop=True, autoplay=False)
        except:
            engine_sound = None
    if engine_sound and not engine_sound.playing:
        try:
            engine_sound.play()
        except:
            pass
    if engine_sound:
        try:
            norm_speed = abs(speed) / 1000
            engine_sound.pitch = 1.0 + (norm_speed * 0.5)
            engine_sound.volume = 0.3 + (norm_speed * 0.4)
        except:
            pass
def play_gear_shift_sound():
    global gear_shift_sound
    if gear_shift_sound is None:
        try:
            gear_shift_sound = Audio('shift', loop=False, autoplay=False)
        except:
            gear_shift_sound = None
    if gear_shift_sound:
        try:
            gear_shift_sound.play()
        except:
            pass
def play_brake_sound():
    try:
        brake_sound = Audio('brake', loop=False, autoplay=False)
        brake_sound.play()
    except:
        pass
def play_collision_sound():
    try:
        collision_sound = Audio('collision', loop=False, autoplay=False)
        collision_sound.play()
    except:
        pass
window.title = '3D Driving Simulator'
window.borderless = False
window.fullscreen = True
window.exit_button.visible = True
window.fps_counter.enabled = True
window.color = color.rgb(20, 20, 30)
LOD_DISTANCE = 300 
CULL_DISTANCE = 600 
TRAFFIC_UPDATE_RATE = 0.2
SKID_MARK_LIMIT = 30
WEATHER_ENTITY_COUNT = 15
fps_counter = Text(text='FPS: 0', position=(-0.78, -0.48), scale=1.5, color=color.white, background=False)
frame_times = []
last_fps_update = 0
fps_update_interval = 0.5
is_paused = False
def show_pause_menu():
    global pause_menu, is_paused
    pause_menu.enabled = True
    mouse.locked = False
    is_paused = True
def hide_pause_menu():
    global pause_menu, is_paused
    pause_menu.enabled = False
    mouse.locked = True
    is_paused = False
ground = Entity(
    model='plane',
    scale=(10000,1,10000),
    color=color.white,
    texture='grass',
    texture_scale=(1500,1500),
    collider='box'
)
wall_thickness = 5
wall_height = 20
map_size = 10000 / 2
invisible_walls = [
    Entity(model='cube', scale=(10000, wall_height, wall_thickness), position=(0, wall_height/2, map_size), collider='box', visible=False),
    Entity(model='cube', scale=(10000, wall_height, wall_thickness), position=(0, wall_height/2, -map_size), collider='box', visible=False),
    Entity(model='cube', scale=(wall_thickness, wall_height, 10000), position=(map_size, wall_height/2, 0), collider='box', visible=False),
    Entity(model='cube', scale=(wall_thickness, wall_height, 10000), position=(-map_size, wall_height/2, 0), collider='box', visible=False),
]
grid_count = 3
road_spacing = 10000 // (grid_count-1)
road_length = 10000
road_width = 40
road_height = 0.1
road_y = 0.06
roads = []
for i in range(-(grid_count//2), grid_count//2+1):
    roads.append(Entity(
        model='cube',
        scale=(road_length, road_height, road_width),
        color=color.gray,
        texture='white_cube',
        texture_scale=(1,400),
        position=(0, road_y, i*road_spacing),
        collider='box'
    ))
    roads.append(Entity(
        model='cube',
        scale=(road_width, road_height, road_length),
        color=color.gray,
        texture='white_cube',
        texture_scale=(1,400),
        position=(i*road_spacing, road_y, 0),
        collider='box'
    ))

# Simplified intersections (only at major crossings)
for x in range(-(grid_count//2), grid_count//2+1):
    for z in range(-(grid_count//2), grid_count//2+1):
        if x == 0 and z == 0:
            continue
        Entity(
            model='cube',
            scale=(road_width, road_height+0.01, road_width),
            color=color.rgb(80,80,80),
            position=(x*road_spacing, road_y+0.01, z*road_spacing),
            collider=None
        )

# Simplified road markings (fewer lines)
for r in roads:
    for i in range(-8, 9, 4):  # Much reduced frequency
        Entity(
            model='cube',
            scale=(2, 0.12, 0.5),
            color=color.yellow,
            position=(r.position[0] + (i*120 if r.scale[2]>r.scale[0] else 0), road_y+0.07, r.position[2] + (i*120 if r.scale[0]>r.scale[2] else 0)),
            collider=None
        )

# Simplified streetlights (fewer)
for r in roads:
    for i in range(-6, 7, 12):  # Much sparser
        Entity(
            model='cube',
            scale=(0.3, 7, 0.3),
            color=color.rgb(200,200,180),
            position=(r.position[0] + (i*120 if r.scale[2]>r.scale[0] else 0), 3.5, r.position[2] + (i*120 if r.scale[0]>r.scale[2] else 0)),
            collider=None
        )

# --- ENHANCED REALISTIC ENVIRONMENT ---
# Building types for variety
building_types = [
    {'scale': (15, 25, 15), 'color': color.rgb(120, 120, 140)},  # Office building
    {'scale': (20, 35, 20), 'color': color.rgb(100, 100, 120)},  # Tall building
    {'scale': (12, 18, 12), 'color': color.rgb(140, 140, 160)},  # Medium building
    {'scale': (8, 12, 8), 'color': color.rgb(160, 160, 180)},    # Small building
    {'scale': (25, 40, 25), 'color': color.rgb(80, 80, 100)},    # Skyscraper
]

# Tree types for variety
tree_types = [
    {'trunk_scale': (0.8, 6, 0.8), 'leaves_scale': (5, 5, 5), 'leaves_color': color.green},
    {'trunk_scale': (1.0, 8, 1.0), 'leaves_scale': (6, 6, 6), 'leaves_color': color.rgb(0, 100, 0)},
    {'trunk_scale': (0.6, 4, 0.6), 'leaves_scale': (4, 4, 4), 'leaves_color': color.rgb(0, 120, 0)},
    {'trunk_scale': (1.2, 10, 1.2), 'leaves_scale': (7, 7, 7), 'leaves_color': color.rgb(0, 80, 0)},
]

# Efficient environment generation with distance-based LOD
def create_building(x, z, building_type):
    """Create a realistic building with windows and details"""
    
    # Building textures
    building_textures = ['white_cube', 'brick', 'grass']
    selected_texture = random.choice(building_textures)
    
    # Roof textures
    roof_textures = ['white_cube', 'brick', 'grass']
    roof_texture = random.choice(roof_textures)
    
    # Window textures
    window_textures = ['white_cube']
    window_texture = random.choice(window_textures)
    
    building = Entity(
        model='cube',
        scale=building_type['scale'],
        color=building_type['color'],
        position=(x, building_type['scale'][1]/2, z),
        collider='box',
        texture=selected_texture,
        texture_scale=(building_type['scale'][0]/5, building_type['scale'][1]/5)
    )
    
    # Add windows with texture
    window_rows = int(building_type['scale'][1] / 4)
    window_cols = int(building_type['scale'][0] / 3)
    for row in range(window_rows):
        for col in range(window_cols):
            if random.random() > 0.3:  # 70% chance of window
                Entity(
                    parent=building,
                    model='cube',
                    scale=(0.8, 0.8, 0.1),
                    color=color.rgb(200, 220, 255),
                    position=(
                        (col - window_cols/2) * 2.5,
                        (row - window_rows/2) * 3 + 2,
                        building_type['scale'][2]/2 + 0.1
                    ),
                    texture=window_texture,
                    texture_scale=(1, 1)
                )
    
    # Add roof details with texture
    Entity(
        parent=building,
        model='cube',
        scale=(building_type['scale'][0] + 1, 1, building_type['scale'][2] + 1),
        color=color.rgb(80, 80, 100),
        position=(0, building_type['scale'][1]/2 + 0.5, 0),
        texture=roof_texture,
        texture_scale=(2, 1)
    )
    
    # Add entrance door
    door_width = min(2.0, building_type['scale'][0] / 4)
    Entity(
        parent=building,
        model='cube',
        scale=(door_width, 3, 0.1),
        color=color.rgb(100, 60, 40),
        position=(0, 1.5, building_type['scale'][2]/2 + 0.1),
        texture='brick',
        texture_scale=(1, 1)
    )
    
    # Add some architectural details
    if building_type['scale'][1] > 20:  # Only for tall buildings
        # Add horizontal bands
        for i in range(1, int(building_type['scale'][1] / 8)):
            y_pos = (i * 8) - (building_type['scale'][1] / 2)
            Entity(
                parent=building,
                model='cube',
                scale=(building_type['scale'][0] + 0.2, 0.3, building_type['scale'][2] + 0.2),
                color=color.rgb(120, 120, 140),
                position=(0, y_pos, 0),
                texture='brick',
                texture_scale=(2, 0.5)
            )
    
    return building

def create_tree(x, z, tree_type):
    """Create a realistic tree with trunk and leaves"""
    tree = Entity(position=(x, 0, z))
    
    # Tree textures
    trunk_textures = ['white_cube', 'brick', 'grass']
    trunk_texture = random.choice(trunk_textures)
    
    leaves_textures = ['white_cube', 'grass']
    leaves_texture = random.choice(leaves_textures)
    
    # Trunk with texture
    trunk = Entity(
        parent=tree,
        model='cube',
        scale=tree_type['trunk_scale'],
        color=color.rgb(80, 50, 20),
        position=(0, tree_type['trunk_scale'][1]/2, 0),
        texture=trunk_texture,
        texture_scale=(tree_type['trunk_scale'][0]/2, tree_type['trunk_scale'][1]/2)
    )
    
    # Leaves (multiple layers for realism) with texture
    leaves_y = tree_type['trunk_scale'][1]
    for i in range(3):
        scale_factor = 1 - i * 0.2
        Entity(
            parent=tree,
            model='sphere',
            scale=(tree_type['leaves_scale'][0] * scale_factor, 
                   tree_type['leaves_scale'][1] * scale_factor, 
                   tree_type['leaves_scale'][2] * scale_factor),
            color=tree_type['leaves_color'],
            position=(0, leaves_y + i * 2, 0),
            texture=leaves_texture,
            texture_scale=(scale_factor, scale_factor)
        )
    
    # Add some branches for realism
    branch_count = random.randint(2, 4)
    for i in range(branch_count):
        branch_angle = (i / branch_count) * 360
        branch_height = random.uniform(0.3, 0.7) * tree_type['trunk_scale'][1]
        branch_length = random.uniform(0.5, 1.5)
        
        # Create branch
        branch = Entity(
            parent=tree,
            model='cube',
            scale=(branch_length, 0.2, 0.2),
            color=color.rgb(60, 40, 20),
            position=(0, branch_height, 0),
            rotation=(0, branch_angle, 0),
            texture=trunk_texture,
            texture_scale=(branch_length, 0.5)
        )
        
        # Add small leaves on branch
        for j in range(random.randint(1, 3)):
            leaf_pos = random.uniform(0.2, branch_length - 0.2)
            Entity(
                parent=branch,
                model='sphere',
                scale=(0.3, 0.3, 0.3),
                color=tree_type['leaves_color'],
                position=(leaf_pos, 0.2, 0),
                texture=leaves_texture,
                texture_scale=(0.5, 0.5)
            )
    
    return tree

# Generate environment with efficient spacing
environment_objects = []

# Define spawn area to avoid buildings near player start
spawn_area_radius = 100  # Keep area around spawn clear
spawn_x, spawn_z = 0, 0  # Player spawn position

def is_in_spawn_area(x, z):
    """Check if position is in the spawn area"""
    distance = ((x - spawn_x)**2 + (z - spawn_z)**2)**0.5
    return distance < spawn_area_radius

def is_too_close_to_roads(x, z, min_distance=25):
    """Check if position is too close to any road"""
    for road in roads:
        road_x, road_z = road.position.x, road.position.z
        distance_to_road = ((x - road_x)**2 + (z - road_z)**2)**0.5
        if distance_to_road < min_distance:
            return True
    return False

# Buildings in urban areas (avoiding roads and spawn area)
for i in range(-(grid_count//2), grid_count//2+1):
    for j in range(-(grid_count//2), grid_count//2+1):
        # Buildings near intersections but not on roads
        if (i+j) % 3 == 0:  # Reduced frequency for better performance
            building_type = random.choice(building_types)
            x = i*road_spacing + random.uniform(-40, 40)
            z = j*road_spacing + random.uniform(-40, 40)
            
            # Check if building is in spawn area or too close to roads
            if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 25):
                building = create_building(x, z, building_type)
                environment_objects.append(building)

# Add more buildings in open areas
for i in range(-(grid_count//2), grid_count//2+1):
    for j in range(-(grid_count//2), grid_count//2+1):
        # Additional buildings in open spaces
        if (i+j) % 4 == 0:  # Reduced frequency for better performance
            building_type = random.choice(building_types)
            x = i*road_spacing + random.uniform(-50, 50)
            z = j*road_spacing + random.uniform(-50, 50)
            
            # Check if building is in spawn area or too close to roads
            if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 30):
                building = create_building(x, z, building_type)
                environment_objects.append(building)

# Add even more buildings for density
for i in range(-(grid_count//2), grid_count//2+1):
    for j in range(-(grid_count//2), grid_count//2+1):
        # Dense urban areas
        if (i+j) % 5 == 0:  # Reduced frequency for better performance
            building_type = random.choice(building_types)
            x = i*road_spacing + random.uniform(-60, 60)
            z = j*road_spacing + random.uniform(-60, 60)
            
            # Check if building is in spawn area or too close to roads
            if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 35):
                building = create_building(x, z, building_type)
                environment_objects.append(building)

# Trees in natural areas (away from roads and spawn area)
for i in range(-(grid_count//2), grid_count//2+1):
    for j in range(-(grid_count//2), grid_count//2+1):
        # Trees in open areas
        if (i+j) % 2 == 0:  # Reduced frequency for better performance
            tree_type = random.choice(tree_types)
            x = i*road_spacing + random.uniform(-40, 40)
            z = j*road_spacing + random.uniform(-40, 40)
            
            # Check if tree is in spawn area or too close to roads
            if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 20):
                tree = create_tree(x, z, tree_type)
                environment_objects.append(tree)

# Add more trees in natural areas
for i in range(-(grid_count//2), grid_count//2+1):
    for j in range(-(grid_count//2), grid_count//2+1):
        # Additional trees for more density
        if (i+j) % 3 == 0:  # Reduced frequency for better performance
            tree_type = random.choice(tree_types)
            x = i*road_spacing + random.uniform(-60, 60)
            z = j*road_spacing + random.uniform(-60, 60)
            
            # Check if tree is in spawn area or too close to roads
            if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 25):
                tree = create_tree(x, z, tree_type)
                environment_objects.append(tree)

# Add even more trees for dense forests
for i in range(-(grid_count//2), grid_count//2+1):
    for j in range(-(grid_count//2), grid_count//2+1):
        # Dense forest areas
        if (i+j) % 4 == 0:  # Reduced frequency for better performance
            tree_type = random.choice(tree_types)
            x = i*road_spacing + random.uniform(-70, 70)
            z = j*road_spacing + random.uniform(-70, 70)
            
            # Check if tree is in spawn area or too close to roads
            if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 30):
                tree = create_tree(x, z, tree_type)
                environment_objects.append(tree)

# Add scattered trees and buildings for natural distribution
for _ in range(100):  # Reduced from 200 for better performance
    x = random.uniform(-4000, 4000)
    z = random.uniform(-4000, 4000)
    
    # Check if position is valid
    if not is_in_spawn_area(x, z) and not is_too_close_to_roads(x, z, 15):
        if random.random() > 0.3:  # 70% chance for trees
            tree_type = random.choice(tree_types)
            tree = create_tree(x, z, tree_type)
            environment_objects.append(tree)
        else:  # 30% chance for buildings
            building_type = random.choice(building_types)
            building = create_building(x, z, building_type)
            environment_objects.append(building)

# Add some special landmarks
landmarks = [
    # City center tower
    {'pos': (road_spacing*2, 0), 'scale': (30, 60, 30), 'color': color.rgb(60, 60, 80), 'texture': 'brick'},
    # Park area
    {'pos': (road_spacing, road_spacing), 'scale': (40, 20, 40), 'color': color.rgb(100, 140, 100), 'texture': 'grass'},
    # Industrial area
    {'pos': (-road_spacing, -road_spacing), 'scale': (35, 25, 35), 'color': color.rgb(120, 100, 80), 'texture': 'brick'},
]

for landmark in landmarks:
    x, z = landmark['pos']
    building = Entity(
        model='cube',
        scale=landmark['scale'],
        color=landmark['color'],
        position=(x, landmark['scale'][1]/2, z),
        collider='box',
        texture=landmark['texture'],
        texture_scale=(landmark['scale'][0]/5, landmark['scale'][1]/5)
    )
    environment_objects.append(building)

# Add street furniture and details
def create_bench(x, z):
    """Create a park bench"""
    bench = Entity(position=(x, 0, z))
    # Bench seat
    Entity(parent=bench, model='cube', scale=(3, 0.3, 0.8), color=color.brown, position=(0, 0.5, 0))
    # Bench back
    Entity(parent=bench, model='cube', scale=(3, 1, 0.1), color=color.brown, position=(0, 1, -0.4))
    # Bench legs
    for x_pos in [-1.2, 1.2]:
        Entity(parent=bench, model='cube', scale=(0.1, 1, 0.1), color=color.brown, position=(x_pos, 0.5, 0))
    return bench

def create_streetlight(x, z):
    """Create a detailed streetlight"""
    light = Entity(position=(x, 0, z))
    # Pole
    Entity(parent=light, model='cube', scale=(0.2, 8, 0.2), color=color.rgb(100, 100, 100), position=(0, 4, 0))
    # Light fixture
    Entity(parent=light, model='sphere', scale=(1, 0.5, 1), color=color.rgb(255, 255, 200), position=(0, 8, 0))
    return light

def create_bus_stop(x, z):
    """Create a bus stop shelter"""
    shelter = Entity(position=(x, 0, z))
    # Roof
    Entity(parent=shelter, model='cube', scale=(4, 0.2, 2), color=color.rgb(80, 80, 80), position=(0, 3, 0))
    # Back wall
    Entity(parent=shelter, model='cube', scale=(4, 3, 0.1), color=color.rgb(120, 120, 120), position=(0, 1.5, -1))
    # Side walls
    for x_pos in [-2, 2]:
        Entity(parent=shelter, model='cube', scale=(0.1, 3, 2), color=color.rgb(120, 120, 120), position=(x_pos, 1.5, 0))
    return shelter

# Add street furniture along roads
for r in roads:
    for i in range(-6, 7, 6):  # Much sparser for better performance
        x = r.position[0] + (i*150 if r.scale[2]>r.scale[0] else 0)
        z = r.position[2] + (i*150 if r.scale[0]>r.scale[2] else 0)
        
        # Add benches in park areas
        if random.random() > 0.8:  # Reduced frequency
            bench = create_bench(x + random.uniform(-20, 20), z + random.uniform(-20, 20))
            environment_objects.append(bench)
        
        # Add bus stops at intersections
        if i % 12 == 0:  # Much sparser
            bus_stop = create_bus_stop(x + 15, z + 15)
            environment_objects.append(bus_stop)

# Add some decorative elements
def create_fountain(x, z):
    """Create a decorative fountain"""
    fountain = Entity(position=(x, 0, z))
    # Base
    Entity(parent=fountain, model='cube', scale=(2, 0.5, 2), color=color.rgb(150, 150, 150), position=(0, 0.25, 0))
    # Center column
    Entity(parent=fountain, model='cube', scale=(0.5, 2, 0.5), color=color.rgb(120, 120, 120), position=(0, 1.5, 0))
    # Water effect (simplified)
    Entity(parent=fountain, model='sphere', scale=(1, 0.5, 1), color=color.rgb(100, 150, 255), position=(0, 2.5, 0))
    return fountain

# Add a fountain in the center
center_fountain = create_fountain(0, 0)
environment_objects.append(center_fountain)

# Add some billboards and signs
def create_billboard(x, z):
    """Create a billboard"""
    billboard = Entity(position=(x, 0, z))
    # Pole
    Entity(parent=billboard, model='cube', scale=(0.3, 8, 0.3), color=color.rgb(80, 80, 80), position=(0, 4, 0))
    # Billboard face
    Entity(parent=billboard, model='cube', scale=(6, 4, 0.2), color=color.rgb(200, 200, 200), position=(0, 6, 0))
    return billboard

# Add billboards at strategic locations
billboard_positions = [
    (road_spacing, road_spacing),
    (-road_spacing, -road_spacing),
    (road_spacing, -road_spacing),
    (-road_spacing, road_spacing),
]

for pos in billboard_positions:
    billboard = create_billboard(pos[0], pos[1])
    environment_objects.append(billboard)

# Add some industrial elements
def create_factory(x, z):
    """Create an industrial factory building"""
    factory = Entity(position=(x, 0, z))
    
    # Factory textures
    factory_textures = ['white_cube', 'brick', 'grass']
    factory_texture = random.choice(factory_textures)
    chimney_texture = random.choice(factory_textures)
    
    # Main building
    Entity(
        parent=factory, 
        model='cube', 
        scale=(25, 15, 20), 
        color=color.rgb(100, 100, 100), 
        position=(0, 7.5, 0),
        texture=factory_texture,
        texture_scale=(5, 3)
    )
    # Chimney
    Entity(
        parent=factory, 
        model='cube', 
        scale=(2, 20, 2), 
        color=color.rgb(80, 80, 80), 
        position=(8, 20, 0),
        texture=chimney_texture,
        texture_scale=(1, 4)
    )
    # Smoke effect (simplified)
    Entity(
        parent=factory, 
        model='sphere', 
        scale=(3, 2, 3), 
        color=color.rgb(150, 150, 150), 
        position=(8, 30, 0),
        texture='white_cube',
        texture_scale=(1, 1)
    )
    return factory

# Add a factory in the industrial area
factory = create_factory(-road_spacing * 1.5, -road_spacing * 1.5)
environment_objects.append(factory)

# Add some residential houses
def create_house(x, z):
    """Create a residential house"""
    house = Entity(position=(x, 0, z))
    
    # House textures
    house_textures = ['white_cube', 'brick', 'grass']
    house_texture = random.choice(house_textures)
    roof_texture = random.choice(house_textures)
    
    # Main house
    Entity(
        parent=house, 
        model='cube', 
        scale=(8, 6, 10), 
        color=color.rgb(180, 160, 140), 
        position=(0, 3, 0),
        texture=house_texture,
        texture_scale=(2, 2)
    )
    # Roof
    Entity(
        parent=house, 
        model='cube', 
        scale=(10, 2, 12), 
        color=color.rgb(120, 80, 60), 
        position=(0, 7, 0),
        texture=roof_texture,
        texture_scale=(3, 1)
    )
    # Door
    Entity(
        parent=house, 
        model='cube', 
        scale=(1.5, 3, 0.1), 
        color=color.rgb(100, 60, 40), 
        position=(0, 1.5, 5.1),
        texture='brick',
        texture_scale=(1, 1)
    )
    # Windows
    for x_pos in [-2, 2]:
        Entity(
            parent=house, 
            model='cube', 
            scale=(1, 1, 0.1), 
            color=color.rgb(200, 220, 255), 
            position=(x_pos, 3, 5.1),
            texture='white_cube',
            texture_scale=(1, 1)
        )
    return house

# Add houses in residential areas - reduced for performance
for i in range(-1, 2):  # Reduced range
    for j in range(-1, 2):  # Reduced range
        if (i+j) % 2 == 0 and (i != 0 or j != 0):  # Avoid center
            x = i * road_spacing * 0.8 + random.uniform(-20, 20)
            z = j * road_spacing * 0.8 + random.uniform(-20, 20)
            house = create_house(x, z)
            environment_objects.append(house)

# Simplified traffic signs
for x in range(-(grid_count//2), grid_count//2+1):
    for z in range(-(grid_count//2), grid_count//2+1):
        if x==0 and z==0:
            continue
        Entity(model='cube', scale=(0.5,2,0.5), color=color.white, position=(x*road_spacing,1.5,z*road_spacing+8), collider=None)
        Entity(model='cube', scale=(2,2,0.2), color=color.red, position=(x*road_spacing,3,z*road_spacing+8), collider=None)

# --- OPTIMIZED TRAFFIC VEHICLES ---
class TrafficVehicle(Entity):
    def __init__(self, kind='car', lane=0, direction=1, color_override=None, **kwargs):
        super().__init__()
        self.kind = kind
        
        # Enhanced color and texture system
        car_colors = [
            color.red, color.blue, color.green, color.yellow, color.orange, 
            color.rgb(128, 0, 128), color.cyan, color.pink, color.brown, color.gray,
            color.rgb(255, 100, 100), color.rgb(100, 255, 100), color.rgb(100, 100, 255),
            color.rgb(255, 255, 100), color.rgb(255, 100, 255), color.rgb(100, 255, 255),
            color.rgb(200, 150, 100), color.rgb(150, 200, 100), color.rgb(100, 150, 200),
            color.rgb(255, 200, 100), color.rgb(200, 255, 100), color.rgb(100, 200, 255)
        ]
        
        main_color = color_override or random.choice(car_colors)
        
        # Vehicle textures
        car_textures = ['white_cube', 'grass', 'brick']
        selected_texture = random.choice(car_textures)
        
        # Enhanced vehicle models with detailed components
        if kind == 'car':
            self.model = None
            self.scale = (2, 0.7, 4)
            # Enhanced body with texture
            self.body = Entity(
                parent=self, 
                model='cube', 
                color=main_color, 
                scale=(2.2, 0.5, 4.2), 
                position=(0, 0.5, 0), 
                texture=selected_texture,
                texture_scale=(2, 2)
            )
            # Enhanced roof with different texture
            roof_texture = random.choice(car_textures)
            self.roof = Entity(
                parent=self, 
                model='cube', 
                color=color.rgba(100, 200, 255, 180), 
                scale=(1.3, 0.25, 1.7), 
                position=(0, 1.0, -0.2), 
                texture=roof_texture,
                texture_scale=(1, 1)
            )
            # Enhanced wheels with texture
            wheel_texture = random.choice(car_textures)
            for x in (-0.95, 0.95):
                for z in (-1.7, 1.7):
                    Entity(
                        parent=self, 
                        model='cube', 
                        color=color.black, 
                        scale=(0.7, 0.32, 0.7), 
                        position=(x, 0.22, z), 
                        rotation=(90,0,0),
                        texture=wheel_texture,
                        texture_scale=(0.5, 0.5)
                    )
            # Add headlights
            for x in (-0.8, 0.8):
                Entity(
                    parent=self,
                    model='sphere',
                    color=color.rgb(255, 255, 200),
                    scale=(0.2, 0.2, 0.2),
                    position=(x, 0.6, 2.1),
                    texture='white_cube'
                )
            # Add taillights
            for x in (-0.8, 0.8):
                Entity(
                    parent=self,
                    model='sphere',
                    color=color.red,
                    scale=(0.15, 0.15, 0.15),
                    position=(x, 0.6, -2.1),
                    texture='white_cube'
                )
            # Add side mirrors
            for x in (-1.2, 1.2):
                Entity(
                    parent=self,
                    model='cube',
                    color=main_color,
                    scale=(0.1, 0.3, 0.1),
                    position=(x, 0.8, 1.5),
                    texture=selected_texture,
                    texture_scale=(0.5, 0.5)
                )
            # Add front grille
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(80, 80, 80),
                scale=(1.5, 0.3, 0.1),
                position=(0, 0.4, 2.1),
                texture='brick',
                texture_scale=(2, 1)
            )
            # Add rear bumper
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(80, 80, 80),
                scale=(1.8, 0.2, 0.1),
                position=(0, 0.3, -2.1),
                texture='brick',
                texture_scale=(2, 1)
            )
            # Add side skirts
            for x in (-1.1, 1.1):
                Entity(
                    parent=self,
                    model='cube',
                    color=color.rgb(60, 60, 60),
                    scale=(0.1, 0.1, 3.5),
                    position=(x, 0.1, 0),
                    texture='brick',
                    texture_scale=(1, 3)
                )
            # Add spoiler (sporty look)
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(40, 40, 40),
                scale=(1.6, 0.1, 0.3),
                position=(0, 1.2, -1.8),
                texture='brick',
                texture_scale=(2, 1)
            )
            # Add exhaust pipes
            for x in (-0.3, 0.3):
                Entity(
                    parent=self,
                    model='cube',
                    color=color.rgb(120, 120, 120),
                    scale=(0.1, 0.1, 0.5),
                    position=(x, 0.1, -2.3),
                    texture='brick',
                    texture_scale=(0.5, 1)
                )
            # Add windshield
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(200, 220, 255),
                scale=(1.8, 0.8, 0.1),
                position=(0, 1.1, 0.8),
                texture='white_cube',
                texture_scale=(2, 1)
            )
            # Add rear window
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(200, 220, 255),
                scale=(1.8, 0.8, 0.1),
                position=(0, 1.1, -0.8),
                texture='white_cube',
                texture_scale=(2, 1)
            )
                
        elif kind == 'truck':
            self.model = None
            self.scale = (2.5, 1.1, 8)
            # Enhanced truck body
            self.body = Entity(
                parent=self, 
                model='cube', 
                color=main_color, 
                scale=(2.7, 0.7, 8.2), 
                position=(0, 0.55, 0), 
                texture=selected_texture,
                texture_scale=(4, 2)
            )
            # Enhanced truck cabin
            cabin_texture = random.choice(car_textures)
            self.cabin = Entity(
                parent=self, 
                model='cube', 
                color=color.rgb(180,180,180), 
                scale=(2.7, 1.1, 2.2), 
                position=(0, 1.0, 2.7), 
                texture=cabin_texture,
                texture_scale=(2, 1)
            )
            # Add truck windows
            for x in (-0.8, 0.8):
                Entity(
                    parent=self,
                    model='cube',
                    color=color.rgb(200, 220, 255),
                    scale=(0.8, 0.6, 0.1),
                    position=(x, 1.2, 3.2),
                    texture='white_cube',
                    texture_scale=(1, 1)
                )
            # Enhanced wheels
            wheel_texture = random.choice(car_textures)
            for x in (-1.1, 1.1):
                for z in (-3.2, 0, 3.2):
                    Entity(
                        parent=self, 
                        model='cube', 
                        color=color.black, 
                        scale=(0.8, 0.35, 0.8), 
                        position=(x, 0.25, z), 
                        rotation=(90,0,0),
                        texture=wheel_texture,
                        texture_scale=(0.6, 0.6)
                    )
            # Add truck headlights
            for x in (-1.0, 1.0):
                Entity(
                    parent=self,
                    model='sphere',
                    color=color.rgb(255, 255, 200),
                    scale=(0.3, 0.3, 0.3),
                    position=(x, 1.2, 3.8),
                    texture='white_cube'
                )
            # Add truck taillights
            for x in (-1.0, 1.0):
                Entity(
                    parent=self,
                    model='sphere',
                    color=color.red,
                    scale=(0.25, 0.25, 0.25),
                    position=(x, 0.8, -4.1),
                    texture='white_cube'
                )
            # Add truck grille
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(80, 80, 80),
                scale=(2.0, 0.4, 0.1),
                position=(0, 0.6, 3.8),
                texture='brick',
                texture_scale=(3, 1)
            )
            # Add truck bumper
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(80, 80, 80),
                scale=(2.2, 0.3, 0.1),
                position=(0, 0.4, -4.1),
                texture='brick',
                texture_scale=(3, 1)
            )
                
        elif kind == 'bus':
            self.model = None
            self.scale = (2.2, 1.2, 7)
            # Enhanced bus body
            self.body = Entity(
                parent=self, 
                model='cube', 
                color=main_color, 
                scale=(2.4, 1.0, 7.2), 
                position=(0, 0.7, 0), 
                texture=selected_texture,
                texture_scale=(3, 2)
            )
            # Add bus windows
            window_texture = random.choice(car_textures)
            for row in range(3):
                for col in range(2):
                    x_pos = (col - 0.5) * 1.5
                    z_pos = (row - 1) * 2.0
                    Entity(
                        parent=self,
                        model='cube',
                        color=color.rgb(200, 220, 255),
                        scale=(1.0, 0.6, 0.1),
                        position=(x_pos, 1.2, z_pos),
                        texture=window_texture,
                        texture_scale=(1, 1)
                    )
            # Add bus door
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(100, 100, 100),
                scale=(1.2, 1.5, 0.1),
                position=(0, 0.75, 2.6),
                texture='brick',
                texture_scale=(1, 1)
            )
            # Enhanced wheels
            wheel_texture = random.choice(car_textures)
            for x in (-0.95, 0.95):
                for z in (-2.7, 2.7):
                    Entity(
                        parent=self, 
                        model='cube', 
                        color=color.black, 
                        scale=(0.7, 0.32, 0.7), 
                        position=(x, 0.22, z), 
                        rotation=(90,0,0),
                        texture=wheel_texture,
                        texture_scale=(0.5, 0.5)
                    )
            # Add bus headlights
            for x in (-0.8, 0.8):
                Entity(
                    parent=self,
                    model='sphere',
                    color=color.rgb(255, 255, 200),
                    scale=(0.25, 0.25, 0.25),
                    position=(x, 1.0, 3.6),
                    texture='white_cube'
                )
            # Add bus taillights
            for x in (-0.8, 0.8):
                Entity(
                    parent=self,
                    model='sphere',
                    color=color.red,
                    scale=(0.2, 0.2, 0.2),
                    position=(x, 1.0, -3.6),
                    texture='white_cube'
                )
            # Add bus grille
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(80, 80, 80),
                scale=(1.8, 0.3, 0.1),
                position=(0, 0.5, 3.6),
                texture='brick',
                texture_scale=(2, 1)
            )
            # Add bus bumper
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(80, 80, 80),
                scale=(2.0, 0.2, 0.1),
                position=(0, 0.3, -3.6),
                texture='brick',
                texture_scale=(2, 1)
            )
        
        self.position = Vec3(lane*road_spacing, 1, -900*direction)
        self.direction = direction
        self.speed = random.uniform(14, 26) if kind=='car' else random.uniform(10, 18)
        if kind == 'bus':
            self.speed = random.uniform(10, 16)
        self.lane = lane
        self.collider = 'box'
        self.last_update = 0
        for k,v in kwargs.items():
            setattr(self, k, v)
    
    def update(self):
        # Optimized update with distance-based culling
        if hasattr(self, 'position') and hasattr(car, 'position') and self.position and car.position:
            try:
                distance = (self.position - car.position).length()
                if distance > CULL_DISTANCE:
                    return  # Skip update if too far
            except:
                pass  # Skip culling if there's an error
        
        # Determine if this is a horizontal or vertical road based on position
        if hasattr(self, 'position') and self.position:
            is_horizontal_road = abs(self.position.x) % road_spacing < 20  # Check if on horizontal road
            is_vertical_road = abs(self.position.z) % road_spacing < 20    # Check if on vertical road
            
            # Simplified movement calculation
            move_distance = self.speed * self.direction * time.dt
            
            if is_horizontal_road:
                # Move along X-axis for horizontal roads
                self.position += Vec3(move_distance, 0, 0)
                
                # Loop traffic for horizontal roads
                if self.direction > 0 and hasattr(self.position, 'x') and self.position.x > 5000:
                    self.position.x = -5000
                elif self.direction < 0 and hasattr(self.position, 'x') and self.position.x < -5000:
                    self.position.x = 5000
            else:
                # Move along Z-axis for vertical roads
                self.position += Vec3(0, 0, move_distance)
                
                # Loop traffic for vertical roads
                if self.direction > 0 and hasattr(self.position, 'z') and self.position.z > 5000:
                    self.position.z = -5000
                elif self.direction < 0 and hasattr(self.position, 'z') and self.position.z < -5000:
                    self.position.z = 5000

# Improved AI traffic that follows roads
traffic_vehicles = []

# Create traffic for each road - optimized for performance
for road in roads:
    # Determine road direction and position
    is_horizontal = road.scale[0] > road.scale[2]  # East-West road
    road_length = road.scale[0] if is_horizontal else road.scale[2]
    road_pos = road.position
    
    # Spawn vehicles along this road - reduced density
    for offset in range(-int(road_length//2), int(road_length//2), 2000):  # Increased spacing
        # Determine vehicle position based on road orientation
        if is_horizontal:
            # East-West road
            x = road_pos.x + offset
            z = road_pos.z
            # Add vehicles in both directions on the same road
            # Right lane (eastbound)
            traffic_vehicles.append(TrafficVehicle('car', lane=0, direction=1, position=Vec3(x, 1, z + 15)))
            # Left lane (westbound)
            traffic_vehicles.append(TrafficVehicle('car', lane=0, direction=-1, position=Vec3(x + 400, 1, z - 15)))
            
            # Trucks (much less frequent)
            if random.random() > 0.7:  # Reduced frequency
                traffic_vehicles.append(TrafficVehicle('truck', lane=0, direction=1, position=Vec3(x + 200, 1, z + 15)))
                traffic_vehicles.append(TrafficVehicle('truck', lane=0, direction=-1, position=Vec3(x + 600, 1, z - 15)))
            
            # Buses (much less frequent)
            if random.random() > 0.9:  # Much reduced frequency
                traffic_vehicles.append(TrafficVehicle('bus', lane=0, direction=1, position=Vec3(x + 100, 1, z + 15)))
                traffic_vehicles.append(TrafficVehicle('bus', lane=0, direction=-1, position=Vec3(x + 500, 1, z - 15)))
        else:
            # North-South road
            x = road_pos.x
            z = road_pos.z + offset
            # Add vehicles in both directions on the same road
            # Right lane (northbound)
            traffic_vehicles.append(TrafficVehicle('car', lane=0, direction=1, position=Vec3(x + 15, 1, z)))
            # Left lane (southbound)
            traffic_vehicles.append(TrafficVehicle('car', lane=0, direction=-1, position=Vec3(x - 15, 1, z + 400)))
            
            # Trucks (much less frequent)
            if random.random() > 0.7:  # Reduced frequency
                traffic_vehicles.append(TrafficVehicle('truck', lane=0, direction=1, position=Vec3(x + 15, 1, z + 200)))
                traffic_vehicles.append(TrafficVehicle('truck', lane=0, direction=-1, position=Vec3(x - 15, 1, z + 600)))
            
            # Buses (much less frequent)
            if random.random() > 0.9:  # Much reduced frequency
                traffic_vehicles.append(TrafficVehicle('bus', lane=0, direction=1, position=Vec3(x + 15, 1, z + 100)))
                traffic_vehicles.append(TrafficVehicle('bus', lane=0, direction=-1, position=Vec3(x - 15, 1, z + 500)))

for v in traffic_vehicles:
    v.parent = scene

# --- OPTIMIZED MINIMAP ---
minimap_bg = Entity(model='quad', scale=(0.18,0.18), color=color.rgba(0,0,0,120), position=(-0.7,0.38,0), z=100)
minimap_dot = Entity(model='sphere', scale=0.012, color=color.red, position=(-0.7,0.38,0.01), z=101)

def update_minimap():
    minimap_dot.x = -0.7 + (car.position.x/2000)*0.16
    minimap_dot.y = 0.38 + (car.position.z/2000)*0.16

# --- OPTIMIZED CAMERA SHAKE ---
def camera_shake(intensity=0.1):
    camera.x += random.uniform(-intensity, intensity)
    camera.y += random.uniform(-intensity, intensity)

# --- OPTIMIZED TIRE SKID MARKS ---
skid_marks = []
def add_skid_mark(pos):
    e = Entity(model='cube', scale=(0.2,0.01,1.2), color=color.rgb(30,30,30), position=pos+Vec3(0,0.01,0), collider=None)
    skid_marks.append(e)
    if len(skid_marks) > SKID_MARK_LIMIT:
        skid_marks[0].enabled=False
        skid_marks.pop(0)

# --- OPTIMIZED DAY/NIGHT CYCLE ---
day_time = 0.0
def update_day_night():
    global day_time
    day_time += time.dt*0.03
    sun = 0.5+0.5*sin(day_time)
    scene.ambient_color = color.rgb(int(80+120*sun),int(80+120*sun),int(120+100*sun))
    window.color = color.rgb(int(60+100*sun),int(80+120*sun),int(120+100*sun))

# --- OPTIMIZED WEATHER SYSTEM ---
weather = random.choice(['clear','rain','fog'])
weather_entities = []
if weather=='rain':
    for _ in range(WEATHER_ENTITY_COUNT):  # Reduced count
        weather_entities.append(Entity(model='cube', scale=(0.05,0.7,0.05), color=color.rgb(120,120,255), position=(random.uniform(-100,100),random.uniform(8,20),random.uniform(-100,100)), collider=None))
if weather=='fog':
    window.color = color.rgb(180,180,200)
    scene.fog_density = 0.03
else:
    scene.fog_density = 0.0

# --- OPTIMIZED CAR MODEL ---
class Car(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        
        # Car color and texture system
        car_colors = [
            color.rgb(255, 100, 100),  # Red
            color.rgb(100, 100, 255),  # Blue
            color.rgb(100, 255, 100),  # Green
            color.rgb(255, 255, 100),  # Yellow
            color.rgb(255, 100, 255),  # Pink
            color.rgb(100, 255, 255),  # Cyan
            color.rgb(255, 200, 100),  # Orange
            color.rgb(200, 100, 255),  # Purple
            color.rgb(255, 255, 255),  # White
            color.rgb(50, 50, 50),     # Black
        ]
        
        main_color = random.choice(car_colors)
        car_textures = ['white_cube', 'brick', 'grass']
        selected_texture = random.choice(car_textures)
        
        # Enhanced car body with texture
        self.body = Entity(
            parent=self,
            model='cube',
            color=main_color,
            scale=(2.2, 0.5, 4.2),
            position=(0, 0.5, 0),
            texture=selected_texture,
            texture_scale=(2, 2)
        )
        
        # Enhanced roof with different texture
        roof_texture = random.choice(car_textures)
        self.roof = Entity(
            parent=self,
            model='cube',
            color=color.rgba(100, 200, 255, 180),
            scale=(1.3, 0.25, 1.7),
            position=(0, 1.0, -0.2),
            texture=roof_texture,
            texture_scale=(1, 1)
        )
        
        # Enhanced wheels with texture
        wheel_texture = random.choice(car_textures)
        self.wheels = []
        for x in (-0.95, 0.95):
            for z in (-1.7, 1.7):
                wheel = Entity(
                    parent=self,
                    model='cube',
                    color=color.black,
                    scale=(0.7, 0.32, 0.7),
                    position=(x, 0.22, z),
                    rotation=(90,0,0),
                    texture=wheel_texture,
                    texture_scale=(0.5, 0.5)
                )
                self.wheels.append(wheel)
        
        # Add headlights
        for x in (-0.8, 0.8):
            Entity(
                parent=self,
                model='sphere',
                color=color.rgb(255, 255, 200),
                scale=(0.2, 0.2, 0.2),
                position=(x, 0.6, 2.1),
                texture='white_cube'
            )
        
        # Add taillights
        for x in (-0.8, 0.8):
            Entity(
                parent=self,
                model='sphere',
                color=color.red,
                scale=(0.15, 0.15, 0.15),
                position=(x, 0.6, -2.1),
                texture='white_cube'
            )
        
        # Add side mirrors
        for x in (-1.2, 1.2):
            Entity(
                parent=self,
                model='cube',
                color=main_color,
                scale=(0.1, 0.3, 0.1),
                position=(x, 0.8, 1.5),
                texture=selected_texture,
                texture_scale=(0.5, 0.5)
            )
        
        # Add front grille
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(80, 80, 80),
            scale=(1.5, 0.3, 0.1),
            position=(0, 0.4, 2.1),
            texture='brick',
            texture_scale=(2, 1)
        )
        
        # Add rear bumper
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(80, 80, 80),
            scale=(1.8, 0.2, 0.1),
            position=(0, 0.3, -2.1),
            texture='brick',
            texture_scale=(2, 1)
        )
        
        # Add side skirts
        for x in (-1.1, 1.1):
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(60, 60, 60),
                scale=(0.1, 0.1, 3.5),
                position=(x, 0.1, 0),
                texture='brick',
                texture_scale=(1, 3)
            )
        
        # Add spoiler (sporty look)
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(40, 40, 40),
            scale=(1.6, 0.1, 0.3),
            position=(0, 1.2, -1.8),
            texture='brick',
            texture_scale=(2, 1)
        )
        
        # Add exhaust pipes
        for x in (-0.3, 0.3):
            Entity(
                parent=self,
                model='cube',
                color=color.rgb(120, 120, 120),
                scale=(0.1, 0.1, 0.5),
                position=(x, 0.1, -2.3),
                texture='brick',
                texture_scale=(0.5, 1)
            )
        
        # Add windshield
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(200, 220, 255),
            scale=(1.8, 0.8, 0.1),
            position=(0, 1.1, 0.8),
            texture='white_cube',
            texture_scale=(2, 1)
        )
        
        # Add rear window
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(200, 220, 255),
            scale=(1.8, 0.8, 0.1),
            position=(0, 1.1, -0.8),
            texture='white_cube',
            texture_scale=(2, 1)
        )
        
        self.position = Vec3(0, 1, 0)
        self.rotation = Vec3(0, 0, 0)
        self.collider = 'box'
        self.speed = 0
        self.max_speed = 1000
        self.max_reverse_speed = 40
        self.acceleration = 0.4  # Reduced from 0.7 for more gradual acceleration
        self.turn_speed = 45
        self.friction = 0.99
        self.drifting = False
        self.suspension_pitch = 0
        self.suspension_roll = 0
        self.suspension_smooth = 8
        self.tire_grip = 1.0
        self.slip = 0.0
        self.traction_control = True
        self.abs_enabled = True
        self.downforce_coeff = 0.0008
        for key, value in kwargs.items():
            setattr(self, key, value)

    def update(self):
        if is_paused:
            return
        else:
            pass
        
        try:
            self.speed = float(self.speed)
        except Exception:
            self.speed = 0.0
        
        friction = 1
        self.drifting = False
        
        # Simplified input handling
        throttle = held_keys.get('w', False)
        brake = held_keys.get('space', False)
        reverse = held_keys.get('s', False)
        steer_left = held_keys.get('a', False)
        steer_right = held_keys.get('d', False)
        
        # Enhanced physics with proper drifting
        if self.traction_control and throttle and abs(self.speed) < 10:
            effective_accel = self.acceleration * 0.7
        else:
            effective_accel = self.acceleration
        
        if throttle:
            self.speed += effective_accel
        elif reverse:
            self.speed -= effective_accel
        
        # Simple braking - works in all gears
        if brake:
            if self.speed > 0:
                self.speed = max(self.speed - 0.4, 0)
            elif self.speed < 0:
                self.speed = min(self.speed + 0.4, 0)
            self.drifting = True
            friction = 0.95
        else:
            if abs(self.speed) < 5:
                friction = 0.995
            else:
                friction = 0.997
        
        if not brake:
            self.speed *= friction
        
        self.speed = clamp(self.speed, -self.max_reverse_speed, self.max_speed)
        
        # Gradual steering with smooth interpolation
        steering_factor = max(abs(self.speed) / self.max_speed, 0.15)
        steer_dir = 0
        if steer_left:
            steer_dir -= 1
        if steer_right:
            steer_dir += 1
        
        # Target steering angle with speed-dependent turning radius
        base_max_steer_angle = 6  # Base steering angle
        
        # Reduce turning radius at low speeds (more responsive steering)
        if abs(self.speed) < 20:  # Very low speed
            max_steer_angle = base_max_steer_angle * 4.5  # Much smaller turning radius
        elif abs(self.speed) < 50:  # Low speed
            max_steer_angle = base_max_steer_angle * 3.0  # Smaller turning radius
        else:  # High speed
            max_steer_angle = base_max_steer_angle  # Normal turning radius
        
        target_steer_angle = steer_dir * max_steer_angle * steering_factor
        
        # Smooth steering interpolation
        if not hasattr(self, 'current_steer_angle'):
            self.current_steer_angle = 0.0
        
        # Gradual steering speed based on vehicle speed and gear
        base_steering_speed = 1.5  # Reduced base speed for less sensitivity
        
        # Reduce steering sensitivity at higher speeds
        speed_factor = max(0.3, 1.0 - (abs(self.speed) / 100.0))  # Less sensitive at high speeds
        
        # Reduce steering sensitivity in higher gears
        gear_factor = 1.0
        if hasattr(self, 'current_gear'):
            if self.current_gear >= 4:  # High gears
                gear_factor = 0.4
            elif self.current_gear >= 2:  # Medium gears
                gear_factor = 0.7
            else:  # Low gears
                gear_factor = 1.0
        
        steering_speed = base_steering_speed * speed_factor * gear_factor
        
        # Add steering wheel centering when no input
        if steer_dir == 0:
            # Gradually return to center
            self.current_steer_angle = lerp(self.current_steer_angle, 0.0, time.dt * 2.0)
        else:
            # Apply steering input
            self.current_steer_angle = lerp(self.current_steer_angle, target_steer_angle, time.dt * steering_speed)
        
        # Apply current steering angle to wheels
        if hasattr(self, 'wheels') and len(self.wheels) >= 4:
            for i in [0, 1]:
                self.wheels[i].rotation_y = self.current_steer_angle
        
        # Simplified movement
        heading = radians(self.rotation_y)
        move_vec = Vec3(sin(heading), 0, cos(heading)) * float(self.speed) * time.dt
        if not isinstance(self.position, Vec3):
            self.position = Vec3(*self.position) if self.position is not None else Vec3(0,1,0)
        self.position += move_vec
        
        # Gradual turning based on current steering angle
        if abs(self.current_steer_angle) > 0.01:
            wheelbase = 2.5
            beta = radians(self.current_steer_angle)
            turning_radius = wheelbase / sin(beta) if abs(sin(beta)) > 0.001 else 9999
            angular_velocity = float(self.speed) / turning_radius
            self.rotation_y += degrees(angular_velocity) * time.dt
        
        # Boundary checks
        if self.position.y < 1:
            self.position = Vec3(self.position.x, 1.0, self.position.z)
        
        map_size = 10000 / 2
        min_x = -map_size + 2
        max_x = map_size - 2
        min_z = -map_size + 2
        max_z = map_size - 2
        clamped_x = clamp(self.position.x, min_x, max_x)
        clamped_z = clamp(self.position.z, min_z, max_z)
        self.position = Vec3(clamped_x, self.position.y, clamped_z)
        
        # Simplified sound
        play_engine_sound(self.speed)

# Instantiate the car
car = Car()

# --- OPTIMIZED GEAR SYSTEM ---
GEAR_RATIOS = [ -2.0, 0, 0.3, 0.6, 0.8, 1.0, 1.2 ]  # Fixed: Proper gear progression for realistic speeds
GEAR_LABELS = [ 'R', 'N', '1', '2', '3', '4', '5' ]
MAX_GEAR = 6
MIN_GEAR = 0
car.current_gear = 2
car.gear_shift_cooldown = 0.0
car.gear_display = Text(
    text=f'Gear: {GEAR_LABELS[car.current_gear]}',
    position=(-0.78, -0.38),
    origin=(0,0),
    scale=2,
    color=color.yellow,
    background=False
)

old_update_logic = car.update

def car_update_with_gears(self):
    if self.gear_shift_cooldown > 0:
        self.gear_shift_cooldown -= time.dt
    
    # Store previous gear for downshift detection
    previous_gear = getattr(self, 'current_gear', 2)
    
    if held_keys.get('e', False) and self.gear_shift_cooldown <= 0:
        if self.current_gear < MAX_GEAR:
            self.current_gear += 1
            self.gear_shift_cooldown = 0.25
            play_gear_shift_sound()
    if held_keys.get('q', False) and self.gear_shift_cooldown <= 0:
        if self.current_gear > MIN_GEAR:
            self.current_gear -= 1
            self.gear_shift_cooldown = 0.25
            play_gear_shift_sound()
    
    # Detect downshift for engine braking
    downshifted = (previous_gear > self.current_gear and self.current_gear > 1)
    
    gear_ratio = GEAR_RATIOS[self.current_gear]
    if self.current_gear == 1:  # Neutral
        self.speed = lerp(self.speed, 0, time.dt * 2)
        self.gear_display.text = f'Gear: {GEAR_LABELS[self.current_gear]}'
        return
    else:
        # Enhanced acceleration system - proper progression through gears
        if self.current_gear == 2:  # 1st gear
            effective_accel = self.acceleration * abs(gear_ratio) * 2.0  # High acceleration
            max_speed = self.max_speed * abs(gear_ratio) * 0.3  # Low max speed
        elif self.current_gear == 3:  # 2nd gear
            effective_accel = self.acceleration * abs(gear_ratio) * 1.6  # Good acceleration
            max_speed = self.max_speed * abs(gear_ratio) * 0.5  # Medium-low max speed
        elif self.current_gear == 4:  # 3rd gear
            effective_accel = self.acceleration * abs(gear_ratio) * 1.2  # Moderate acceleration
            max_speed = self.max_speed * abs(gear_ratio) * 0.7  # Medium max speed
        elif self.current_gear == 5:  # 4th gear
            effective_accel = self.acceleration * abs(gear_ratio)  # Normal acceleration
            max_speed = self.max_speed * abs(gear_ratio) * 0.85  # High max speed
        else:  # 5th gear
            effective_accel = self.acceleration * abs(gear_ratio) * 0.8  # Lower acceleration
            max_speed = self.max_speed * abs(gear_ratio)  # Highest max speed
    
    if self.current_gear == 0:
        max_speed = self.max_reverse_speed
        effective_accel = self.acceleration * abs(gear_ratio) * 1.5  # Good reverse acceleration
    
    throttle = held_keys['w']
    brake = held_keys['space']
    reverse = held_keys['s']
    
    # Engine braking when downshifting
    if downshifted and not throttle and not brake:
        # Calculate max speed for the new gear
        if self.current_gear == 2:  # 1st gear
            max_speed_new_gear = self.max_speed * abs(GEAR_RATIOS[self.current_gear]) * 0.3
        elif self.current_gear == 1:  # Neutral
            max_speed_new_gear = 0
        else:
            max_speed_new_gear = self.max_speed * abs(GEAR_RATIOS[self.current_gear])
        # If speed is above new gear's max, prevent further acceleration, let friction slow down
        if self.speed > max_speed_new_gear:
            # No throttle effect, just friction
            pass  # Do not apply artificial braking
        # Clamp only if speed is way above max (physics bug safety net)
        if self.speed > max_speed_new_gear * 1.1:
            self.speed = max_speed_new_gear * 1.1

    # Always enforce gear speed limits, regardless of braking state
    if self.current_gear == 0:
        self.speed = clamp(self.speed, -max_speed, 0)
    else:
        self.speed = clamp(self.speed, 0, max_speed)
    
    self.gear_display.text = f'Gear: {GEAR_LABELS[self.current_gear]}'
    old_update_logic()

car.update = car_update_with_gears.__get__(car, type(car))
speedometer = Text(
    text='Speed: 0',
    position=(-0.78, -0.32),
    origin=(0,0),
    scale=2,
    color=color.azure,
    background=False
)
camera.parent = car
camera.position = (0, 7, -18)
camera.rotation = (20, 0, 0)
camera.fov = 90
camera_control_enabled = False
default_camera_position = (0, 7, -18)
default_camera_rotation = (20, 0, 0)
camera_sensitivity = 0.5
reverse_camera_transition_speed = 2.0
reverse_camera_position = (0, 7, 18)
reverse_camera_rotation = (20, 180, 0)

def toggle_camera_control():
    global camera_control_enabled, mouse
    camera_control_enabled = not camera_control_enabled
    if camera_control_enabled:
        mouse.locked = True
        print("Camera control enabled - Move mouse to look around")
    else:
        mouse.locked = False
        # Reset camera to default position
        camera.position = default_camera_position
        camera.rotation = default_camera_rotation
        print("Camera control disabled - Mouse unlocked")

def update_camera():
    global camera_control_enabled
    
    # Handle reverse gear camera transition
    if hasattr(car, 'current_gear') and car.current_gear == 0:
        target_position = reverse_camera_position
        target_rotation = reverse_camera_rotation
        
        # Smooth transition to reverse view
        camera.position = lerp(camera.position, target_position, time.dt * reverse_camera_transition_speed)
        camera.rotation = lerp(camera.rotation, target_rotation, time.dt * reverse_camera_transition_speed)
    else:
        # Normal forward gear camera
        if not camera_control_enabled:
            # Reset to default position when not in camera control mode
            camera.position = lerp(camera.position, default_camera_position, time.dt * 3.0)
            camera.rotation = lerp(camera.rotation, default_camera_rotation, time.dt * 3.0)
        else:
            # Mouse-controlled camera movement
            if mouse.locked:
                # Get mouse movement
                mouse_x = mouse.velocity[0] * camera_sensitivity
                mouse_y = mouse.velocity[1] * camera_sensitivity
                
                # Apply mouse movement to camera rotation
                current_rotation = list(camera.rotation)
                current_rotation[1] += mouse_x  # Yaw (left/right)
                current_rotation[0] -= mouse_y  # Pitch (up/down)
                
                # Clamp pitch to prevent over-rotation
                current_rotation[0] = clamp(current_rotation[0], -60, 60)
                
                # Apply new rotation
                camera.rotation = tuple(current_rotation)

# Instructions
instructions = Text(
    text='W/S: Accelerate/Brake | A/D: Steer | C: Camera Control | H: Horn | ESC: Pause',
    origin=(0, 18),
    background=True,
    position=(0, -0.45)
)

# Pause menu
pause_menu = WindowPanel(
    title='Paused',
    content=(
        Button('Resume', on_click=hide_pause_menu),
        Button('Quit', on_click=Func(quit)),
    ),
    position=window.center,
    enabled=False,
    popup=True,
    color=color.rgba(40,40,50,180),
    scale=(0.25,0.18),
    panel_color=color.rgba(0,0,0,120),
    padding=(0.03,0.03),
    rounded=True,
    z=10,
    shadow=True,
    border=True,
    border_color=color.rgba(255,255,255,60)
)

def input(key):
    if key == 'escape':
        if not pause_menu.enabled:
            show_pause_menu()
        else:
            hide_pause_menu()
    elif key == 'c':  # Toggle camera control with 'C' key
        toggle_camera_control()
    elif key == 'h':  # Horn sound
        play_horn_sound()

def update_speedometer():
    speedometer.text = f'Speed: {int(abs(car.speed))}'

# Add collision detection and sound effects
def check_collision(car, other_entity):
    """Check if car collides with another entity"""
    if hasattr(car, 'position') and hasattr(other_entity, 'position'):
        distance = (car.position - other_entity.position).length()
        if distance < 3:  # Collision threshold
            play_collision_sound()
            return True
    return False

# Add sound effects for different actions
def play_horn_sound():
    """Play horn sound"""
    horn_sound = Audio('horn', loop=False, autoplay=False)
    horn_sound.play()

def play_tire_squeal():
    """Play tire squeal sound when drifting"""
    squeal_sound = Audio('squeal', loop=False, autoplay=False)
    squeal_sound.play()

# --- OPTIMIZED UPDATE FUNCTION ---
old_update = update_speedometer
traffic_update_timer = 0

# Object management system for performance
def update_environment_objects():
    """Update environment objects based on distance from player - optimized"""
    if not hasattr(car, 'position') or not car.position:
        return
    
    # Only update every few frames for better performance
    if not hasattr(update_environment_objects, 'frame_count'):
        update_environment_objects.frame_count = 0
    
    update_environment_objects.frame_count += 1
    if update_environment_objects.frame_count % 10 != 0:  # Update every 10 frames
        return
    
    car_pos = car.position
    for obj in environment_objects:
        if hasattr(obj, 'position') and obj.position:
            try:
                distance = (obj.position - car_pos).length()
                
                # Optimized distance-based culling
                if distance > CULL_DISTANCE:
                    if obj.enabled:  # Only disable if currently enabled
                        obj.enabled = False
                elif distance < CULL_DISTANCE * 0.8:  # Add some hysteresis
                    if not obj.enabled:  # Only enable if currently disabled
                        obj.enabled = True
            except:
                # Skip problematic objects
                pass

def update():
    global traffic_update_timer, frame_times, last_fps_update
    old_update()
    update_minimap()
    update_day_night()
    update_camera()
    if hasattr(car, 'position') and car.position:
        car_pos = car.position
        for tcar in traffic_vehicles:
            if hasattr(tcar, 'position') and tcar.position:
                try:
                    distance = (car_pos - tcar.position).length()
                    if distance < 50:
                        if check_collision(car, tcar):
                            camera_shake(0.3)
                except:
                    pass
        for obj in environment_objects:
            if hasattr(obj, 'collider') and obj.collider and hasattr(obj, 'position') and obj.position:
                try:
                    distance = (car_pos - obj.position).length()
                    if distance < 30:
                        if check_collision(car, obj):
                            camera_shake(0.2)
                except:
                    pass
    if car.drifting and random.random() < 0.02:
        play_tire_squeal()
    traffic_update_timer += time.dt
    if traffic_update_timer >= TRAFFIC_UPDATE_RATE:
        for tcar in traffic_vehicles:
            tcar.update()
        traffic_update_timer = 0
    update_environment_objects()
    if car.drifting or (hasattr(car, 'slip') and car.slip and car.slip > 0.2):
        camera_shake(0.12)
        add_skid_mark(car.position)
    
    frame_times.append(time.dt)
    
    if len(frame_times) > 120:
        frame_times.pop(0)
    
    current_time = time.time()
    if current_time - last_fps_update >= fps_update_interval:
        if len(frame_times) > 0:
            recent_frame_times = frame_times[-30:]
            avg_frame_time = sum(recent_frame_times) / len(recent_frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
            fps_counter.text = f'FPS: {int(fps)}'
        last_fps_update = current_time

app.run()