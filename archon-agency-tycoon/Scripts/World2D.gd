extends Node2D

@onready var floor_layer: TileMapLayer = $FloorLayer
@onready var objects_node: Node2D = $Objects
@onready var path_line: Line2D = $PathLine

var astar = AStarGrid2D.new()
var grid_size = 10

var assets = {
    "desk_nw": preload("res://Assets/Rooms/isometric/desk_SW.png"),
    "chair_nw": preload("res://Assets/Rooms/isometric/chair_SW.png"),
    "sofa_sw": preload("res://Assets/Rooms/isometric/sofa_SW.png"),
    "sofa_se": preload("res://Assets/Rooms/isometric/sofa_SE.png"),
    "coffee_table": preload("res://Assets/Rooms/isometric/coffee_table_SE.png"),
    "vending_machine": preload("res://Assets/Rooms/isometric/vending_machine_SW.png"),
    "wall_corner": preload("res://Assets/Rooms/isometric/half_wall_SW.png")
}

# ---------------------------------------------------------
# 徹底排毒：最乾淨、最直覺的 2.5D 物件擺放邏輯
# ---------------------------------------------------------
func place_object(map_pos: Vector2i, type: String) -> Sprite2D:
    if not astar.region.has_point(map_pos) or astar.is_point_solid(map_pos):
        return null

    var tex = assets[type]
    var sprite = Sprite2D.new()
    sprite.texture = tex
    
    # === 1. 拒絕 AI 的瞎編縮放：保持 1.0 原圖比例 ===
    sprite.scale = Vector2(1, 1) 
    
    # === 2. 拒絕 AI 盲猜的 Offset ===
    # 由於我們已經在外部將圖片裁剪並縮放為 1x 比例 (scale = 1.0)
    # 現在我們手動針對每個家具設定精準的 Offset，讓你可以自由微調
    sprite.centered = true
    
    # 預設先對齊底部 (圖片高 / 2 加上網格半高 32)
    var base_offset_y = 32.0 - (tex.get_height() / 2.0)
    sprite.offset = Vector2(0, base_offset_y)
    
    # 開放手動微調區 (可直接在 Godot Editor 中修改這些數字)
    match type:
        "wall_corner":
            sprite.offset.y += -32 # 牆角往上推，對齊網格最北端點
        "desk_nw":
            sprite.offset.y += 0 # 如果覺得浮空，可填正數 (往上) 或負數 (往下)
        "chair_nw":
            sprite.offset.y += 0
        "vending_machine":
            sprite.offset.y += 0
        "coffee_table":
            sprite.offset.y += 0
        "sofa_sw", "sofa_se":
            sprite.offset.y += 0
    
    sprite.y_sort_enabled = true # 開啟深度排序
    sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST # 解決黑邊

    # === 3. 完美利用原生等距網格定位 ===
    sprite.position = snap_to_grid(map_pos)
    
    objects_node.add_child(sprite)
    astar.set_point_solid(map_pos, true) # 鎖定網格不可通行
    return sprite

func _ready():
    # 啟動 2.5D 最核心的 Y-Sort 排序
    y_sort_enabled = true
    objects_node.y_sort_enabled = true
    
    setup_floor()
    setup_astar()
    build_office_layout()

# ---------------------------------------------------------
# 1. 右上角透視修正與網格鎖定 (snap_to_grid)
# ---------------------------------------------------------
func snap_to_grid(grid_pos: Vector2i) -> Vector2:
    # 完美使用 Godot 內建的 Isometric 轉換，不再手寫數學
    # 這能確保 (0,0) 為頂點，往右下為 +X，往左下為 +Y，徹底避免透視塌陷
    return floor_layer.map_to_local(grid_pos)

# ---------------------------------------------------------
# 2. 走道地毯 (雙層迴圈)
# ---------------------------------------------------------
func setup_floor():
    floor_layer.modulate = Color(1, 1, 1, 1.0)
    for x in range(grid_size):
        for y in range(grid_size):
            var tile_id = 0 # 預設 Dev 區地板
            # 依據範例圖，走道沿著中央對角線鋪設
            if x == 4 or y == 4:
                tile_id = 4 # 地毯走道
            elif x < 4 and y < 4: tile_id = 0   # A 區 (Dev)
            elif x < 4 and y > 4: tile_id = 2   # B 區 
            elif x > 4 and y < 4: tile_id = 3   # C 區
            elif x > 4 and y > 4: tile_id = 1   # D 區 (休息室)
            
            floor_layer.set_cell(Vector2i(x, y), tile_id, Vector2i(0, 0))

func setup_astar():
    astar.region = Rect2i(0, 0, grid_size, grid_size)
    astar.cell_size = Vector2(128, 64)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    astar.update()

# ---------------------------------------------------------
# 具體佈局：辦公桌 NW、L 型沙發、緊鄰販賣機、最北端角落牆
# ---------------------------------------------------------
func build_office_layout():
    # --- 【最深處頂點的角落牆】 ---
    var wall = place_object(Vector2i(0, 0), "wall_corner")
    if wall:
        # Sprite2D.offset 調整說明：
        # 由於 snap_to_grid 預設對齊格子的「正中心」，但牆角必須壓在 (0,0) 的「最北端點」
        # 最北端點距離中心點為 (0, -32)，因此我們必須額外推移：
        wall.position += Vector2(0, -32)
        astar.set_point_solid(Vector2i(0,0), false) # 解除阻擋，以便走道通行
    
    # --- 【A 區辦公桌：NW 朝向】 ---
    var desk = place_object(Vector2i(2, 2), "desk_nw")
    orient_desk(desk, "NW")
    # 椅子放在東南側，面向西北的辦公桌
    var chair = place_object(Vector2i(3, 3), "chair_nw")
    
    # --- 【D 區休息室：L 型沙發與茶几】 ---
    place_object(Vector2i(7, 7), "coffee_table")
    
    # (6,7) 放一張 SW 面向的沙發
    place_object(Vector2i(6, 7), "sofa_sw")
    # (7,6) 利用邏輯反轉，拼出 L 型
    var sofa_other = place_object(Vector2i(7, 6), "sofa_se")
    build_l_shape_sofa(sofa_other, "SE") 
        
    # --- 【販賣機：強迫並排邏輯】 ---
    place_vending_machines(Vector2i(8, 8))

# 方向翻轉封裝
func orient_desk(sprite: Sprite2D, direction: String):
    if direction == "NW":
        # 若素材本身不是 NW，可以透過 flip_h 翻轉（但我們目前有現成的 desk_nw）
        sprite.flip_h = false

func build_l_shape_sofa(sprite: Sprite2D, target_direction: String):
    # 若我們只有 sofa_sw.png，可以透過設定 sprite.flip_h = true 來製造出 SE 的面向，構成直角 L 型
    if target_direction == "SE" and sprite.texture == assets["sofa_sw"]:
        sprite.flip_h = true

func place_vending_machines(start_pos: Vector2i):
    # 放置第一台
    if place_object(start_pos, "vending_machine"):
        # 嘗試尋找 (1,0) 右下方緊鄰格
        var next_pos = start_pos + Vector2i(1, 0)
        if not astar.is_point_solid(next_pos):
            place_object(next_pos, "vending_machine")
        else:
            # 如果右下方滿了，強制找 (0,1) 左下方緊鄰格
            next_pos = start_pos + Vector2i(0, 1)
            if not astar.is_point_solid(next_pos):
                place_object(next_pos, "vending_machine")
