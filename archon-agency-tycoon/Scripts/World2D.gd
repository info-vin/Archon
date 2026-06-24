extends Node2D

@onready var floor_layer: TileMapLayer = $FloorLayer
@onready var objects_node: Node2D = $Objects
@onready var path_line: Line2D = $PathLine

var astar = AStarGrid2D.new()
var grid_size = 18

var assets = {
    "desk_nw": preload("res://Assets/Rooms/isometric/desk_SW.png"),
    "chair_nw": preload("res://Assets/Rooms/isometric/chair_SW.png"),
    "sofa_sw": preload("res://Assets/Rooms/isometric/sofa_SW.png"),
    "sofa_se": preload("res://Assets/Rooms/isometric/sofa_SE.png"),
    "coffee_table": preload("res://Assets/Rooms/isometric/desk_SE.png"),
    "vending_machine": preload("res://Assets/Rooms/isometric/vending_machine_SW.png"),
    "wall_corner": preload("res://Assets/Rooms/isometric/wall_corner_SW.png")
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
    
    # 初始化尋路網格
    astar.region = Rect2i(0, 0, grid_size, grid_size)
    astar.cell_size = Vector2(128, 64)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
    astar.update()
    
    # 掃描場景中已有的物件並標記阻擋
    for child in objects_node.get_children():
        if child is Sprite2D:
            var map_pos = floor_layer.local_to_map(child.position)
            if astar.region.has_point(map_pos):
                astar.set_point_solid(map_pos, true)

# ---------------------------------------------------------
# 1. 右上角透視修正與網格鎖定 (snap_to_grid)
# ---------------------------------------------------------
func snap_to_grid(grid_pos: Vector2i) -> Vector2:
    # 完美使用 Godot 內建的 Isometric 轉換
    return floor_layer.map_to_local(grid_pos)

