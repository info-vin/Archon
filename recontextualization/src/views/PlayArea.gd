extends Control

func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	# Check if the data is a valid CardChip node
	if typeof(data) == TYPE_OBJECT and data is Control and data.has_method("set_card_data") and data.get("card_data") != null:
		return true
	return false

func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if typeof(data) == TYPE_OBJECT and data is Control:
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
					tween.chain().tween_callback(func(): data.queue_free())
				else:
					# Data Chip: just shrink slightly and line up (for now just shrink slightly)
					tween.tween_property(data, "scale", Vector2(0.8, 0.8), 0.3)
				
				await tween.finished
				
				# Inform the game state via EventBus after animation
				if Engine.has_singleton("EventBus"):
					var event_bus = Engine.get_singleton("EventBus")
					if event_bus.has_signal("card_played"):
						event_bus.card_played.emit(card_data_ref)
			)
		else:
			# Fallback if no event_queue (e.g. tests without full GameBoard owner)
			if Engine.has_singleton("EventBus"):
				var event_bus = Engine.get_singleton("EventBus")
				if event_bus.has_signal("card_played"):
					event_bus.card_played.emit(data.card_data)
