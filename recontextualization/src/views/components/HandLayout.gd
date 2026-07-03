extends Container
class_name HandLayout

@export var radius: float = 800.0
@export var angle_spread_degrees: float = 40.0
@export var vertical_offset: float = 600.0
@export var hover_scale: float = 1.2
@export var hover_y_offset: float = -40.0

func _notification(what: int) -> void:
	if what == NOTIFICATION_SORT_CHILDREN:
		_layout_cards()

func _layout_cards() -> void:
	var children: Array[Node] = get_children()
	var count: int = children.size()
	if count == 0:
		return
		
	var angle_spread: float = deg_to_rad(angle_spread_degrees)
	var start_angle: float = -angle_spread / 2.0
	var step_angle: float = 0.0
	if count > 1:
		step_angle = angle_spread / float(count - 1)
		
	for i in range(count):
		var child: Node = children[i]
		if not child is Control:
			continue
			
		var current_angle: float = start_angle + (step_angle * float(i))
		if count == 1:
			current_angle = 0.0
			
		# Calculate position using polar coordinates
		var pos_x: float = sin(current_angle) * radius
		var pos_y: float = -cos(current_angle) * radius + vertical_offset
		
		var target_pos: Vector2 = Vector2(pos_x, pos_y) + (size / 2.0) - (child.size / 2.0)
		target_pos.y += 100 # Push down to screen bottom
		
		# Connect hover signals if not connected
		if not child.has_meta("hover_connected"):
			child.mouse_entered.connect(_on_card_hovered.bind(child, true, target_pos, current_angle))
			child.mouse_exited.connect(_on_card_hovered.bind(child, false, target_pos, current_angle))
			child.set_meta("hover_connected", true)
		
		# Animate to position
		if not child.has_meta("is_hovered") or not child.get_meta("is_hovered"):
			var tween: Tween = create_tween().set_parallel(true)
			tween.tween_property(child, "position", target_pos, 0.2).set_trans(Tween.TRANS_QUAD)
			tween.tween_property(child, "rotation", current_angle, 0.2).set_trans(Tween.TRANS_QUAD)
			tween.tween_property(child, "scale", Vector2(1.0, 1.0), 0.2).set_trans(Tween.TRANS_QUAD)
			child.z_index = i

func _on_card_hovered(card: Control, is_hovered: bool, base_pos: Vector2, base_rot: float) -> void:
	card.set_meta("is_hovered", is_hovered)
	var tween: Tween = create_tween().set_parallel(true)
	if is_hovered:
		card.z_index = 100
		tween.tween_property(card, "position", base_pos + Vector2(0, hover_y_offset), 0.1).set_trans(Tween.TRANS_QUAD)
		tween.tween_property(card, "rotation", 0.0, 0.1).set_trans(Tween.TRANS_QUAD)
		tween.tween_property(card, "scale", Vector2(hover_scale, hover_scale), 0.1).set_trans(Tween.TRANS_QUAD)
	else:
		_layout_cards() # Re-trigger layout to restore everyone
