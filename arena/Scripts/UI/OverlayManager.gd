class_name OverlayManager
extends RefCounted

static func show_help_overlay(ui_node: Node, cjk_font: Font) -> Control:
	var HelpOverlayScript = load("res://Scripts/UI/HelpOverlay.gd")
	var help_overlay = HelpOverlayScript.new()
	help_overlay.setup_overlay(cjk_font)
	ui_node.get_node("UILayer/UIRoot").add_child(help_overlay)
	return help_overlay

static func hide_help_overlay(help_overlay: Control) -> void:
	if help_overlay != null:
		if help_overlay.has_method("close"):
			help_overlay.close()
		else:
			help_overlay.queue_free()

static func show_difficulty_selection(ui_node: Node, cjk_font: Font, diff_callback: Callable) -> void:
	var DifficultyOverlayScript = load("res://Scripts/UI/DifficultyOverlay.gd")
	var overlay = DifficultyOverlayScript.new()
	overlay.setup_overlay(cjk_font)
	overlay.difficulty_selected.connect(diff_callback)
	ui_node.get_node("UILayer/UIRoot").add_child(overlay)
