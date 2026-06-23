extends SceneTree

func _init():
	var scene_path = "res://Scenes/Main/Main.tscn"
	var packed_scene = ResourceLoader.load(scene_path)
	var root = packed_scene.instantiate()
	var rooms = root.get_node("World/Rooms")
	
	var light_tex = load("res://Assets/Rooms/isometric/neon_light.tres")
	
	var room_colors = {
		"DevRoom": Color("#39ff14"),
		"SalesRoom": Color("#fde910"),
		"QARoom": Color("#ff003c"),
		"BreakRoom": Color("#00ffff")
	}
	
	# Load assets
	var tex_desk = load("res://Assets/Rooms/isometric/desk_SW.png")
	var tex_server = load("res://Assets/Rooms/isometric/server_rack_SW.png")
	var tex_chair = load("res://Assets/Rooms/isometric/chair_SW.png")
	var tex_wall = load("res://Assets/Rooms/isometric/wall_corner_SW.png")
	var tex_sofa = load("res://Assets/Rooms/isometric/sofa_SW.png")
	
	for r_name in room_colors.keys():
		var room = rooms.get_node_or_null(r_name)
		if not room: continue
		
		var tml = room.get_node_or_null("FloorTileMap")
		if not tml: continue
		
		# 1. Clear old props (everything that is a Sprite2D)
		for child in room.get_children():
			if child is Sprite2D:
				child.free() # immediately remove so we can replace
				
		# 2. Define standard layout (Leaving walking space!)
		# 4x4 Grid means (0,0) to (3,3)
		# (0,0) is top corner -> Wall
		# (0,1) is left wall -> Server
		# (2,2) is center -> Desk
		# (3,2) is bottom right of desk -> Chair
		
		var layout = []
		if r_name == "BreakRoom":
			layout = [
				{"name": "WallCorner", "tex": tex_wall, "pos": Vector2i(0, 0), "light": false},
				{"name": "Sofa", "tex": tex_sofa, "pos": Vector2i(2, 1), "light": true},
				{"name": "Sofa2", "tex": tex_sofa, "pos": Vector2i(1, 2), "light": false}
			]
		else:
			layout = [
				{"name": "WallCorner", "tex": tex_wall, "pos": Vector2i(0, 0), "light": false},
				{"name": "ServerRack", "tex": tex_server, "pos": Vector2i(0, 1), "light": true},
				{"name": "Desk", "tex": tex_desk, "pos": Vector2i(2, 2), "light": true},
				{"name": "Chair", "tex": tex_chair, "pos": Vector2i(3, 2), "light": false}
			]
			
		for item in layout:
			var sprite = Sprite2D.new()
			sprite.name = item["name"]
			sprite.texture = item["tex"]
			sprite.y_sort_enabled = true
			
			# The Magic Formula for Auto-Alignment
			# 1. Get exact pixel center of the diamond tile
			var local_pos = tml.map_to_local(item["pos"])
			sprite.position = local_pos
			
			# 2. Offset: The anchor point of the PNG should be its bottom center (feet).
			# Since the image is 128x128, bottom center is X=0, Y=64 (when centered=true)
			# We offset it up by height/2 (64) so its feet touch the tile center.
			# We add +16 to account for the thickness of the floor tile diamond.
			# BASED ON ASCII ART: The desk's feet are at y=116. Image center is at y=64. 
			# Distance to center is 52. To put feet at tile center, shift image up by 52.
			sprite.offset = Vector2(0, -52)
			
			room.add_child(sprite)
			sprite.owner = root
			
			if item["light"]:
				var light = PointLight2D.new()
				light.name = "NeonLight"
				light.texture = light_tex
				light.color = room_colors[r_name]
				light.energy = 1.2
				light.range_z_min = -10
				light.range_z_max = 10
				light.shadow_enabled = true
				light.position = Vector2(0, -32) # Light comes from the middle of the object
				sprite.add_child(light)
				light.owner = root

	var packed = PackedScene.new()
	packed.pack(root)
	ResourceSaver.save(packed, scene_path)
	print("Intelligent Spatial Alignment and Asset Population complete.")
	quit()
