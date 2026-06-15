extends ColorRect
class_name DifficultyOverlay

signal difficulty_selected(diff: int)

func setup_overlay(cjk_font: Font) -> void:
	name = "DifficultyOverlay"
	color = Color(0, 0, 0, 0.8)
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	var center_container = CenterContainer.new()
	add_child(center_container)
	center_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	var v_box = VBoxContainer.new()
	v_box.alignment = BoxContainer.ALIGNMENT_CENTER
	v_box.add_theme_constant_override("separation", 20)
	center_container.add_child(v_box)
	
	var title = Label.new()
	title.text = "SELECT DIFFICULTY / 選擇難度"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 40)
	title.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	title.add_theme_font_override("font", cjk_font)
	v_box.add_child(title)
	
	var desc = Label.new()
	desc.text = "（難度將影響敵人的血量、每回合自動增加的護盾與隨時間成長的力量）"
	desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	desc.add_theme_font_size_override("font_size", 16)
	desc.add_theme_font_override("font", cjk_font)
	v_box.add_child(desc)
	
	var btn_easy = Button.new()
	btn_easy.text = "簡單 (Easy) - Target: <5 Turns"
	btn_easy.custom_minimum_size = Vector2(300, 50)
	btn_easy.pressed.connect(func(): _select(0))
	btn_easy.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_easy)
	
	var btn_normal = Button.new()
	btn_normal.text = "普通 (Normal) - Target: ~8 Turns"
	btn_normal.custom_minimum_size = Vector2(300, 50)
	btn_normal.pressed.connect(func(): _select(1))
	btn_normal.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_normal)
	
	var btn_hard = Button.new()
	btn_hard.text = "困難 (Hard) - Target: 20-50 Turns"
	btn_hard.custom_minimum_size = Vector2(300, 50)
	btn_hard.pressed.connect(func(): _select(2))
	btn_hard.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_hard)
	
	var btn_expert = Button.new()
	btn_expert.text = "超難 (Expert) - Target: 50+ Turns"
	btn_expert.custom_minimum_size = Vector2(300, 50)
	btn_expert.pressed.connect(func(): _select(3))
	btn_expert.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_expert)

func _select(diff: int) -> void:
	emit_signal("difficulty_selected", diff)
	queue_free()
