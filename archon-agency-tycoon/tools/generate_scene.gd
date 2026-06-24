@tool
extends SceneTree

var assets = {}

func _init():
    print("Generating fully populated World2D.tscn with 22x22 grid (10x10 departments)...")
    
    assets = {
        "desk_sw": load("res://Assets/Rooms/isometric/desk_SW.png"),
        "chair_ne": load("res://Assets/Rooms/isometric/chair_NE.png"),
        "sofa_sw": load("res://Assets/Rooms/isometric/sofa_SW.png"),
        "vending_machine_sw": load("res://Assets/Rooms/isometric/vending_machine_SW.png"),
        "server_rack_se": load("res://Assets/Rooms/isometric/server_rack_SE.png"),
        "server_rack_sw": load("res://Assets/Rooms/isometric/server_rack_SW.png"),
        "side_cabinet_se": load("res://Assets/Rooms/isometric/side_cabinet_SE.png"),
        "half_wall_nw": load("res://Assets/Rooms/isometric/half_wall_NW.png"),
        "half_wall_sw": load("res://Assets/Rooms/isometric/half_wall_SW.png"),
        "half_wall_se": load("res://Assets/Rooms/isometric/half_wall_SE.png")
    }

    var tileset = load("res://Assets/Rooms/isometric/Isometric_TileSet.tres")
    var world_script = load("res://Scripts/World2D.gd")
    var world = Node2D.new()
    world.name = "World2D"
    world.y_sort_enabled = true 
    world.set_script(world_script)
    world.grid_size = 22
    
    var camera = Camera2D.new()
    camera.name = "Camera2D"
    world.add_child(camera)
    camera.owner = world
    
    var floor_layer = TileMapLayer.new()
    floor_layer.name = "FloorLayer"
    floor_layer.tile_set = tileset
    floor_layer.z_index = -1 
    floor_layer.position = Vector2(900, 250)
    world.add_child(floor_layer)
    floor_layer.owner = world
    
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    objects.position = floor_layer.position
    world.add_child(objects)
    objects.owner = world
    
    camera.position = floor_layer.position + floor_layer.map_to_local(Vector2i(11, 11))
    
    for x in range(22):
        for y in range(22):
            var tile_id = 0
            if (x == 10 or x == 11) or (y == 10 or y == 11): tile_id = 4
            elif x < 10 and y < 10: tile_id = 0
            elif x > 11 and y < 10: tile_id = 3
            elif x < 10 and y > 11: tile_id = 2
            elif x > 11 and y > 11: tile_id = 1
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))
            
    # Green Zone (Top-Left): 1 Desk
    place_object(objects, floor_layer, Vector2i(7, 7), "desk_sw")
    place_object(objects, floor_layer, Vector2i(7, 8), "chair_ne")
    
    # Orange Zone (Top-Right): 2 Desks, 1 Server rack
    place_object(objects, floor_layer, Vector2i(14, 6), "desk_sw")
    place_object(objects, floor_layer, Vector2i(14, 7), "chair_ne")
    place_object(objects, floor_layer, Vector2i(17, 6), "desk_sw")
    place_object(objects, floor_layer, Vector2i(17, 7), "chair_ne")
    place_object(objects, floor_layer, Vector2i(20, 2), "server_rack_sw")
    
    # Blue Zone (Bottom-Left): 3 Server racks
    place_object(objects, floor_layer, Vector2i(2, 16), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(2, 17), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(2, 18), "server_rack_se")
    
    # Red Zone (Bottom-Right): 2 Sofas, 2 Side cabinets, 1 Vending machine
    place_object(objects, floor_layer, Vector2i(15, 16), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(16, 16), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(14, 16), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(17, 16), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(18, 14), "vending_machine_sw")

    for child in objects.get_children():
        child.owner = world

    var packed = PackedScene.new()
    packed.pack(world)
    ResourceSaver.save(packed, "res://Scenes/Main/World2D.tscn")
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
