class_name HandController
extends RefCounted

static func render_hand(hand_area: Control, game_state: RefCounted, config: Resource, play_callback: Callable) -> void:
	for child in hand_area.get_children():
		child.queue_free()
		
	var scene_path = config.get("card_scene_path") if config and config.get("card_scene_path") else "res://Scenes/UI/CardUI.tscn"
	var card_scene = load(scene_path)
	var hand_width = hand_area.size.x if hand_area.size.x > 0 else 650.0
	var card_width = 180.0
	var total_cards = game_state.hand.size()
	
	var max_spacing = 130.0
	var required_width = card_width + (total_cards - 1) * max_spacing
	var spacing = max_spacing
	if required_width > hand_width:
		spacing = (hand_width - card_width) / max(1, total_cards - 1)
	if total_cards <= 1: spacing = 0
	
	var total_width = card_width + (total_cards - 1) * spacing
	var start_x = (hand_width - total_width) / 2.0
	
	for i in range(total_cards):
		var card = game_state.hand[i]
		var card_ui = card_scene.instantiate()
		hand_area.add_child(card_ui)
		
		var target_x = start_x + (i * spacing)
		
		var t = 0.5 if total_cards <= 1 else float(i) / float(total_cards - 1)
		var curve_y = abs(t - 0.5) * abs(t - 0.5) * 150.0
		var rotation_deg = lerpf(-15.0, 15.0, t)
		
		card_ui.position = Vector2(target_x, 10 + curve_y)
		card_ui.rotation_degrees = rotation_deg
		card_ui.original_y = card_ui.position.y
		
		card_ui.setup(card, i)
		card_ui.pressed.connect(func(): play_callback.call(card_ui.card_index))
		card_ui.animate_draw(card_ui.position)
