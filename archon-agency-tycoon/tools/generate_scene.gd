@tool
extends SceneTree

var assets = {}

func _init():
    print("Restoring exact 1:1 layout from user screenshot...")
    
    # 載入所有必要的圖檔資源
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
    
    # 部門大小為 12x12
    # 外框 1 格，走道 2 格
    # 總大小: 1 + 12 + 2 + 12 + 1 = 28
    var GRID_SIZE = 28
    
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
    floor_layer.position = Vector2(900, 250)
    world.add_child(floor_layer)
    floor_layer.owner = world
    
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    objects.position = floor_layer.position
    world.add_child(objects)
    objects.owner = world
    
    # 攝影機對準正中央
    camera.position = floor_layer.position + floor_layer.map_to_local(Vector2i(14, 14))
    
    # 鋪設地板 (1:1 還原外圍地毯、十字走道與四個部門)
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            var tile_id = 0
            # 判斷是否為外圍地毯邊框或十字走道
            if x == 0 or x == GRID_SIZE - 1 or y == 0 or y == GRID_SIZE - 1: 
                tile_id = 4 # 外圍邊框地毯
            elif (x == 13 or x == 14) or (y == 13 or y == 14): 
                tile_id = 4 # 十字走道地毯
            elif x >= 1 and x <= 12 and y >= 1 and y <= 12: 
                tile_id = 0 # Green QA
            elif x >= 15 and x <= 26 and y >= 1 and y <= 12: 
                tile_id = 3 # Orange Dev
            elif x >= 1 and x <= 12 and y >= 15 and y <= 26: 
                tile_id = 2 # Blue Art
            elif x >= 15 and x <= 26 and y >= 15 and y <= 26: 
                tile_id = 1 # Red Lounge
                
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))
            
    # --- 放置家具 (精準對位使用者的截圖) ---
    
    # Green Zone (Top-Left): 1 桌椅
    place_object(objects, floor_layer, Vector2i(9, 9), "desk_se")
    place_object(objects, floor_layer, Vector2i(10, 9), "chair_nw")
    
    # Orange Zone (Top-Right): 2 桌椅, 1 機櫃
    place_object(objects, floor_layer, Vector2i(18, 8), "desk_sw")
    place_object(objects, floor_layer, Vector2i(18, 9), "chair_ne")
    place_object(objects, floor_layer, Vector2i(21, 8), "desk_sw")
    place_object(objects, floor_layer, Vector2i(21, 9), "chair_ne")
    place_object(objects, floor_layer, Vector2i(25, 2), "server_rack_se")
    
    # Blue Zone (Bottom-Left): 3 機櫃
    place_object(objects, floor_layer, Vector2i(3, 20), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(3, 21), "server_rack_se")
    place_object(objects, floor_layer, Vector2i(3, 22), "server_rack_se")
    
    # Red Zone (Bottom-Right): 2 沙發, 2 邊櫃, 1 販賣機
    place_object(objects, floor_layer, Vector2i(19, 21), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(20, 21), "sofa_sw")
    place_object(objects, floor_layer, Vector2i(18, 21), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(21, 21), "side_cabinet_se")
    place_object(objects, floor_layer, Vector2i(22, 19), "vending_machine_sw")

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
