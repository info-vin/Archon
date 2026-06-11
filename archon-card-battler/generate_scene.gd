@tool
extends SceneTree

func _init():
	var root = Node2D.new()
	root.name = "Main"
	root.set_script(load("res://Scripts/UI/MainUI.gd"))
	
	# Background
	var bg = TextureRect.new()
	bg.name = "Background"
	if ResourceLoader.exists("res://Assets/Background/landscape.jpg"):
		bg.texture = load("res://Assets/Background/landscape.jpg")
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg.position = Vector2(0, 0)
	bg.size = Vector2(1152, 648)
	root.add_child(bg)
	bg.owner = root
	
	# Dim
	var dim = ColorRect.new()
	dim.name = "DimOverlay"
	dim.color = Color(0, 0, 0, 0.6)
	dim.position = Vector2(0, 0)
	dim.size = Vector2(1152, 648)
	root.add_child(dim)
	dim.owner = root
	
	var cam = Camera2D.new()
	cam.name = "Camera2D"
	cam.position = Vector2(576, 324) 
	root.add_child(cam)
	cam.owner = root
	
	var ui_layer = CanvasLayer.new()
	ui_layer.name = "UILayer"
	root.add_child(ui_layer)
	ui_layer.owner = root
	
	var ui_root = Control.new()
	ui_root.name = "UIRoot"
	ui_root.position = Vector2(0, 0)
	ui_root.size = Vector2(1152, 648)
	ui_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_layer.add_child(ui_root)
	ui_root.owner = root
	
	# 1. Player HUD (Top Left)
	var player_hud = VBoxContainer.new()
	player_hud.name = "PlayerHUD"
	player_hud.position = Vector2(20, 20)
	player_hud.size = Vector2(350, 100)
	ui_root.add_child(player_hud)
	player_hud.owner = root
	
	var p_name = Label.new()
	p_name.name = "PlayerName"
	p_name.text = "👨‍💻 TECH LEAD"
	p_name.add_theme_font_size_override("font_size", 36)
	p_name.add_theme_color_override("font_color", Color(0.4, 0.8, 1))
	player_hud.add_child(p_name)
	p_name.owner = root
	
	var player_hp = ProgressBar.new()
	player_hp.name = "PlayerHP"
	player_hp.custom_minimum_size = Vector2(0, 30)
	player_hp.max_value = 50
	player_hp.value = 50
	player_hp.modulate = Color(0.2, 0.8, 0.2)
	player_hud.add_child(player_hp)
	player_hp.owner = root
	
	var mana_label = Label.new()
	mana_label.name = "ManaLabel"
	mana_label.text = "💎 Tokens: 3 | 🛡️ Block: 0 | 🎴 Deck: 10"
	mana_label.add_theme_font_size_override("font_size", 20)
	player_hud.add_child(mana_label)
	mana_label.owner = root
	
	# 2. Enemy HUD (Top Right)
	var enemy_hud = VBoxContainer.new()
	enemy_hud.name = "EnemyHUD"
	enemy_hud.position = Vector2(1152 - 350 - 20, 20) # 782, 20
	enemy_hud.size = Vector2(350, 100)
	ui_root.add_child(enemy_hud)
	enemy_hud.owner = root
	
	var e_name = Label.new()
	e_name.name = "EnemyName"
	e_name.text = "👾 TECH DEBT"
	e_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	e_name.add_theme_font_size_override("font_size", 36)
	e_name.add_theme_color_override("font_color", Color(1, 0.4, 0.4))
	enemy_hud.add_child(e_name)
	e_name.owner = root
	
	var enemy_hp = ProgressBar.new()
	enemy_hp.name = "EnemyHP"
	enemy_hp.custom_minimum_size = Vector2(0, 30)
	enemy_hp.max_value = 200
	enemy_hp.value = 200
	enemy_hp.fill_mode = ProgressBar.FILL_END_TO_BEGIN
	enemy_hp.modulate = Color(1, 0.2, 0.2)
	enemy_hud.add_child(enemy_hp)
	enemy_hp.owner = root
	
	var enemy_intent = Label.new()
	enemy_intent.name = "EnemyIntent"
	enemy_intent.text = "Intent: ⚔️ 15 DMG"
	enemy_intent.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	enemy_intent.add_theme_font_size_override("font_size", 20)
	enemy_hud.add_child(enemy_intent)
	enemy_intent.owner = root
	
	# 3. Fighters (GIANT Avatars)
	var fighter_left = Label.new()
	fighter_left.name = "FighterLeft"
	fighter_left.text = "🥷"
	fighter_left.add_theme_font_size_override("font_size", 250)
	fighter_left.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	fighter_left.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	fighter_left.position = Vector2(80, 120)
	fighter_left.size = Vector2(300, 300)
	ui_root.add_child(fighter_left)
	fighter_left.owner = root
	
	var fighter_right = Label.new()
	fighter_right.name = "FighterRight"
	fighter_right.text = "🐛"
	fighter_right.add_theme_font_size_override("font_size", 250)
	fighter_right.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	fighter_right.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	fighter_right.position = Vector2(1152 - 380, 120)
	fighter_right.size = Vector2(300, 300)
	ui_root.add_child(fighter_right)
	fighter_right.owner = root
	
	# 4. Combo Counter
	var combo_label = Label.new()
	combo_label.name = "ComboLabel"
	combo_label.text = ""
	combo_label.add_theme_font_size_override("font_size", 72)
	combo_label.add_theme_color_override("font_color", Color(1, 0.8, 0))
	combo_label.add_theme_color_override("font_shadow_color", Color(1, 0, 0))
	combo_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	combo_label.position = Vector2(376, 200)
	combo_label.size = Vector2(400, 100)
	ui_root.add_child(combo_label)
	combo_label.owner = root
	
	# 5. Hand Area (Bottom Center)
	var hand_area = Control.new()
	hand_area.name = "HandArea"
	hand_area.position = Vector2(250, 360) # Moved up significantly (648 - 288)
	hand_area.size = Vector2(652, 288)
	hand_area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(hand_area)
	hand_area.owner = root
	
	# 6. Action Log (Bottom Left)
	var log_panel = PanelContainer.new()
	log_panel.name = "LogArea"
	log_panel.position = Vector2(20, 420) 
	log_panel.size = Vector2(220, 208)
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0,0,0, 0.7)
	log_panel.add_theme_stylebox_override("panel", style)
	ui_root.add_child(log_panel)
	log_panel.owner = root
	
	var action_log = RichTextLabel.new()
	action_log.name = "ActionLog"
	action_log.bbcode_enabled = true
	action_log.scroll_following = true
	action_log.text = "[b]Combat Log[/b]\n"
	log_panel.add_child(action_log)
	action_log.owner = root
	
	# 7. End Turn (Bottom Right)
	var end_turn = Button.new()
	end_turn.name = "EndTurnButton"
	end_turn.text = "END TURN"
	end_turn.position = Vector2(922, 548) # 1152 - 210 - 20
	end_turn.size = Vector2(210, 80)
	end_turn.add_theme_font_size_override("font_size", 28)
	var btn_style = StyleBoxFlat.new()
	btn_style.bg_color = Color(0.8, 0.2, 0.2, 1)
	end_turn.add_theme_stylebox_override("normal", btn_style)
	ui_root.add_child(end_turn)
	end_turn.owner = root
	
	# 8. Game Over Overlay
	var top_layer = CanvasLayer.new()
	top_layer.name = "TopLayer"
	top_layer.layer = 10
	root.add_child(top_layer)
	top_layer.owner = root
	
	var overlay = ColorRect.new()
	overlay.name = "GameOverOverlay"
	overlay.color = Color(0,0,0, 0.8)
	overlay.position = Vector2(0, 0)
	overlay.size = Vector2(1152, 648)
	overlay.visible = false
	top_layer.add_child(overlay)
	overlay.owner = root
	
	var ovbox = VBoxContainer.new()
	ovbox.name = "VBox"
	ovbox.position = Vector2(376, 224) 
	ovbox.size = Vector2(400, 200)
	overlay.add_child(ovbox)
	ovbox.owner = root
	
	var result_label = Label.new()
	result_label.name = "ResultLabel"
	result_label.text = "VICTORY"
	result_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	result_label.add_theme_font_size_override("font_size", 64)
	ovbox.add_child(result_label)
	result_label.owner = root
	
	var restart_btn = Button.new()
	restart_btn.name = "RestartButton"
	restart_btn.text = "New Deployment (Restart)"
	restart_btn.custom_minimum_size = Vector2(400, 80)
	restart_btn.add_theme_font_size_override("font_size", 32)
	ovbox.add_child(restart_btn)
	restart_btn.owner = root
	
	var packed_scene = PackedScene.new()
	packed_scene.pack(root)
	ResourceSaver.save(packed_scene, "res://Scenes/Main/Main.tscn")
	
	print("Scene generated successfully with absolute anchors!")
	quit()
