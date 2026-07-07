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

func _ready() -> void:
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
	# Define a few mock nodes and connections matching the background roughly
	var node_positions = [
		Vector2(400, 300), # Center (Master Power)
		Vector2(400, 150), # Top
		Vector2(550, 300), # Right
		Vector2(400, 450), # Bottom
		Vector2(250, 300)  # Left
	]
	
	var connections = [
		[0, 1], [0, 2], [0, 3], [0, 4]
	]
	
	for conn in connections:
		var line = Line2D.new()
		line.add_point(node_positions[conn[0]])
		line.add_point(node_positions[conn[1]])
		line.width = 4.0
		line.default_color = Color(0.2, 0.8, 1.0, 1.0)
		
		# Set shader
		if line_shader:
			var mat = ShaderMaterial.new()
			mat.shader = line_shader
			line.material = mat
			
		lines_container.add_child(line)
		
	for i in range(node_positions.size()):
		var btn = TextureButton.new()
		btn.position = node_positions[i] - Vector2(32, 32)
		btn.custom_minimum_size = Vector2(64, 64)
		btn.pressed.connect(_on_node_pressed.bind(i))
		nodes_container.add_child(btn)

func _on_node_pressed(node_idx: int) -> void:
	print("Topology Node %d clicked! Emitting pulse..." % node_idx)
	var btn = nodes_container.get_child(node_idx)
	var tween = create_tween()
	tween.tween_property(btn, "modulate", Color(2.0, 2.0, 2.0, 1.0), 0.1) # HDR Glow
	tween.tween_property(btn, "modulate", Color.WHITE, 0.4)
