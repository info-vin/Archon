extends Control

signal request_return_menu

@export var badge_rank_c: Texture2D
@export var badge_rank_b: Texture2D
@export var badge_rank_a: Texture2D
@export var badge_rank_s: Texture2D

@export var bg_texture: TextureRect
@export var avatar_rect: TextureRect
@export var badge_rect: TextureRect
@export var rank_label: Label
@export var xp_bar: ProgressBar

# Topology Web
@export var topology_panel: Control
@export var lines_container: Node2D
@export var nodes_container: Control
@export var terminal_lore: RichTextLabel
@export var back_button: TextureButton

@export var player_card: TextureRect
@export var terminal_panel: TextureRect

var _controller: Node

var tab_container: TabContainer
var card_manage_scene = "res://src/views/CardManagementMenu.tscn"
var card_workshop_scene = "res://src/views/CardWorkshop.tscn"
var teammate_scene = "res://src/views/TeammateDashboard.tscn"

var tab_frame_tex = preload("res://assets/images/card_frame_blank.png")

func _ready() -> void:
	# 1. Create TabContainer
	tab_container = TabContainer.new()
	tab_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	tab_container.offset_top = 30.0 # leave room for back button
	
	# Tab separation
	tab_container.add_theme_constant_override("h_separation", 15)
	
	# Create Tech StyleBox for Tabs using Texture
	var tab_bg = StyleBoxTexture.new()
	tab_bg.texture = tab_frame_tex
	tab_bg.texture_margin_left = 10
	tab_bg.texture_margin_right = 10
	tab_bg.texture_margin_top = 10
	tab_bg.texture_margin_bottom = 5
	tab_bg.content_margin_left = 45
	tab_bg.content_margin_right = 45
	tab_bg.content_margin_top = 15
	tab_bg.content_margin_bottom = 10
	tab_bg.modulate_color = Color(0.4, 0.6, 0.6, 0.9) # Dimmed when unselected
	
	var tab_selected = StyleBoxTexture.new()
	tab_selected.texture = tab_frame_tex
	tab_selected.texture_margin_left = 10
	tab_selected.texture_margin_right = 10
	tab_selected.texture_margin_top = 10
	tab_selected.texture_margin_bottom = 5
	tab_selected.content_margin_left = 45
	tab_selected.content_margin_right = 45
	tab_selected.content_margin_top = 15
	tab_selected.content_margin_bottom = 10
	tab_selected.modulate_color = Color(1.2, 1.2, 1.2, 1.0) # Bright when selected
	
	var panel_bg = StyleBoxFlat.new()
	panel_bg.bg_color = Color(0.0, 0.0, 0.0, 0.0)
	
	tab_container.add_theme_stylebox_override("tab_unselected", tab_bg)
	tab_container.add_theme_stylebox_override("tab_selected", tab_selected)
	tab_container.add_theme_stylebox_override("panel", panel_bg)
	tab_container.add_theme_color_override("font_selected_color", Color(0.2, 1.0, 0.8))
	tab_container.add_theme_color_override("font_unselected_color", Color(0.5, 0.7, 0.7))
	tab_container.add_theme_font_size_override("font_size", 24)
	
	add_child(tab_container)
	
	# 2. Move current UI to Tab 1
	var hbox = $HBoxContainer
	remove_child(hbox)
	var tab1 = MarginContainer.new()
	tab1.name = "ProfileTab"
	tab1.add_theme_constant_override("margin_left", 20)
	tab1.add_theme_constant_override("margin_top", 20)
	tab1.add_theme_constant_override("margin_right", 20)
	tab1.add_theme_constant_override("margin_bottom", 20)
	tab1.add_child(hbox)
	tab_container.add_child(tab1)
	tab_container.set_tab_title(0, "駭客檔案")
	
	# 3. Inject Card Management
	var tab2 = MarginContainer.new()
	tab2.name = "DeckTab"
	var deck = load(card_manage_scene).instantiate()
	if deck.has_node("NavBox"): deck.get_node("NavBox").hide()
	if deck.has_node("ColorRect"): deck.get_node("ColorRect").hide()
	tab2.add_child(deck)
	tab_container.add_child(tab2)
	tab_container.set_tab_title(1, "核心武裝")
	
	# 4. Inject Workshop
	var tab3 = MarginContainer.new()
	tab3.name = "WorkshopTab"
	var workshop = load(card_workshop_scene).instantiate()
	if workshop.has_node("ReturnButton"): workshop.get_node("ReturnButton").hide()
	if workshop.has_node("Background"): workshop.get_node("Background").hide()
	if workshop.has_node("ColorRect"): workshop.get_node("ColorRect").hide()
	tab3.add_child(workshop)
	tab_container.add_child(tab3)
	tab_container.set_tab_title(2, "卡牌工坊")
	
	# 5. Inject Teammates
	var tab4 = MarginContainer.new()
	tab4.name = "TeammateTab"
	var teammate = load(teammate_scene).instantiate()
	if teammate.has_node("MarginContainer/VBoxContainer/NavHBox"): 
		teammate.get_node("MarginContainer/VBoxContainer/NavHBox").hide()
	tab4.add_child(teammate)
	tab_container.add_child(tab4)
	tab_container.set_tab_title(3, "特務編制")
	
	# 6. Ensure BackButton stays on top
	if back_button:
		remove_child(back_button)
		add_child(back_button)
	
	setup_topology_web()
	
	if back_button:
		back_button.pressed.connect(func(): request_return_menu.emit())

