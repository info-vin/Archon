extends Node3D

@onready var grid_map: GridMap = $GridMap

func _ready() -> void:
    setup_floor(10, 10, 0) # 0 is floor_tile
    setup_walls(10, 10, 1) # 1 is wall_corner_SW

func setup_floor(width: int = 10, depth: int = 10, floor_item_id: int = 0) -> void:
    grid_map.clear()
    for x in range(-width/2, width/2):
        for z in range(-depth/2, depth/2):
            grid_map.set_cell_item(Vector3i(x, 0, z), floor_item_id)

func setup_walls(width: int = 10, depth: int = 10, wall_item_id: int = 1) -> void:
    # Just a basic example wall setup on the North and West edges
    for x in range(-width/2, width/2):
        grid_map.set_cell_item(Vector3i(x, 1, -depth/2), wall_item_id)
    for z in range(-depth/2, depth/2):
        grid_map.set_cell_item(Vector3i(-width/2, 1, z), wall_item_id)
