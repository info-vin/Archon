extends Control

func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	# Enforce 5 card context limit
	return true

func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if data is Control and data.has_method("set_card_data"):
		# Enforce 5 card context limit here instead
		var card_count = 0
		for child in get_children():
			if child.name != "HintLabel":
				card_count += 1
		if card_count >= 5:
			return
			
		# Tutorial Error Blocking
		var t_mgr = get_tree().get_first_node_in_group("tutorial_manager")
		if t_mgr and t_mgr.is_blocking_noise_drag() and data.get("card_data"):
			var similarity = data.card_data.get("similarity")
			if similarity == null:
				similarity = 1.0
			if similarity < 0.5:
				# Reject drag
				t_mgr.show_dialog("等等！這份資料的相似度太低了。如果強行把無關的垃圾資料塞給 LLM，會引發嚴重的『模型幻覺 (Hallucination)』，系統會崩潰的！請換一張綠色的晶片。", false)
				return
		
		# Reparent the node to PlayArea
		var parent = data.get_parent()
		if parent != null:
			parent.remove_child(data)
		add_child(data)
		
		# Center the card at the drop position initially
		data.position = _at_position - (data.size / 2.0)
		
		# Animate the card falling into the center of the PlayArea
		if owner != null and owner.get("event_queue") != null:
			owner.event_queue.add_animation(func():
				var card_data_ref = data.card_data
				var tween = create_tween().set_parallel(true)
				# Move to center of PlayArea
				var target_pos = (size / 2.0) - (data.size / 2.0)
				tween.tween_property(data, "position", target_pos, 0.4).set_trans(Tween.TRANS_SPRING)
				
				var card_type = card_data_ref.get("type") if card_data_ref.get("type") != null else 1
				if card_type == 1:
					# Action Card: Dissolve and delete
					tween.tween_property(data, "modulate:a", 0.0, 0.4)
					tween.tween_property(data, "scale", Vector2(1.5, 1.5), 0.4)
					tween.chain().tween_callback(func(): 
						if is_instance_valid(data):
							data.queue_free()
					)
				else:
					# Data Chip: just shrink slightly and line up (for now just shrink slightly)
					tween.tween_property(data, "scale", Vector2(0.8, 0.8), 0.3)
				
				await get_tree().create_timer(0.4).timeout
				
				# Inform the game state via EventBus after animation
				var event_bus = get_node_or_null("/root/EventBus")
				if event_bus != null:
					if event_bus.has_signal("card_played"):
						event_bus.card_played.emit(card_data_ref)
			)
		else:
			# Fallback if no event_queue (e.g. tests without full GameBoard owner)
			var event_bus = get_node_or_null("/root/EventBus")
			if event_bus != null:
				if event_bus.has_signal("card_played"):
					event_bus.card_played.emit(data.card_data)