func update_profile(sector: int, account_xp: int) -> void:
	# Determine badge and avatar tint
	var badge_tex: Texture2D = badge_rank_c
	var avatar_tint = Color(1.0, 1.0, 1.0) # Fully bright character
	var rank_text = "權限階級：C級節點行者"
	
	if sector == 2:
		badge_tex = badge_rank_b
		avatar_tint = Color(1.0, 1.0, 1.0)
		rank_text = "權限階級：B級網路行者"
	elif sector == 3:
		badge_tex = badge_rank_a
		avatar_tint = Color(1.0, 1.0, 1.0)
		rank_text = "權限階級：A級菁英駭客"
	elif sector >= 4:
		badge_tex = badge_rank_s
		avatar_tint = Color(1.0, 1.0, 1.0)
		rank_text = "權限階級：S級系統管理員"
		
	if badge_tex and badge_rect:
		badge_rect.texture = badge_tex
		badge_rect.modulate = Color(1.2, 1.2, 1.2, 1.0) # Brighten badge
		
	if avatar_rect:
		avatar_rect.modulate = avatar_tint
	if rank_label:
		rank_label.text = rank_text
	if xp_bar:
		xp_bar.value = account_xp

var _typewriter_tween: Tween

func _print_to_terminal(text: String) -> void:
	if not terminal_lore: return
	terminal_lore.visible_characters = 0
	terminal_lore.text = text
	
	if _typewriter_tween:
		_typewriter_tween.kill()
	_typewriter_tween = create_tween()
	var duration = text.length() * 0.02 # Faster typing
	_typewriter_tween.tween_property(terminal_lore, "visible_ratio", 1.0, duration)
	
	# Glitch effect on terminal
	var glitch_tween = create_tween()
	for i in range(3):
		glitch_tween.tween_property(terminal_lore, "modulate", Color(randf_range(0.8, 1.2), randf_range(0.8, 1.2), randf_range(0.8, 1.2), 1.0), 0.05)
	glitch_tween.tween_property(terminal_lore, "modulate", Color.WHITE, 0.05)

