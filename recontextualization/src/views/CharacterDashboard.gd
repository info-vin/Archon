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
	tab1.name = "ProfileTab"
	tab1.add_theme_constant_override("margin_left", 20)
	tab1.add_theme_constant_override("margin_top", 20)
	tab1.add_theme_constant_override("margin_right", 20)
	tab1.add_theme_constant_override("margin_bottom", 20)
	tab1.add_child(hbox)
	tab_container.add_child(tab1)
	tab_container.set_tab_title(0, tr("tab_profile_relics"))
	
	# 3. Inject Card Management
	var tab2 = MarginContainer.new()
	tab2.name = "DeckTab"
	var deck = card_manage_scene.instantiate()
	if deck.has_node("NavBox"): deck.get_node("NavBox").hide()
	if deck.has_node("ColorRect"): deck.get_node("ColorRect").hide()
	tab2.add_child(deck)
	tab_container.add_child(tab2)
	tab_container.set_tab_title(1, tr("tab_deck_management"))
	
	# 4. Inject Workshop
	var tab3 = MarginContainer.new()
	tab3.name = "WorkshopTab"
	var workshop = card_workshop_scene.instantiate()
	if workshop.has_node("ReturnButton"): workshop.get_node("ReturnButton").hide()
	if workshop.has_node("Background"): workshop.get_node("Background").hide()
	tab3.add_child(workshop)
	tab_container.add_child(tab3)
	tab_container.set_tab_title(2, tr("tab_card_workshop"))
	
	# 5. Inject Teammates
	var tab4 = MarginContainer.new()
	tab4.name = "TeammateTab"
	var teammate = teammate_scene.instantiate()
	if teammate.has_node("NavHBox"): teammate.get_node("NavHBox").hide()
	if teammate.has_node("ColorRect"): teammate.get_node("ColorRect").hide()
	tab4.add_child(teammate)
	tab_container.add_child(tab4)
	tab_container.set_tab_title(3, tr("tab_teammates"))
	
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
	
	var main_vbox = VBoxContainer.new()
	main_vbox.set_anchors_preset(Control.PRESET_CENTER)
	main_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	nodes_container.add_child(main_vbox)
	
	var title = Label.new()
	title.text = "外掛擴充槽 (Active Implants)"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 24)
	main_vbox.add_child(title)
	
	var grid = GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 20)
	grid.add_theme_constant_override("v_separation", 20)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	main_vbox.add_child(grid)
	
	var stat_label = Label.new()
	stat_label.text = "\n[ 晶片共鳴 (Resonance) ]\nMax AP: +40%  |  Draw Rate: +2"
	stat_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	stat_label.modulate = Color(0.2, 1.0, 0.4) # Cyber green
	main_vbox.add_child(stat_label)
	
	var node_icon = preload("res://assets/images/chip_green_target.png")
	var slot_bg = preload("res://assets/images/icon_equipment_slot.png")
	
	var implant_names = ["超頻核心 (Overclock)", "神經加速器 (Neural Accel)", "量子算力 (Quantum Compute)", "記憶擴充 (Mem Expansion)"]
	var implant_effects = ["AP Recovery +5/turn", "Draw 1 extra card", "Reasoning Depth +1", "Max Hand Size +2"]
	
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
			btn.tooltip_text = "【%s】\n%s" % [implant_names[i], implant_effects[i]]
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
