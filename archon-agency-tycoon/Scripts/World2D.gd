extends Node2D

@onready var floor_layer: TileMapLayer = $FloorLayer
@onready var objects_node: Node2D = $Objects
@onready var path_line: Line2D = $PathLine

var astar = AStarGrid2D.new()

# 設定四個部門的方形區域 (以 8x8 為一個部門)
# Dev (左上), QA (右上), Break (左下), Sales (右下)
var grid_rect = Rect2i(-10, -10, 20, 20)

var assets = {
    "desk_sw": preload("res://Assets/Rooms/isometric/desk_SW.png"),
    "desk_se": preload("res://Assets/Rooms/isometric/desk_SE.png"),
    "server_sw": preload("res://Assets/Rooms/isometric/server_rack_SW.png"),
    "server_se": preload("res://Assets/Rooms/isometric/server_rack_SE.png"),
    "chair_sw": preload("res://Assets/Rooms/isometric/chair_SW.png"),
    "chair_se": preload("res://Assets/Rooms/isometric/chair_SE.png"),
    "sofa_sw": preload("res://Assets/Rooms/isometric/sofa_SW.png"),
    "sofa_se": preload("res://Assets/Rooms/isometric/sofa_SE.png"),
    "vending_machine": preload("res://Assets/Rooms/isometric/vending_machine_SW.png"),
    "coffee_machine": preload("res://Assets/Rooms/isometric/coffee_machine_SW.png"),
    "wall": preload("res://Assets/Rooms/isometric/wall_corner_SW.png")
}

# 根據物件類型設定縮放比例 (讓 AI 產出的大圖縮小至符合等距網格)
var scale_factors = {
    "desk_sw": Vector2(0.5, 0.5),
    "desk_se": Vector2(0.5, 0.5),
    "server_sw": Vector2(0.4, 0.4),
    "server_se": Vector2(0.4, 0.4),
    "chair_sw": Vector2(0.5, 0.5),
    "chair_se": Vector2(0.5, 0.5),
    "sofa_sw": Vector2(0.5, 0.5),
    "sofa_se": Vector2(0.5, 0.5),
    "vending_machine": Vector2(0.25, 0.25), # 販賣機縮小更多
    "coffee_machine": Vector2(0.25, 0.25),  # 咖啡機縮小更多
    "wall": Vector2(0.6, 0.6)
}

var current_agent_pos: Vector2i = Vector2i(0, 0)
var agent_sprite: Sprite2D

func _ready():
    setup_floor()
    setup_astar()

func setup_floor():
    # 恢復地板不透明度
    floor_layer.modulate = Color(1, 1, 1, 1.0) 
    # 建立接近正方形的 4 個部門
    for x in range(grid_rect.position.x, grid_rect.end.x):
        for y in range(grid_rect.position.y, grid_rect.end.y):
            # 留出十字走道 (x=0 或 y=0)
            if x == 0 or y == 0:
                continue
                
            var tile_id = 0 
            if x > 0 and y > 0: tile_id = 1       # Sales (右下)
            elif x < 0 and y > 0: tile_id = 2     # Break (左下)
            elif x > 0 and y < 0: tile_id = 3     # QA (右上)
            elif x < 0 and y < 0: tile_id = 0     # Dev (左上)
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))

func setup_astar():
    astar.region = grid_rect
    astar.cell_size = Vector2(128, 64)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    astar.update()

func spawn_agent(pos: Vector2i):
    agent_sprite = Sprite2D.new()
    agent_sprite.texture = assets["chair_sw"]
    agent_sprite.scale = scale_factors["chair_sw"]
    agent_sprite.centered = false
    agent_sprite.offset = Vector2(-assets["chair_sw"].get_width() / 2.0, -assets["chair_sw"].get_height())
    agent_sprite.position = floor_layer.map_to_local(pos)
    agent_sprite.modulate = Color(1, 0, 1) # 粉紅色小人
    current_agent_pos = pos
    objects_node.add_child(agent_sprite)

func place_object(map_pos: Vector2i, type: String):
    var tex = assets[type]
    var sprite = Sprite2D.new()
    sprite.texture = tex
    sprite.scale = scale_factors[type]
    sprite.centered = false
    # 根據縮放比例重新計算原點偏移
    sprite.offset = Vector2(-tex.get_width() / 2.0, -tex.get_height())
    sprite.position = floor_layer.map_to_local(map_pos)
    objects_node.add_child(sprite)
    astar.set_point_solid(map_pos, true)

func move_agent_to(target_pos: Vector2i):
    var path = astar.get_id_path(current_agent_pos, target_pos)
    if path.is_empty(): return
        
    path_line.clear_points()
    for point in path:
        path_line.add_point(floor_layer.map_to_local(point))
        
    current_agent_pos = target_pos
    agent_sprite.position = floor_layer.map_to_local(target_pos)
