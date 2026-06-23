extends SceneTree

func _init():
	# 1. Update env.tres for true Cyberpunk Neon Glow
	var env_path = "res://env.tres"
	var env = load(env_path) as Environment
	if not env:
		env = Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.glow_enabled = true
	env.set("glow_levels/1", 1.0)
	env.set("glow_levels/2", 1.0)
	env.set("glow_levels/3", 1.0)
	env.set("glow_levels/4", 0.5)
	env.set("glow_levels/5", 0.0)
	env.glow_intensity = 1.2
	env.glow_strength = 1.1
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	env.glow_hdr_threshold = 0.8 # Lower threshold so bright neon colors bloom
	ResourceSaver.save(env, env_path)
	
	# 2. Add CanvasModulate and PointLight2D to Main.tscn
	var scene_path = "res://Scenes/Main/Main.tscn"
	var packed_scene = ResourceLoader.load(scene_path)
	var root = packed_scene.instantiate()
	var rooms = root.get_node("World/Rooms")
	
	# Darken the world
	var modulate = rooms.get_node_or_null("WorldModulate")
	if not modulate:
		modulate = CanvasModulate.new()
		modulate.name = "WorldModulate"
		modulate.color = Color(0.2, 0.2, 0.25) # Dark, slightly blue ambient light
		rooms.add_child(modulate)
		modulate.owner = root
		
	# Create a basic radial light texture
	var grad = Gradient.new()
	grad.add_point(0.0, Color(1, 1, 1, 1))
	grad.add_point(1.0, Color(0, 0, 0, 1))
	var tex = GradientTexture2D.new()
	tex.gradient = grad
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(0.5, 0.0)
	tex.width = 256
	tex.height = 256
	var light_tex_path = "res://Assets/Rooms/isometric/neon_light.tres"
	ResourceSaver.save(tex, light_tex_path)
	var loaded_tex = load(light_tex_path)
	
	# Add PointLights to furniture
	var room_colors = {
		"DevRoom": Color("#39ff14"),
		"SalesRoom": Color("#fde910"),
		"QARoom": Color("#ff003c"),
		"BreakRoom": Color("#00ffff")
	}
	
	for r_name in room_colors.keys():
		var room = rooms.get_node_or_null(r_name)
		if not room: continue
		
		var neon_color = room_colors[r_name]
		for child in room.get_children():
			if child is Sprite2D and child.name != "FloorTile" and not child.has_node("NeonLight"):
				var light = PointLight2D.new()
				light.name = "NeonLight"
				light.texture = loaded_tex
				light.color = neon_color
				light.energy = 1.5
				light.range_z_min = -10
				light.range_z_max = 10
				light.shadow_enabled = true
				# Offset the light to appear slightly above the base
				light.position = Vector2(0, -32)
				child.add_child(light)
				light.owner = root

	var packed = PackedScene.new()
	packed.pack(root)
	ResourceSaver.save(packed, scene_path)
	print("Lighting & Post-Processing standard applied.")
	quit()
