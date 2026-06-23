extends SceneTree

func _init():
	var tileset_path = "res://Assets/Rooms/isometric/Isometric_TileSet.tres"
	var ts = TileSet.new()
	ts.tile_shape = TileSet.TILE_SHAPE_ISOMETRIC
	ts.tile_layout = TileSet.TILE_LAYOUT_DIAMOND_DOWN
	ts.tile_size = Vector2i(128, 64)
	
	var floor_tex = load("res://Assets/Rooms/isometric/floor_tile.png")
	var source = TileSetAtlasSource.new()
	source.texture = floor_tex
	source.texture_region_size = Vector2i(128, 128)
	source.create_tile(Vector2i(0, 0))
	source.get_tile_data(Vector2i(0, 0), 0).texture_origin = Vector2i(0, -32) # Align 128x128 texture inside 128x64 tile
	ts.add_source(source, 1)
	
	var err = ResourceSaver.save(ts, tileset_path)
	if err != OK:
		print("Failed to save TileSet")
		quit()
		return
		
	var scene_path = "res://Scenes/Main/Main.tscn"
	var packed_scene = ResourceLoader.load(scene_path)
	var root = packed_scene.instantiate()
	var rooms = root.get_node("World/Rooms")
	
	var room_names = ["DevRoom", "SalesRoom", "QARoom", "BreakRoom"]
	
	for r_name in room_names:
		var room = rooms.get_node_or_null(r_name)
		if not room: continue
		
		# 1. Add TileMapLayer
		var old_floor = room.get_node_or_null("FloorTile")
		if old_floor:
			old_floor.queue_free()
			
		var tml = TileMapLayer.new()
		tml.name = "FloorTileMap"
		tml.tile_set = ts
		tml.z_index = -1
		tml.y_sort_enabled = true
		room.add_child(tml)
		tml.owner = root
		
		# Paint a 4x4 floor grid
		for x in range(4):
			for y in range(4):
				tml.set_cell(Vector2i(x, y), 1, Vector2i(0, 0))
				
		# 2. Align Furniture
		# We'll map them to grid coordinates (1,1), (2,1), (1,2), etc.
		var props = []
		for child in room.get_children():
			if child is Sprite2D and child.name != "FloorTile":
				props.append(child)
				
		# Grid assignments (just sequential for now)
		var grid_positions = [
			Vector2i(1, 1),
			Vector2i(2, 1),
			Vector2i(1, 2),
			Vector2i(2, 2)
		]
		
		for i in range(props.size()):
			var prop = props[i]
			var grid_pos = grid_positions[i % grid_positions.size()]
			# Math: px = (x - y) * 64, py = (x + y) * 32
			var px = (grid_pos.x - grid_pos.y) * 64.0
			var py = (grid_pos.x + grid_pos.y) * 32.0
			prop.position = Vector2(px, py)
			# Standardize offset
			prop.offset = Vector2(0, -prop.texture.get_height() / 2.0 + 16)

	var packed = PackedScene.new()
	packed.pack(root)
	ResourceSaver.save(packed, scene_path)
	print("Isometric TileMap conversion and alignment complete.")
	quit()
