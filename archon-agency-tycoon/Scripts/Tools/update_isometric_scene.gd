extends SceneTree

func _init():
	var scene_path = "res://Scenes/Main/Main.tscn"
	var packed_scene = ResourceLoader.load(scene_path)
	if not packed_scene:
		print("Failed to load Main.tscn")
		return
		
	var root = packed_scene.instantiate()
	var rooms = root.get_node("World/Rooms")
	
	if not rooms:
		print("Rooms node not found")
		return
		
	rooms.y_sort_enabled = true
	
	var floor_tex = load("res://Assets/Rooms/isometric/floor_tile.png")
	var desk_tex = load("res://Assets/Rooms/isometric/desk_SW.png")
	var server_tex = load("res://Assets/Rooms/isometric/server_rack_SW.png")
	var sofa_tex = load("res://Assets/Rooms/isometric/sofa_SW.png")
	
	var room_data = [
		{"name": "DevRoom", "floor": floor_tex, "props": [{"name": "Desk", "tex": desk_tex, "points": ["DeskPoint_1", "DeskPoint_2", "DeskPoint_3", "DeskPoint_4"]}, {"name": "Server", "tex": server_tex, "points": ["StandPoint_1"]}]},
		{"name": "SalesRoom", "floor": floor_tex, "props": [{"name": "Desk", "tex": desk_tex, "points": ["DeskPoint_1", "DeskPoint_2", "DeskPoint_3", "DeskPoint_4"]}]},
		{"name": "QARoom", "floor": floor_tex, "props": [{"name": "Desk", "tex": desk_tex, "points": ["DeskPoint_1", "DeskPoint_2"]}, {"name": "Server", "tex": server_tex, "points": ["StandPoint_1"]}]},
		{"name": "BreakRoom", "floor": floor_tex, "props": [{"name": "Sofa", "tex": sofa_tex, "points": ["DeskPoint_1", "DeskPoint_2", "DeskPoint_3"]}]}
	]
	
	for data in room_data:
		var room = rooms.get_node_or_null(data["name"])
		if not room: continue
		
		room.y_sort_enabled = true
		
		# Replace Background
		var bg = room.get_node_or_null("BackgroundTexture")
		if bg:
			bg.texture = data["floor"]
			bg.z_index = -1 # Floor is always at the bottom
			bg.name = "FloorTile"
			bg.centered = false
			bg.y_sort_enabled = false
			
		# Add Props based on Marker2Ds
		for prop_group in data["props"]:
			for point_name in prop_group["points"]:
				var marker = room.get_node_or_null(point_name)
				if marker:
					var prop = Sprite2D.new()
					prop.name = prop_group["name"] + "_" + point_name
					prop.texture = prop_group["tex"]
					prop.position = marker.position
					prop.offset = Vector2(0, -prop_group["tex"].get_height() / 2.0 + 16) # Adjust origin to base
					prop.y_sort_enabled = true
					room.add_child(prop)
					prop.owner = root # Must set owner for packing
	
	var packed = PackedScene.new()
	packed.pack(root)
	var err = ResourceSaver.save(packed, scene_path)
	if err == OK:
		print("Successfully updated Main.tscn with isometric assets and Y-Sort!")
	else:
		print("Failed to save Main.tscn, error code: ", err)
	quit()