func setup_topology_web() -> void:
	for c in lines_container.get_children(): c.queue_free()
	for c in nodes_container.get_children(): c.queue_free()
	
	var node_icon_green = preload("res://assets/images/chip_green_target.png")
	var node_icon_red = preload("res://assets/images/chip_red_noise.png")
	
	# Phase 5.8.6 - Exactly 3 Parameters
	var implant_names = ["暴力檢索", "純粹主義", "混合工程師"]
	var implant_effects = ["召回數量 (match_count) +3", "相似度閥值 (min_score) +0.1", "解鎖混合檢索 (use_hybrid = true)"]
	var implant_lore = [
		"注入極端暴力的資料爬蟲協定。忽視系統負載，強行從深網中撈出更多可能相關的碎片資訊。適合需要高召回率的駭客。",
		"嚴格的語義過濾器。大幅提高判定閥值，過濾掉所有模糊不清的干擾雜訊。確保每一筆回傳資料都極度精確。",
		"將傳統關鍵字與向量語義深度融合的高階神經協定。全面提升檢索的靈活性，應對複雜的複合型威脅。"
	]
	
	var center = Vector2(380, 260)
	var radius_x = 260
	var radius_y = 200
	
	# 3 Nodes around the card
	var positions = [
		Vector2(-radius_x, -radius_y * 0.2), # Left
		Vector2(radius_x, -radius_y * 0.5),  # Top Right
		Vector2(radius_x * 1.1, radius_y * 0.5) # Bottom Right
	]
	
	# Draw ComfyUI style Bezier curves with neon gradient
	for pos in positions:
		var line = Line2D.new()
		var start = center
		var end = center + pos
		
		var dist = abs(end.x - start.x) * 0.6
		var p1 = start + Vector2(dist, 0) if end.y > start.y + 100 else start + Vector2(0, dist*0.5)
		var p2 = end - Vector2(dist, 0) if end.y > start.y + 100 else end - Vector2(0, dist*0.5)
		
		if abs(end.y - start.y) > abs(end.x - start.x):
			dist = abs(end.y - start.y) * 0.5
			p1 = start + Vector2(0, dist)
			p2 = end - Vector2(0, dist)
		else:
			p1 = start + Vector2(dist * sign(end.x - start.x), 0)
			p2 = end - Vector2(dist * sign(end.x - start.x), 0)
			
		var curve = Curve2D.new()
		curve.add_point(start, Vector2.ZERO, p1 - start)
		curve.add_point(end, p2 - end, Vector2.ZERO)
		
		line.points = curve.get_baked_points()
		line.width = 2
		
		# Directional Neon Gradient
		var grad = Gradient.new()
		grad.add_point(0.0, Color(0.0, 1.0, 0.7, 0.0)) # Transparent at card
		grad.add_point(1.0, Color(0.0, 1.0, 0.7, 1.0)) # Bright at node
		line.gradient = grad
		
		line.antialiased = true
		
		var mat = CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		line.material = mat
		lines_container.add_child(line)
		
	for i in range(positions.size()):
		var pos = center + positions[i]
		
		var btn = TextureButton.new()
		btn.texture_normal = node_icon_green if i == 0 else node_icon_red
		btn.ignore_texture_size = true
		btn.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		btn.custom_minimum_size = Vector2(64, 64)
		btn.position = pos - Vector2(32, 32)
		btn.pivot_offset = Vector2(32, 32)
		
		var lore_text = "【%s】\n\n[ 系統竄改 ]\n%s\n\n[ 檔案描述 ]\n%s" % [implant_names[i], implant_effects[i], implant_lore[i]]
		btn.pressed.connect(_on_node_pressed.bind(i, btn, lore_text))
		btn.mouse_entered.connect(_on_node_hovered.bind(btn, true))
		btn.mouse_exited.connect(_on_node_hovered.bind(btn, false))
		
		nodes_container.add_child(btn)
		
	_print_to_terminal("系統就緒... 等待神經網路節點連線。")

func _on_node_hovered(btn: TextureButton, is_hovered: bool) -> void:
	var tween = create_tween()
	if is_hovered:
		tween.tween_property(btn, "scale", Vector2(1.2, 1.2), 0.1)
		tween.parallel().tween_property(btn, "modulate", Color(1.5, 1.5, 1.5, 1.0), 0.1)
	else:
		tween.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.1)
		tween.parallel().tween_property(btn, "modulate", Color.WHITE, 0.1)

func _on_node_pressed(node_idx: int, btn: TextureButton, lore_text: String) -> void:
	var tween = create_tween()
	tween.tween_property(btn, "scale", Vector2(1.5, 1.5), 0.05)
	tween.parallel().tween_property(btn, "modulate", Color(3.0, 3.0, 3.0, 1.0), 0.05)
	tween.tween_property(btn, "scale", Vector2(1.2, 1.2), 0.3).set_trans(Tween.TRANS_BOUNCE)
	tween.parallel().tween_property(btn, "modulate", Color(1.5, 1.5, 1.5, 1.0), 0.3)
	
	_print_to_terminal(lore_text)

# For automated screenshots to trigger text display
func debug_trigger_node(idx: int) -> void:
	if nodes_container.get_child_count() > idx:
		var btn = nodes_container.get_child(idx) as TextureButton
		if btn:
			btn.pressed.emit()
