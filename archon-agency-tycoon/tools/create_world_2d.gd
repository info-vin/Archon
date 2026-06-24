@tool
extends SceneTree

func _init():
    print("Building Node2D Isometric World with new assets...")
    
    # 1. Create Isometric TileSet
    var tileset = TileSet.new()
    tileset.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
    tileset.tile_size = Vector2i(128, 64)
    
    var floors = [
        {"id": 0, "file": "floor_tile.png"},
        {"id": 1, "file": "floor_tile_red.png"},
        {"id": 2, "file": "floor_tile_blue.png"},
        {"id": 3, "file": "floor_tile_orange.png"}
    ]
    
    for f in floors:
        var tex = load("res://Assets/Rooms/isometric/" + f["file"])
        var source = TileSetAtlasSource.new()
        source.texture = tex
        source.texture_region_size = Vector2i(128, 64)
        source.create_tile(Vector2i(0, 0))
        tileset.add_source(source, f["id"])
        
    ResourceSaver.save(tileset, "res://Assets/Rooms/isometric/Isometric_TileSet.tres")
    
    # 2. Create World2D Scene
    var world = Node2D.new()
    world.name = "World2D"
    world.y_sort_enabled = true 
    world.set_script(load("res://Scripts/World2D.gd"))
    
    # Camera
    var camera = Camera2D.new()
    camera.name = "Camera2D"
    world.add_child(camera)
    camera.owner = world
    
    # TileMapLayer (Floor)
    var floor_layer = TileMapLayer.new()
    floor_layer.name = "FloorLayer"
    floor_layer.tile_set = tileset
    floor_layer.z_index = -1 
    world.add_child(floor_layer)
    floor_layer.owner = world
    
    # Objects Container (Y-Sort)
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    world.add_child(objects)
    objects.owner = world
    
    var path_line = Line2D.new()
    path_line.name = "PathLine"
    path_line.default_color = Color(0, 1, 0, 0.5)
    path_line.width = 4.0
    world.add_child(path_line)
    path_line.owner = world
    
    # Save Scene
    var packed = PackedScene.new()
    packed.pack(world)
    ResourceSaver.save(packed, "res://Scenes/Main/World2D.tscn")
    
    print("Done! Pure 2D Isometric World generated with multi-color floors.")
    quit()
