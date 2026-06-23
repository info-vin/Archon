extends Control
class_name Minimap

func update_minimap(office_grid: Node2D, agent_manager: Object, agent_views: Dictionary) -> void:
	var minimap_size = size
	if minimap_size.x == 0 or minimap_size.y == 0: return
	
	# Clear old dots and rooms (except "BG" background node if exists)
	for child in get_children():
		if child.name != "BG":
			child.queue_free()
			
	if not office_grid: return
	
	var content_x = max(office_grid.size.x, 800.0)
	var content_y = max(office_grid.size.y, 600.0)
	var scale_x = minimap_size.x / content_x
	var scale_y = minimap_size.y / content_y
	var uniform_scale = min(scale_x, scale_y)
	var offset_x = (minimap_size.x - content_x * uniform_scale) / 2.0
	var offset_y = (minimap_size.y - content_y * uniform_scale) / 2.0
	var offset = Vector2(offset_x, offset_y)
	
	# Draw all rooms and hallways
	for room in office_grid.get_children():
		var final_node: Control
		
		# Find if this room has a background texture
		var tex = null
		for c in room.get_children():
			if c is TextureRect:
				tex = c.texture
				break
				
		if tex != null:
			var tex_rect = TextureRect.new()
			tex_rect.texture = tex
			tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			# Dim the texture a bit to make agents pop
			tex_rect.modulate = Color(0.6, 0.6, 0.6, 1.0)
			final_node = tex_rect
		else:
			var rect = ColorRect.new()
			rect.color = Color(0.15, 0.15, 0.15, 1.0) # Dark gray for hallways
			final_node = rect
			
		final_node.position = offset + room.position * uniform_scale
		final_node.size = room.size * uniform_scale
		add_child(final_node)
		
		# Draw neon border if it's a room
		if room.has_meta("neon_color"):
			var border = ReferenceRect.new()
			border.editor_only = false
			border.border_color = room.get_meta("neon_color")
			border.border_width = 1.0
			border.position = final_node.position
			border.size = final_node.size
			add_child(border)

	# Draw agents
	if agent_manager:
		for agent_id in agent_views.keys():
			var agent = agent_manager.get_agent(agent_id)
			var view = agent_views[agent_id]
			if not agent or not view or not view.get_parent(): continue
			
			var dot = ColorRect.new()
			var color = Color.WHITE
			if agent.role == 1: color = Color("#39ff14")
			elif agent.role == 0: color = Color("#fde910")
			elif agent.role == 2: color = Color("#ff003c")
			
			dot.color = color
			dot.size = Vector2(4, 4)
			
			var room_pos = view.get_parent().position
			var global_pos = room_pos + view.position
			dot.position = offset + global_pos * uniform_scale
			
			add_child(dot)
