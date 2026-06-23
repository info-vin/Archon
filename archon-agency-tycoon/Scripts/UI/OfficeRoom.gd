extends Node2D
class_name OfficeRoom

var room_name: String
var neon_color: Color
var crisis_tween: Tween
var crisis_label: Label

func setup_room(p_name: String, p_color: Color, tycoon_manager) -> void:
	room_name = p_name
	neon_color = p_color
	set_meta("neon_color", p_color)
	
	var border_panel = Panel.new()
	border_panel.name = "NeonBorder"
	border_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	border_panel.size = Vector2(360, 390)
	
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.0, 0.0, 0.0, 0.0) # Transparent inside
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	
	style.border_color = neon_color * 1.5 # Overbright for neon glow
	style.corner_radius_top_left = 4
	style.corner_radius_top_right = 4
	style.corner_radius_bottom_right = 4
	style.corner_radius_bottom_left = 4
	
	border_panel.add_theme_stylebox_override("panel", style)
	add_child(border_panel)
	
	# Floating label for multi-stage crisis
	crisis_label = Label.new()
	crisis_label.name = "CrisisLabel"
	crisis_label.horizontal_alignment = HorizontalAlignment.HORIZONTAL_ALIGNMENT_CENTER
	crisis_label.vertical_alignment = VerticalAlignment.VERTICAL_ALIGNMENT_CENTER
	crisis_label.position = Vector2(0, -30)
	crisis_label.visible = false
	crisis_label.add_theme_color_override("font_color", Color(1, 0.2, 0.2)) # neon red text
	add_child(crisis_label)
	
	# Connect to TycoonManager signals for crisis flashing
	if tycoon_manager:
		if not tycoon_manager.crisis_spawned.is_connected(_on_crisis_spawned):
			tycoon_manager.crisis_spawned.connect(_on_crisis_spawned)
		if not tycoon_manager.crisis_resolved.is_connected(_on_crisis_resolved):
			tycoon_manager.crisis_resolved.connect(_on_crisis_resolved)
		if tycoon_manager.has_signal("crisis_stage_changed") and not tycoon_manager.crisis_stage_changed.is_connected(_on_crisis_stage_changed):
			tycoon_manager.crisis_stage_changed.connect(_on_crisis_stage_changed)

func _on_crisis_spawned(p_room_name: String) -> void:
	if p_room_name == room_name:
		if crisis_label:
			crisis_label.text = "NEED DEV"
			crisis_label.visible = true
		if not crisis_tween:
			crisis_tween = create_tween().set_loops()
			crisis_tween.tween_property(self, "modulate", Color(1, 0.4, 0.4), 0.5)
			crisis_tween.tween_property(self, "modulate", Color.WHITE, 0.5)

func _on_crisis_stage_changed(p_room_name: String, stage_name: String) -> void:
	if p_room_name == room_name and crisis_label:
		crisis_label.text = stage_name
		crisis_label.visible = true

func _on_crisis_resolved(p_room_name: String) -> void:
	if p_room_name == room_name:
		if crisis_label:
			crisis_label.visible = false
		if crisis_tween and crisis_tween.is_valid():
			crisis_tween.kill()
		crisis_tween = null
		modulate = Color.WHITE
