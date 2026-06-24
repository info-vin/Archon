extends Node2D

@onready var floor_layer: TileMapLayer = $FloorLayer
@onready var objects_node: Node2D = $Objects
@onready var path_line: Line2D = $PathLine

var astar = AStarGrid2D.new()
var grid_rect = Rect2i(-5, -5, 10, 10)

# Furniture and Wall assets
var assets = {
    "desk": preload("res://Assets/Rooms/isometric/desk_SW.png"),
    "server": preload("res://Assets/Rooms/isometric/server_rack_SW.png"),
    "chair": preload("res://Assets/Rooms/isometric/chair_SW.png")
}

var current_agent_pos: Vector2i = Vector2i(0, 0)
var agent_sprite: Sprite2D

func _ready():
    # A. 動態鋪設 128x64 地磚
    setup_floor()
    
    # C. 初始化 AStarGrid2D 尋路
    setup_astar()
    
    # 初始化一個代表員工的 Sprite
    spawn_agent()

func setup_floor():
    for x in range(grid_rect.position.x, grid_rect.end.x):
        for y in range(grid_rect.position.y, grid_rect.end.y):
            # Source ID 0, Atlas coords (0,0)
            floor_layer.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))

func setup_astar():
    astar.region = grid_rect
    astar.cell_size = Vector2(128, 64)
    # Isometric 通常只允許四向移動（對角線在畫面上是上下左右）
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    astar.update()

func spawn_agent():
    agent_sprite = Sprite2D.new()
    # 我們暫時用椅子當人員代表
    agent_sprite.texture = assets["chair"]
    agent_sprite.centered = false
    agent_sprite.offset = Vector2(-assets["chair"].get_width() / 2.0, -assets["chair"].get_height())
    agent_sprite.position = floor_layer.map_to_local(current_agent_pos)
    objects_node.add_child(agent_sprite)

func _unhandled_input(event):
    if event is InputEventMouseButton and event.pressed:
        var map_pos = floor_layer.local_to_map(get_global_mouse_position())
        
        if not grid_rect.has_point(map_pos):
            return
            
        if event.button_index == MOUSE_BUTTON_LEFT:
            # 左鍵：放置家具 (B. 家具點擊擺放邏輯)
            if map_pos != current_agent_pos and not astar.is_point_solid(map_pos):
                place_object(map_pos, "desk")
                
        elif event.button_index == MOUSE_BUTTON_RIGHT:
            # 右鍵：尋路與移動 (C. 員工 AStarGrid2D 尋路)
            move_agent_to(map_pos)

func place_object(map_pos: Vector2i, type: String):
    var tex = assets[type]
    var sprite = Sprite2D.new()
    sprite.texture = tex
    sprite.centered = false
    # 最精華的一步：底部尖角對齊原點！
    sprite.offset = Vector2(-tex.get_width() / 2.0, -tex.get_height())
    
    # 把物件放進開啟了 Y-Sort 的容器中
    sprite.position = floor_layer.map_to_local(map_pos)
    objects_node.add_child(sprite)
    
    # 標記該網格為不可行走
    astar.set_point_solid(map_pos, true)

func move_agent_to(target_pos: Vector2i):
    var path = astar.get_id_path(current_agent_pos, target_pos)
    if path.is_empty():
        print("無法到達目的地！")
        path_line.clear_points()
        return
        
    # 畫出尋路軌跡
    path_line.clear_points()
    for point in path:
        path_line.add_point(floor_layer.map_to_local(point))
        
    # 瞬間移動 (實際遊戲會用 Tween 或 _process 平滑移動)
    current_agent_pos = target_pos
    agent_sprite.position = floor_layer.map_to_local(target_pos)
