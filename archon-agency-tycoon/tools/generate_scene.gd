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
    
    # 精準 34x24 網格 
    # X軸: 1(邊界) + 15(部門) + 2(走道) + 15(部門) + 1(邊界) = 34
    # Y軸: 1(邊界) + 10(部門) + 2(走道) + 10(部門) + 1(邊界) = 24
    var GRID_SIZE_X = 34
    var GRID_SIZE_Y = 24
    
    if world_script:
        world.set_script(world_script)
        # 暫時把 grid_size 設成最大邊界，避免越界
        world.set("grid_size", 34)
    
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
    camera.position = floor_layer.position + floor_layer.map_to_local(Vector2i(17, 12))
    
    # 鋪設 1:1 精準地板
    for x in range(GRID_SIZE_X):
        for y in range(GRID_SIZE_Y):
            var tile_id = 0
            if x == 0 or x == GRID_SIZE_X - 1 or y == 0 or y == GRID_SIZE_Y - 1: 
                tile_id = 4 # 外圍地毯
            elif (x == 16 or x == 17) and y > 0 and y < GRID_SIZE_Y - 1: 
                tile_id = 4 # 垂直走道
            elif (y == 11 or y == 12) and x > 0 and x < GRID_SIZE_X - 1: 
                tile_id = 4 # 水平走道
            elif x >= 1 and x <= 15 and y >= 1 and y <= 10: 
                tile_id = 0 # 綠區 15x10
            elif x >= 18 and x <= 32 and y >= 1 and y <= 10: 
                tile_id = 3 # 橘區 15x10
            elif x >= 1 and x <= 15 and y >= 13 and y <= 22: 
                tile_id = 2 # 藍區 15x10
            elif x >= 18 and x <= 32 and y >= 13 and y <= 22: 
                tile_id = 1 # 紅區 15x10
                
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))
            
    # --- 1:1 像素級精準放置家具 ---
    
    # Green Zone (15x10)
    place_object(objects, floor_layer, Vector2i(12, 6), "desk_se")
    place_object(objects, floor_layer, Vector2i(13, 6), "chair_nw")
    
    # Orange Zone (15x10)
    place_object(objects, floor_layer, Vector2i(21, 6), "desk_sw")
    place_object(objects, floor_layer, Vector2i(21, 7), "chair_ne")
    place_object(objects, floor_layer, Vector2i(24, 6), "desk_sw")
    place_object(objects, floor_layer, Vector2i(24, 7), "chair_ne")
    place_object(objects, floor_layer, Vector2i(30, 2), "server_rack_se")
    
    # Blue Zone (15x10)
    place_object(objects, floor_layer, Vector2i(3, 16), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(3, 17), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(3, 18), "server_rack_se")
    
    # Red Zone (15x10)
    place_object(objects, floor_layer, Vector2i(21, 18), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(22, 18), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(20, 18), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(23, 18), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(25, 16), "vending_machine_sw")

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
