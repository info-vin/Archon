class_name GameOverHelper
extends RefCounted

static func show(ui_node: Node, overlay: Control, result_label: Label, restart_button: Button, win: bool) -> void:
	overlay.visible = true
	var vbox = overlay.get_node("VBox")
	vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	vbox.offset_left = 0
	vbox.offset_right = 0
	vbox.offset_top = 0
	vbox.offset_bottom = 0
	vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	
	result_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	result_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	result_label.add_theme_font_size_override("font_size", 48)
	
	restart_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	
	if win:
		result_label.text = "[SUCCESS] DEPLOYMENT SUCCESS!"
		result_label.add_theme_color_override("font_color", Color(0.2, 1, 0.4))
	else:
		result_label.text = "[CRASH] SYSTEM CRASH"
		result_label.add_theme_color_override("font_color", Color(1, 0.2, 0.2))
