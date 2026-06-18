extends ColorRect
class_name HelpOverlay

signal closed()

func setup_overlay(cjk_font: Font) -> void:
	name = "HelpOverlay"
	color = Color(0, 0, 0, 0.9)
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	var center_container = CenterContainer.new()
	add_child(center_container)
	center_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	var v_box = VBoxContainer.new()
	v_box.alignment = BoxContainer.ALIGNMENT_CENTER
	v_box.add_theme_constant_override("separation", 15)
	center_container.add_child(v_box)
	
	var title = Label.new()
	title.text = "遊戲說明 (GAME MANUAL)"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 28)
	title.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	title.add_theme_font_override("font", cjk_font)
	v_box.add_child(title)
	
	var rules = Label.new()
	rules.text = "【核心規則】\n" + \
		"1. 玩家為 Tech Lead [TECH LEAD]，敵人為專案技術債 Bug。\n" + \
		"2. 卡牌來自真實 Git commit，依照變更行數決定 Token 花費、攻擊與防禦。\n" + \
		"3. 每次出牌會累積 COMBO，傷害會以乘數放大！\n" + \
		"4. 重構自癒：打出 [重構] 卡牌時，可額外獲得傷害值 50% 的防禦護盾。\n" + \
		"5. 回合時間：每回合有 30 秒限制，或當 Token 消耗完時會自動結束回合。\n\n" + \
		"【快捷鍵說明】\n" + \
		"• [H] 鍵：開啟此遊戲說明\n" + \
		"• [ESC] 鍵：關閉遊戲說明\n" + \
		"• [Space / Enter] 鍵：結束玩家回合"
	rules.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	rules.add_theme_font_size_override("font_size", 16)
	rules.add_theme_font_override("font", cjk_font)
	v_box.add_child(rules)
	
	var close_btn = Button.new()
	close_btn.text = "關閉說明 (ESC)"
	close_btn.custom_minimum_size = Vector2(200, 40)
	close_btn.pressed.connect(close)
	close_btn.add_theme_font_override("font", cjk_font)
	v_box.add_child(close_btn)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			close()

func close() -> void:
	emit_signal("closed")
	queue_free()
