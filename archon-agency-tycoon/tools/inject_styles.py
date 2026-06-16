import os

gd_path = 'archon-agency-tycoon/Scripts/Main.gd'

with open(gd_path, 'r') as f:
    gd = f.read()

style_func = """
func _setup_room_styles() -> void:
	var rooms = [
		{"node": dev_room, "label": dev_room_label, "color": Color("#39ff14")},
		{"node": sales_room, "label": sales_room_label, "color": Color("#fde910")},
		{"node": qa_room, "label": qa_room_label, "color": Color("#ff003c")},
		{"node": break_room, "label": break_room_label, "color": Color("#b026ff")}
	]
	
	for data in rooms:
		if data["node"] == null: continue
		var panel: PanelContainer = data["node"]
		var label: Label = data["label"]
		var c: Color = data["color"]
		
		# Colorize the label font
		label.add_theme_color_override("font_color", c)
		
		# Colorize the panel border
		var style = StyleBoxFlat.new()
		style.bg_color = Color(0.0, 0.0, 0.0, 0.5)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = c * 1.5 # Overbright for neon glow
		style.corner_radius_top_left = 4
		style.corner_radius_top_right = 4
		style.corner_radius_bottom_right = 4
		style.corner_radius_bottom_left = 4
		
		panel.add_theme_stylebox_override("panel", style)

func _on_lang_button_pressed() -> void:"""

gd = gd.replace("func _on_lang_button_pressed() -> void:", style_func)

ready_hook = """	_update_static_labels()
	_setup_room_styles()"""

gd = gd.replace("\t_update_static_labels()", ready_hook)

with open(gd_path, 'w') as f:
    f.write(gd)

print("✅ Room styles injected!")
