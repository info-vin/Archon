@tool
extends SceneTree

var assets = {}

func _init():
    print("Generating fully populated World2D.tscn with 13x13 grid...")
    
    # Preload assets
    assets = {
        "desk_sw": load("res://Assets/Rooms/isometric/desk_SW.png"),
        "desk_se": load("res://Assets/Rooms/isometric/desk_SE.png"),
        "chair_sw": load("res://Assets/Rooms/isometric/chair_SW.png"),
        "chair_se": load("res://Assets/Rooms/isometric/chair_SE.png"),
        "sofa_sw": load("res://Assets/Rooms/isometric/sofa_SW.png"),
        "sofa_se": load("res://Assets/Rooms/isometric/sofa_SE.png"),
        
        "vending_machine_sw": load("res://Assets/Rooms/isometric/vending_machine_SW.png"),
        "server_rack_se": load("res://Assets/Rooms/isometric/server_rack_SE.png"),
        "server_rack_sw": load("res://Assets/Rooms/isometric/server_rack_SW.png"),
        "side_cabinet_se": load("res://Assets/Rooms/isometric/side_cabinet_SE.png")
    }

    var tileset = load("res://Assets/Rooms/isometric/Isometric_TileSet.tres")
    if not tileset:
        tileset = TileSet.new()
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
    
    var world_script = load("res://Scripts/World2D.gd")
    var world = Node2D.new()
    world.name = "World2D"
    world.y_sort_enabled = true 
    world.set_script(world_script)
    world.grid_size = 13
    
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
    
    # === SETUP FLOOR ===
    var grid_size = 13
    for x in range(grid_size):
        for y in range(grid_size):
            var tile_id = 0
            if x == 6 or y == 6: tile_id = 4 # Carpet
            elif x < 6 and y < 6: tile_id = 0 # Green QA
            elif x > 6 and y < 6: tile_id = 3 # Orange Dev
            elif x < 6 and y > 6: tile_id = 2 # Blue Art
            elif x > 6 and y > 6: tile_id = 1 # Red Lounge
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))
            
    # === LAYOUT OBJECTS ===
    # Green Zone (QA): 3 server racks, 2 desks
    place_object(objects, floor_layer, Vector2i(0, 3), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(0, 4), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(0, 5), "server_rack_se")
    
    var d1 = place_object(objects, floor_layer, Vector2i(2, 1), "desk_sw")
    place_object(objects, floor_layer, Vector2i(2, 2), "chair_sw")
    
    var d2 = place_object(objects, floor_layer, Vector2i(4, 3), "desk_se")
    place_object(objects, floor_layer, Vector2i(5, 3), "chair_se")
    
    # Orange Zone (Dev): 2 desks, 1 server rack
    place_object(objects, floor_layer, Vector2i(8, 1), "desk_sw")
    place_object(objects, floor_layer, Vector2i(8, 2), "chair_sw")
    
    place_object(objects, floor_layer, Vector2i(10, 3), "desk_sw")
    place_object(objects, floor_layer, Vector2i(10, 4), "chair_sw")
    
    place_object(objects, floor_layer, Vector2i(12, 0), "server_rack_sw")
    
    # Red Zone (Lounge): 2 sofas, 2 side cabinets, 1 vending machine
    place_object(objects, floor_layer, Vector2i(8, 8), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(9, 9), "sofa_sw")
    
    place_object(objects, floor_layer, Vector2i(11, 8), "vending_machine_sw")
    place_object(objects, floor_layer, Vector2i(7, 10), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(8, 11), "side_cabinet_se")

    for child in objects.get_children():
        child.owner = world

    var packed = PackedScene.new()
    packed.pack(world)
    var err = ResourceSaver.save(packed, "res://Scenes/Main/World2D.tscn")
    if err == OK:
        print("Successfully saved fully populated World2D.tscn!")
    else:
        print("Error saving: ", err)
    quit()

func place_object(objects_node: Node2D, floor_layer: TileMapLayer, map_pos: Vector2i, type: String) -> Sprite2D:
    var tex = assets[type]
    var sprite = Sprite2D.new()
    sprite.texture = tex
    sprite.scale = Vector2(1, 1) 
    sprite.centered = true
    
    var base_offset_y = 32.0 - (tex.get_height() / 2.0)
    sprite.offset = Vector2(0, base_offset_y)
    
    sprite.y_sort_enabled = true 
    sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST 
    sprite.position = floor_layer.map_to_local(map_pos)
    
    objects_node.add_child(sprite)
    return sprite
