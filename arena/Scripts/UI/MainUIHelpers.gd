class_name MainUIHelpers
extends RefCounted

static func create_sound(parent: Node, stream_path: String) -> AudioStreamPlayer:
	var player = AudioStreamPlayer.new()
	player.stream = load(stream_path)
	parent.add_child(player)
	return player

static func create_avatar(parent: Node, texture_path: String, pos: Vector2) -> TextureRect:
	var avatar = TextureRect.new()
	avatar.custom_minimum_size = Vector2(216, 324)
	avatar.size = Vector2(216, 324)
	avatar.position = pos
	avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if texture_path != "":
		avatar.texture = load(texture_path)
	parent.add_child(avatar)
	parent.move_child(avatar, 0)
	return avatar

static func create_hp_text(hp_bar: ProgressBar, cjk_font: Font) -> Label:
	hp_bar.show_percentage = false
	var lbl = Label.new()
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.add_theme_font_override("font", cjk_font)
	lbl.add_theme_font_size_override("font_size", 16)
	lbl.add_theme_color_override("font_color", Color(1, 1, 1))
	hp_bar.add_child(lbl)
	lbl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	return lbl

static func update_hp_bar(ui_node: Node, hp_bar: ProgressBar, label: Label, current_hp: int, max_hp: int) -> void:
	hp_bar.max_value = float(max_hp)
	var tween = ui_node.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(hp_bar, "value", float(current_hp), 0.3)
	if label:
		label.text = "%d / %d HP" % [current_hp, max_hp]
