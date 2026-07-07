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
	if teammate.has_node("MarginContainer/VBoxContainer/NavHBox"): 
		teammate.get_node("MarginContainer/VBoxContainer/NavHBox").hide()
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
        
	var profile_panel = get_node_or_null("HBoxContainer/ProfilePanel")
	var terminal_panel = get_node_or_null("HBoxContainer/TerminalPanel")
	for panel in [profile_panel, terminal_panel]:
		if panel:
			var style = StyleBoxFlat.new()
			style.bg_color = Color(0.05, 0.1, 0.15, 0.8)
			style.border_width_left = 2
			style.border_width_top = 2
			style.border_width_right = 2
			style.border_width_bottom = 2
			style.border_color = Color(0.0, 0.8, 0.8, 0.5)
			style.corner_radius_top_left = 16
			style.corner_radius_top_right = 16
			style.corner_radius_bottom_left = 16
			style.corner_radius_bottom_right = 16
			panel.add_theme_stylebox_override("panel", style)

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

var _typewriter_tween: Tween

func _print_to_terminal(text: String) -> void:
	if not terminal_lore: return
	terminal_lore.visible_characters = 0
	terminal_lore.text = text
	
	if _typewriter_tween:
		_typewriter_tween.kill()
	_typewriter_tween = create_tween()
	var duration = text.length() * 0.02 # Fast typing
	_typewriter_tween.tween_property(terminal_lore, "visible_ratio", 1.0, duration)
	
	# Glitch effect on terminal
	var glitch_tween = create_tween()
	for i in range(4):
		glitch_tween.tween_property(terminal_lore, "modulate", Color(randf_range(0.5, 1.5), randf_range(0.5, 1.5), randf_range(0.5, 1.5), 1.0), 0.05)
	glitch_tween.tween_property(terminal_lore, "modulate", Color.WHITE, 0.05)

func setup_topology_web() -> void:
	for c in lines_container.get_children(): c.queue_free()
	for c in nodes_container.get_children(): c.queue_free()
	
	var node_icon = preload("res://assets/images/chip_green_target.png")
	var slot_bg = preload("res://assets/images/icon_equipment_slot.png")
	
	var implant_names = ["超頻核心 (Overclock)", "神經加速器 (Neural Accel)", "量子算力 (Quantum Compute)", "記憶擴充 (Mem Expansion)", "終極協定 (Root Protocol)"]
	var implant_effects = ["AP Recovery +5/turn", "Draw 1 extra card", "Reasoning Depth +1", "Max Hand Size +2", "Unlock Admin Privileges"]
	var implant_lore = [
		"A standard issue military grade overclock module. Tends to run hot. Prolonged use may cause neural burnout.",
		"Illegal neural lace modification. Increases reaction time by 300% but voids warranty.",
		"Miniaturized Q-bit processor array. Directly interfaces with the frontal lobe for instantaneous calculations.",
		"Extra terabytes of cold storage for your brain. Perfect for hoarding encrypted corporate data.",
		"The holy grail of netrunners. Grants root access to reality itself. Use with extreme caution."
	]
	
	# Topology positions relative to center
	var positions = [
		Vector2(0, -120),
		Vector2(-100, -30),
		Vector2(100, -30),
		Vector2(-70, 80),
		Vector2(70, 80)
	]
	
	var center = Vector2(250, 200) # Topology center
	
	# Draw Lines
	for pos in positions:
		var line = Line2D.new()
		line.add_point(center)
		line.add_point(center + pos)
		line.width = 4
		line.default_color = Color(0.2, 0.6, 0.8, 0.5)
		
		# Apply shader material if available (we'll just use a glowing color here for robustness)
		var mat = CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		line.material = mat
		lines_container.add_child(line)
		
	# Draw Root Node
	var root_slot = TextureRect.new()
	root_slot.texture = slot_bg
	root_slot.custom_minimum_size = Vector2(80, 80)
	root_slot.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	root_slot.position = center - Vector2(40, 40)
	root_slot.modulate = Color(1.0, 0.8, 0.2) # Gold core
	nodes_container.add_child(root_slot)
	
	for i in range(positions.size()):
		var pos = center + positions[i]
		
		var slot = TextureRect.new()
		slot.texture = slot_bg
		slot.custom_minimum_size = Vector2(64, 64)
		slot.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		slot.position = pos - Vector2(32, 32)
		
		var btn = TextureButton.new()
		btn.texture_normal = node_icon
		btn.ignore_texture_size = true
		btn.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		btn.custom_minimum_size = Vector2(48, 48)
		btn.set_anchors_preset(Control.PRESET_CENTER)
		btn.pivot_offset = Vector2(24, 24)
		
		var lore_text = "【%s】\n\n[ EFFECT ]\n%s\n\n[ LORE ]\n%s" % [implant_names[i], implant_effects[i], implant_lore[i]]
		btn.pressed.connect(_on_node_pressed.bind(i, btn, lore_text))
		btn.mouse_entered.connect(_on_node_hovered.bind(btn, true))
		btn.mouse_exited.connect(_on_node_hovered.bind(btn, false))
		
		slot.add_child(btn)
		nodes_container.add_child(slot)
		
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
	tween.parallel().tween_property(btn, "modulate", Color(3.0, 3.0, 3.0, 1.0), 0.05) # Extreme HDR Glow
	tween.tween_property(btn, "scale", Vector2(1.2, 1.2), 0.3).set_trans(Tween.TRANS_BOUNCE)
	tween.parallel().tween_property(btn, "modulate", Color(1.5, 1.5, 1.5, 1.0), 0.3)
	
	_print_to_terminal(lore_text)
