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
			
		# Reparent the node to PlayArea
		var parent = data.get_parent()
		if parent != null:
			parent.remove_child(data)
		add_child(data)
		
		# Center the card at the drop position initially
		data.position = _at_position - (data.size / 2.0)
		
		if owner != null and owner.get("event_queue") != null:
			owner.event_queue.add_animation(func():
				var tween = create_tween()
				var target_pos = (size / 2.0) - (data.size / 2.0)
				tween.tween_property(data, "position", target_pos, 0.4).set_trans(Tween.TRANS_SPRING)
				tween.parallel().tween_property(data, "scale", Vector2(0.8, 0.8), 0.3)
				await get_tree().create_timer(0.4).timeout
				
				var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
				if event_bus != null and event_bus.has_signal("card_played"):
					event_bus.card_played.emit(data.card_data)
			)
		else:
			# Fallback if no event_queue (e.g. tests without full GameBoard owner)
			var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
			if event_bus != null:
				if event_bus.has_signal("card_played"):
					event_bus.card_played.emit(data.card_data)
