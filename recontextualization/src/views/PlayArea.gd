extends Control

func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	return true

func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if data is Control and data.has_method("set_card_data"):
		var locator = preload("res://src/utils/AutoloadLocator.gd")
		var event_bus: Node = locator.get_service(get_tree(), "EventBus")
		if event_bus != null and event_bus.has_signal("request_play_card"):
			event_bus.request_play_card.emit(data.card_data)
