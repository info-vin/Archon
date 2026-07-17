extends Control

func _ready() -> void:
	var hud_bg = ColorRect.new()
	hud_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	
	var mat = preload("res://src/views/shaders/PlayAreaHUD.tres")
	if mat:
		hud_bg.material = mat
		
	# Add it to the top of the children list so it draws behind cards
	add_child(hud_bg)
	move_child(hud_bg, 0)

func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	return true

func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if data is Control and data.has_method("set_card_data"):
		var locator = preload("res://src/utils/AutoloadLocator.gd")
		var event_bus: Node = locator.get_service(get_tree(), "EventBus")
		if event_bus != null and event_bus.has_signal("request_play_card"):
			event_bus.request_play_card.emit(data.card_data)
