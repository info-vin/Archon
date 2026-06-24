@tool
extends SceneTree

var assets = {}

func _init():
    print("Generating fully populated World2D.tscn with 18x18 grid...")
    
    # Preload assets
    assets = {
        "desk_sw": load("res://Assets/Rooms/isometric/desk_SW.png"),
        "desk_se": load("res://Assets/Rooms/isometric/desk_SE.png"),
        "chair_nw": load("res://Assets/Rooms/isometric/chair_NW.png"),
        "chair_ne": load("res://Assets/Rooms/isometric/chair_NE.png"),
        "chair_sw": load("res://Assets/Rooms/isometric/chair_SW.png"),
        "chair_se": load("res://Assets/Rooms/isometric/chair_SE.png"),
        "sofa_sw": load("res://Assets/Rooms/isometric/sofa_SW.png"),
        "sofa_se": load("res://Assets/Rooms/isometric/sofa_SE.png"),
        "vending_machine_sw": load("res://Assets/Rooms/isometric/vending_machine_SW.png"),
        "server_rack_se": load("res://Assets/Rooms/isometric/server_rack_SE.png"),
        "server_rack_sw": load("res://Assets/Rooms/isometric/server_rack_SW.png"),
        "side_cabinet_se": load("res://Assets/Rooms/isometric/side_cabinet_SE.png"),
        "half_wall_nw": load("res://Assets/Rooms/isometric/half_wall_NW.png"),
        "half_wall_ne": load("res://Assets/Rooms/isometric/half_wall_NE.png"),
        "half_wall_sw": load("res://Assets/Rooms/isometric/half_wall_SW.png"),
        "half_wall_se": load("res://Assets/Rooms/isometric/half_wall_SE.png")
    }

    var tileset = load("res://Assets/Rooms/isometric/Isometric_TileSet.tres")
    
    var world_script = load("res://Scripts/World2D.gd")
    var world = Node2D.new()
    world.name = "World2D"
    world.y_sort_enabled = true 
    world.set_script(world_script)
    world.grid_size = 18
    
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
    
    # Camera2D 對照左上的部門中心 (QA Zone is 0..7, so center is roughly 4,4)
    camera.position = floor_layer.map_to_local(Vector2i(4, 4))
    
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    world.add_child(objects)
    objects.owner = world
    
    # === SETUP FLOOR ===
    var grid_size = 18
    for x in range(grid_size):
        for y in range(grid_size):
            var tile_id = 0
            if (x == 8 or x == 9) or (y == 8 or y == 9): tile_id = 4 # Carpet
            elif x < 8 and y < 8: tile_id = 0 # Green QA
            elif x > 9 and y < 8: tile_id = 3 # Orange Dev
            elif x < 8 and y > 9: tile_id = 2 # Blue Art
            elif x > 9 and y > 9: tile_id = 1 # Red Lounge
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))
            
    # === LAYOUT OBJECTS ===
    # Draw walls on top-left boundaries
    for i in range(8):
        place_object(objects, floor_layer, Vector2i(0, i), "half_wall_se")
        place_object(objects, floor_layer, Vector2i(i, 0), "half_wall_sw")
            
    # Green Zone (QA): 3 server racks, 2 desks
    place_object(objects, floor_layer, Vector2i(1, 3), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(1, 4), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(1, 5), "server_rack_se")
    
    place_object(objects, floor_layer, Vector2i(3, 2), "desk_sw")
    place_object(objects, floor_layer, Vector2i(3, 3), "chair_ne") # Desk faces SW, so chair is on SW side facing NE
    
    place_object(objects, floor_layer, Vector2i(5, 4), "desk_se")
    place_object(objects, floor_layer, Vector2i(6, 4), "chair_nw") # Desk faces SE, so chair is on SE side facing NW
    
    # Orange Zone (Dev): 2 desks, 1 server rack
    place_object(objects, floor_layer, Vector2i(12, 2), "desk_sw")
    place_object(objects, floor_layer, Vector2i(12, 3), "chair_ne")
    
    place_object(objects, floor_layer, Vector2i(15, 4), "desk_sw")
    place_object(objects, floor_layer, Vector2i(15, 5), "chair_ne")
    
    place_object(objects, floor_layer, Vector2i(17, 1), "server_rack_sw")
    
    # Red Zone (Lounge): 2 sofas, 2 side cabinets, 1 vending machine
    place_object(objects, floor_layer, Vector2i(12, 12), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(13, 13), "sofa_sw")
    
    place_object(objects, floor_layer, Vector2i(16, 12), "vending_machine_sw")
    place_object(objects, floor_layer, Vector2i(11, 14), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(12, 15), "side_cabinet_se")

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
    var tex = assets.get(type)
    if not tex: return null
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
