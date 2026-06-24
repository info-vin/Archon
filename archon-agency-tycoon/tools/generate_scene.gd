@tool
extends SceneTree

var assets = {}

func _init():
    print("Restoring ABSOLUTE EXACT 1:1 layout from user screenshot...")
    
    # 載入所有圖檔資源
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
    
    # 精準 24x24 網格 (包含 1格邊界 + 10x10部門 + 2格走道)
    var GRID_SIZE = 24
    
    if world_script:
        world.set_script(world_script)
        world.set("grid_size", GRID_SIZE)
    
    var camera = Camera2D.new()
    camera.name = "Camera2D"
    world.add_child(camera)
    camera.owner = world
    
    var floor_layer = TileMapLayer.new()
    floor_layer.name = "FloorLayer"
    floor_layer.tile_set = tileset
    floor_layer.z_index = -1 
    
    # 完美對齊 Godot Editor 的十字準星 (0,0) 於綠區最左側頂點 (Grid X=1, Y=10)
    floor_layer.position = Vector2(576, -352)
    world.add_child(floor_layer)
    floor_layer.owner = world
    
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    objects.position = floor_layer.position
    world.add_child(objects)
    objects.owner = world
    
    # 攝影機置中
    camera.position = floor_layer.position + floor_layer.map_to_local(Vector2i(11, 11))
    
    # 鋪設 1:1 精準地板
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            var tile_id = 0
            if x == 0 or x == GRID_SIZE - 1 or y == 0 or y == GRID_SIZE - 1: 
                tile_id = 4 # 1格最外圍地毯
            elif (x == 11 or x == 12) or (y == 11 or y == 12): 
                tile_id = 4 # 2格十字走道
            elif x >= 1 and x <= 10 and y >= 1 and y <= 10: 
                tile_id = 0 # 綠區 10x10
            elif x >= 13 and x <= 22 and y >= 1 and y <= 10: 
                tile_id = 3 # 橘區 10x10
            elif x >= 1 and x <= 10 and y >= 13 and y <= 22: 
                tile_id = 2 # 藍區 10x10
            elif x >= 13 and x <= 22 and y >= 13 and y <= 22: 
                tile_id = 1 # 紅區 10x10
                
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))
            
    # --- 1:1 像素級精準放置家具 ---
    
    # Green Zone
    place_object(objects, floor_layer, Vector2i(7, 6), "desk_se")
    place_object(objects, floor_layer, Vector2i(8, 6), "chair_nw")
    
    # Orange Zone
    place_object(objects, floor_layer, Vector2i(16, 6), "desk_sw")
    place_object(objects, floor_layer, Vector2i(16, 7), "chair_ne")
    place_object(objects, floor_layer, Vector2i(19, 6), "desk_sw")
    place_object(objects, floor_layer, Vector2i(19, 7), "chair_ne")
    place_object(objects, floor_layer, Vector2i(20, 2), "server_rack_se")
    
    # Blue Zone
    place_object(objects, floor_layer, Vector2i(3, 16), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(3, 17), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(3, 18), "server_rack_se")
    
    # Red Zone
    place_object(objects, floor_layer, Vector2i(16, 18), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(17, 18), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(15, 18), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(18, 18), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(20, 16), "vending_machine_sw")

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
