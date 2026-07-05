extends Control

func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	return true

func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if data is Control and data.has_method("set_card_data"):
		var event_bus: Node = (Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else get_node_or_null("/root/EventBus"))
		if event_bus != null and event_bus.has_signal("request_play_card"):
			event_bus.request_play_card.emit(data.card_data)
