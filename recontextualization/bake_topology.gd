extends SceneTree

func _init():
	var scene_path = "res://src/views/CharacterDashboard.tscn"
	var packed_scene = ResourceLoader.load(scene_path)
	if not packed_scene:
		print("Failed to load scene")
		return
		
	var scene = packed_scene.instantiate()
	var topology_panel = scene.get_node("HBoxContainer/TopologyPanel")
	var lines_container = topology_panel.get_node("LinesContainer")
	var nodes_container = topology_panel.get_node("NodesContainer")
	
	# Clear existing if any
	for c in lines_container.get_children():
		c.queue_free()
	for c in nodes_container.get_children():
		c.queue_free()
		
	var node_positions = [
		Vector2(400, 300), # Center
		Vector2(400, 150), # Top
		Vector2(550, 300), # Right
		Vector2(400, 450), # Bottom
		Vector2(250, 300)  # Left
	]
	var connections = [[0, 1], [0, 2], [0, 3], [0, 4]]
	var line_shader = load("res://src/shaders/DataFlowLine.gdshader")
	
	for i in range(connections.size()):
		var conn = connections[i]
		var line = Line2D.new()
		line.name = "TopologyLine_%d" % i
		line.add_point(node_positions[conn[0]])
		line.add_point(node_positions[conn[1]])
		line.width = 4.0
		line.default_color = Color(0.2, 0.8, 1.0, 1.0)
		
		var mat = ShaderMaterial.new()
		mat.shader = line_shader
		line.material = mat
		
		lines_container.add_child(line)
		line.owner = scene
		
	for i in range(node_positions.size()):
		var btn = TextureButton.new()
		btn.name = "TopologyNode_%d" % i
		btn.position = node_positions[i] - Vector2(32, 32)
		btn.custom_minimum_size = Vector2(64, 64)
		
		nodes_container.add_child(btn)
		btn.owner = scene
		
	var err = ResourceSaver.save(scene, scene_path)
	if err == OK:
		print("Successfully baked Topology Web into ", scene_path)
	else:
		print("Failed to save scene: ", err)
	quit()
