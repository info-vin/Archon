extends SceneTree

func _init() -> void:
	var theme = Theme.new()
	
	# Base Panel Style (Deep background with neon green border)
	var panel_style = StyleBoxFlat.new()
	panel_style.bg_color = Color("#0f172a") # Deep Slate
	panel_style.border_width_left = 2
	panel_style.border_width_top = 2
	panel_style.border_width_right = 2
	panel_style.border_width_bottom = 2
	panel_style.border_color = Color("#10B981") # Emerald Neon
	panel_style.corner_radius_top_left = 8
	panel_style.corner_radius_top_right = 8
	panel_style.corner_radius_bottom_right = 8
	panel_style.corner_radius_bottom_left = 8
	panel_style.shadow_color = Color(0.06, 0.72, 0.5, 0.2) # Emerald glow
	panel_style.shadow_size = 10
	
	theme.set_stylebox("panel", "PanelContainer", panel_style)
	
	# Button Style
	var btn_style = panel_style.duplicate() as StyleBoxFlat
	btn_style.bg_color = Color("#1e293b")
	btn_style.border_color = Color("#3b82f6") # Blue Neon
	theme.set_stylebox("normal", "Button", btn_style)
	
	var btn_hover = btn_style.duplicate() as StyleBoxFlat
	btn_hover.bg_color = Color("#334155")
	btn_hover.shadow_size = 15
	theme.set_stylebox("hover", "Button", btn_hover)
	
	var btn_pressed = btn_style.duplicate() as StyleBoxFlat
	btn_pressed.bg_color = Color("#0f172a")
	btn_pressed.shadow_size = 0
	theme.set_stylebox("pressed", "Button", btn_pressed)

	# Label Font overrides
	theme.set_color("font_color", "Label", Color("#f8fafc"))
	
	var res_path = "res://Scripts/Resources/NeonTheme.tres"
	var err = ResourceSaver.save(theme, res_path)
	if err == OK:
		print("Successfully generated Deep Neon Tech theme at: ", res_path)
		quit(0)
	else:
		push_error("Failed to save theme: ", err)
		quit(1)
