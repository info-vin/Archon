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
@export var back_button: Button

var line_shader = preload("res://src/shaders/DataFlowLine.gdshader")
var _controller: Node

var tab_container: TabContainer
var card_manage_scene = preload("res://src/views/CardManagementMenu.tscn")
var card_workshop_scene = preload("res://src/views/CardWorkshop.tscn")
var teammate_scene = preload("res://src/views/TeammateDashboard.tscn")

func _ready() -> void:
	# 1. Create TabContainer
	tab_container = TabContainer.new()
	tab_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	tab_container.offset_top = 40.0 # leave room for back button
	add_child(tab_container)
	
	# 2. Move current UI to Tab 1
	var hbox = $HBoxContainer
	remove_child(hbox)
	var tab1 = MarginContainer.new()
	tab1.name = "Profile & Relics"
	tab1.add_theme_constant_override("margin_left", 20)
	tab1.add_theme_constant_override("margin_top", 20)
	tab1.add_theme_constant_override("margin_right", 20)
	tab1.add_theme_constant_override("margin_bottom", 20)
	tab1.add_child(hbox)
	tab_container.add_child(tab1)
	
	# 3. Inject Card Management
	var tab2 = MarginContainer.new()
	tab2.name = "Deck Management"
	var deck = card_manage_scene.instantiate()
	if deck.has_node("NavBox"): deck.get_node("NavBox").hide()
	if deck.has_node("ColorRect"): deck.get_node("ColorRect").hide()
	tab2.add_child(deck)
	tab_container.add_child(tab2)
	
	# 4. Inject Workshop
	var tab3 = MarginContainer.new()
	tab3.name = "Card Workshop"
	var workshop = card_workshop_scene.instantiate()
	if workshop.has_node("BackButton"): workshop.get_node("BackButton").hide()
	if workshop.has_node("Background"): workshop.get_node("Background").hide()
	tab3.add_child(workshop)
	tab_container.add_child(tab3)
	
	# 5. Inject Teammates
	var tab4 = MarginContainer.new()
	tab4.name = "Teammates"
	var teammate = teammate_scene.instantiate()
	if teammate.has_node("BackButton"): teammate.get_node("BackButton").hide()
	if teammate.has_node("ColorRect"): teammate.get_node("ColorRect").hide()
	tab4.add_child(teammate)
	tab_container.add_child(tab4)
	
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
	var avatar_tint = Color(0.6, 0.6, 0.6) # C rank gray
	var rank_text = "Rank C: Script Kiddie"
	
	if sector == 2:
		badge_tex = badge_rank_b
		avatar_tint = Color(0.2, 0.8, 0.2) # B rank green
		rank_text = "Rank B: Node Runner"
	elif sector == 3:
		badge_tex = badge_rank_a
		avatar_tint = Color(0.2, 0.5, 1.0) # A rank blue
		rank_text = "Rank A: Elite Netrunner"
	elif sector >= 4:
		badge_tex = badge_rank_s
		avatar_tint = Color(1.0, 0.8, 0.2) # S rank gold
		rank_text = "Rank S: Archon Admin"
		
	if badge_tex:
		badge_rect.texture = badge_tex
		
	avatar_rect.modulate = avatar_tint
	rank_label.text = rank_text
	xp_bar.value = account_xp

func setup_topology_web() -> void:
	# Convert topology into a Relics Grid
	for c in lines_container.get_children(): c.queue_free()
	for c in nodes_container.get_children(): c.queue_free()
	
	var grid = GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 20)
	grid.add_theme_constant_override("v_separation", 20)
	grid.set_anchors_preset(Control.PRESET_CENTER)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	nodes_container.add_child(grid)
	
	var node_icon = preload("res://assets/images/chip_green_target.png")
	var slot_bg = preload("res://assets/images/icon_equipment_slot.png")
	
	for i in range(8):
		var slot = TextureRect.new()
		slot.texture = slot_bg
		slot.custom_minimum_size = Vector2(80, 80)
		slot.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		
		# Only first 4 have relics
		if i < 4:
			var btn = TextureButton.new()
			btn.texture_normal = node_icon
			btn.ignore_texture_size = true
			btn.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
			btn.custom_minimum_size = Vector2(64, 64)
			btn.set_anchors_preset(Control.PRESET_CENTER)
			btn.pivot_offset = Vector2(32, 32)
			btn.tooltip_text = "【Relic %d】: Boosts stats by %d%%" % [i, (i+1)*10]
			btn.pressed.connect(_on_node_pressed.bind(i, btn))
			btn.mouse_entered.connect(_on_node_hovered.bind(btn, true))
			btn.mouse_exited.connect(_on_node_hovered.bind(btn, false))
			slot.add_child(btn)
			
		grid.add_child(slot)

func _on_node_hovered(btn: TextureButton, is_hovered: bool) -> void:
	var tween = create_tween()
	if is_hovered:
		tween.tween_property(btn, "scale", Vector2(1.2, 1.2), 0.1)
		tween.parallel().tween_property(btn, "modulate", Color(1.5, 1.5, 1.5, 1.0), 0.1)
	else:
		tween.tween_property(btn, "scale", Vector2(1.0, 1.0), 0.1)
		tween.parallel().tween_property(btn, "modulate", Color.WHITE, 0.1)

func _on_node_pressed(node_idx: int, btn: TextureButton) -> void:
	print("Relic %d clicked! Emitting pulse..." % node_idx)
	var tween = create_tween()
	tween.tween_property(btn, "scale", Vector2(1.5, 1.5), 0.05)
	tween.parallel().tween_property(btn, "modulate", Color(3.0, 3.0, 3.0, 1.0), 0.05) # Extreme HDR Glow
	tween.tween_property(btn, "scale", Vector2(1.2, 1.2), 0.3).set_trans(Tween.TRANS_BOUNCE)
	tween.parallel().tween_property(btn, "modulate", Color(1.5, 1.5, 1.5, 1.0), 0.3)
