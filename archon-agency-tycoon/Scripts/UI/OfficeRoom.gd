extends PanelContainer
class_name OfficeRoom

var room_name: String
var neon_color: Color
var crisis_tween: Tween

func setup_room(p_name: String, p_color: Color, tycoon_manager) -> void:
	room_name = p_name
	neon_color = p_color
	set_meta("neon_color", p_color)
	
	# Apply stylebox
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.0, 0.0, 0.0, 0.5)
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.expand_margin_left = -2
	style.expand_margin_top = -2
	style.expand_margin_right = -2
	style.expand_margin_bottom = -2
	style.border_color = neon_color * 1.5 # Overbright for neon glow
	style.corner_radius_top_left = 4
	style.corner_radius_top_right = 4
	style.corner_radius_bottom_right = 4
	style.corner_radius_bottom_left = 4
	add_theme_stylebox_override("panel", style)
	
	# Connect to TycoonManager signals for crisis flashing
	if tycoon_manager:
		if not tycoon_manager.crisis_spawned.is_connected(_on_crisis_spawned):
			tycoon_manager.crisis_spawned.connect(_on_crisis_spawned)
		if not tycoon_manager.crisis_resolved.is_connected(_on_crisis_resolved):
			tycoon_manager.crisis_resolved.connect(_on_crisis_resolved)

func _on_crisis_spawned(p_room_name: String) -> void:
	if p_room_name == room_name and not crisis_tween:
		crisis_tween = create_tween().set_loops()
		crisis_tween.tween_property(self, "modulate", Color(1, 0.4, 0.4), 0.5)
		crisis_tween.tween_property(self, "modulate", Color.WHITE, 0.5)

func _on_crisis_resolved(p_room_name: String) -> void:
	if p_room_name == room_name:
		if crisis_tween and crisis_tween.is_valid():
			crisis_tween.kill()
		crisis_tween = null
		modulate = Color.WHITE
