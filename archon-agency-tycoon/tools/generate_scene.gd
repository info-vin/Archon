@tool
extends SceneTree

func _init():
    print("Generating fully populated World2D.tscn...")
    
    # 1. Create Isometric TileSet
    var tileset = TileSet.new()
    tileset.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
    tileset.tile_size = Vector2i(128, 64)
    var floors = [
        {"id": 0, "file": "floor_tile.png"},
        {"id": 1, "file": "floor_tile_red.png"},
        {"id": 2, "file": "floor_tile_blue.png"},
        {"id": 3, "file": "floor_tile_orange.png"},
        {"id": 4, "file": "floor_tile_carpet.png"}
    ]
    for f in floors:
        var tex = load("res://Assets/Rooms/isometric/" + f["file"])
        var source = TileSetAtlasSource.new()
        source.texture = tex
        source.texture_region_size = Vector2i(128, 64)
        source.create_tile(Vector2i(0, 0))
        tileset.add_source(source, f["id"])
        
    ResourceSaver.save(tileset, "res://Assets/Rooms/isometric/Isometric_TileSet.tres")
    
    # 2. Load World2D script
    var world_script = load("res://Scripts/World2D.gd")
    var world = Node2D.new()
    world.name = "World2D"
    world.y_sort_enabled = true 
    world.set_script(world_script)
    
    var camera = Camera2D.new()
    camera.name = "Camera2D"
    world.add_child(camera)
    camera.owner = world
    
    var floor_layer = TileMapLayer.new()
    floor_layer.name = "FloorLayer"
    floor_layer.tile_set = tileset
    floor_layer.z_index = -1 
    world.add_child(floor_layer)
    floor_layer.owner = world
    
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    world.add_child(objects)
    objects.owner = world
    
    # 3. RUN build_room() logic to populate floor and objects
    # We must explicitly pass the nodes since _ready won't fire in SceneTree script cleanly
    world.floor_layer = floor_layer
    world.objects_node = objects
    world.astar = AStarGrid2D.new()
    world.astar.region = Rect2i(0, 0, world.grid_size, world.grid_size)
    world.astar.cell_size = Vector2(1, 1)
    world.astar.default_compute_heuristic = AStarGrid2D.HEURISTIC_MANHATTAN
    world.astar.default_estimate_heuristic = AStarGrid2D.HEURISTIC_MANHATTAN
    world.astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    world.astar.update()
    
    world.setup_floor()
    world.build_office_layout()
    
    # 4. VERY IMPORTANT: set owner for all spawned children so they save in the TSCN
    for cell in floor_layer.get_used_cells():
        pass # TileMapLayer saves automatically
        
    for child in objects.get_children():
        child.owner = world

    # 5. Save the Scene
    var packed = PackedScene.new()
    packed.pack(world)
    var err = ResourceSaver.save(packed, "res://Scenes/Main/World2D.tscn")
    if err == OK:
        print("Successfully saved fully populated World2D.tscn!")
    else:
        print("Error saving: ", err)
    quit()
