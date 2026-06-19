extends Button

@onready var cost_label = $VBox/TopRow/CostLabel
@onready var name_label = $VBox/NameLabel
@onready var desc_label = $VBox/DescLabel
@onready var type_label = $VBox/TopRow/TypeLabel

var card_index: int = -1
var original_y: float = 0.0
var original_scale: Vector2 = Vector2.ONE
var is_combo_card: bool = false
var combo_glow_tween: Tween

# Sound effect nodes (to be assigned by MainUI or auto-created)
var hover_sound: AudioStreamPlayer
var play_sound: AudioStreamPlayer

func setup(card_stats: CardStats, index: int, is_combo_active: bool = false) -> void:
	card_index = index
	is_combo_card = is_combo_active
	
	if OS.has_feature("web"):
		cost_label.text = "◆ " + str(card_stats.cost)
	else:
		cost_label.text = "💎 " + str(card_stats.cost)
	
	var cjk_font = preload("res://Assets/Fonts/arial_unicode.ttf")
	cjk_font.multichannel_signed_distance_field = true # Enable MSDF for crisp text rendering at any resolution
	cost_label.add_theme_font_override("font", cjk_font)
	name_label.add_theme_font_override("font", cjk_font)
	desc_label.add_theme_font_override("normal_font", cjk_font)
	desc_label.add_theme_font_override("bold_font", cjk_font)
	desc_label.add_theme_font_override("italics_font", cjk_font)
	desc_label.add_theme_font_override("bold_italics_font", cjk_font)
	type_label.add_theme_font_override("font", cjk_font)
	
	var card_name = card_stats.card_name
	if OS.has_feature("web"):
		# Strip emojis by removing characters outside the Basic Multilingual Plane (BMP) or in symbol ranges
		var clean_name = ""
		for char_idx in range(card_name.length()):
			var c = card_name[char_idx]
			var code = c.unicode_at(0)
			# Filter out standard emoji ranges (U+2600 to U+27BF) and anything > U+FFFF
			if code < 0x2600 or (code > 0x27BF and code <= 0xFFFF):
				clean_name += c
		card_name = clean_name.strip_edges()
		
	if card_name.contains(" ("):
		card_name = card_name.replace(" (", "\n(")
	name_label.text = card_name
	name_label.add_theme_font_size_override("font_size", 14)
	name_label.autowrap_mode = TextServer.AUTOWRAP_ARBITRARY
	
	# Determine theme colors based on Category (solid background colors for optimal readability, preserving neon borders)
	var bg_color = Color(0.15, 0.17, 0.23, 1.0) # Default opaque dark
	var border_color = Color(0.3, 0.8, 1.0, 0.8) # Default neon cyan
	
	type_label.text = card_stats.category
	if card_stats.category == "Feature":
		type_label.text = "功能 (Feature)"
		bg_color = Color(0.15, 0.23, 0.15, 1.0)
		border_color = Color(0.4, 1.0, 0.4, 0.8)
	elif card_stats.category == "Docs":
		type_label.text = "說明文件 (Docs)"
		bg_color = Color(0.15, 0.23, 0.23, 1.0)
		border_color = Color(0.4, 1.0, 1.0, 0.8)
	elif card_stats.category == "Merge":
		type_label.text = "分支合併 (Merge)"
		bg_color = Color(0.25, 0.22, 0.15, 1.0)
		border_color = Color(1.0, 0.85, 0.4, 0.8)
	elif card_stats.category == "Fix":
		type_label.text = "修復 (Fix)"
		bg_color = Color(0.23, 0.15, 0.15, 1.0)
		border_color = Color(1.0, 0.4, 0.4, 0.8)
	elif card_stats.category == "Refactor":
		type_label.text = "重構 (Refactor)"
		bg_color = Color(0.15, 0.15, 0.23, 1.0)
		border_color = Color(0.4, 0.4, 1.0, 0.8)
	elif card_stats.category == "Performance":
		type_label.text = "效能 (Performance)"
		bg_color = Color(0.23, 0.23, 0.15, 1.0)
		border_color = Color(1.0, 1.0, 0.4, 0.8)
	elif card_stats.category == "Chore":
		type_label.text = "雜務 (Chore)"
		bg_color = Color(0.20, 0.20, 0.20, 1.0)
		border_color = Color(0.6, 0.6, 0.6, 0.8)
	elif card_stats.category == "Test":
		type_label.text = "測試 (Test)"
		bg_color = Color(0.20, 0.15, 0.25, 1.0)
		border_color = Color(0.75, 0.6, 0.9, 0.8)
	elif card_stats.category == "Style":
		type_label.text = "樣式 (Style)"
		bg_color = Color(0.25, 0.15, 0.20, 1.0)
		border_color = Color(1.0, 0.6, 0.8, 0.8)
	elif card_stats.category == "Agent":
		type_label.text = "自動化 (Agent)"
		bg_color = Color(0.18, 0.12, 0.25, 1.0)
		border_color = Color(0.6, 0.3, 0.9, 0.8)
		
	# Apply dynamic styling
	var style_normal = get_theme_stylebox("normal").duplicate() as StyleBoxFlat
	style_normal.bg_color = bg_color
	style_normal.border_color = border_color
	add_theme_stylebox_override("normal", style_normal)
	
	var style_hover = get_theme_stylebox("hover").duplicate() as StyleBoxFlat
	style_hover.bg_color = bg_color.lightened(0.2)
	style_hover.border_color = border_color.lightened(0.4)
	add_theme_stylebox_override("hover", style_hover)
	add_theme_stylebox_override("pressed", style_hover)
	
	# BBCode formatting (Traditional Chinese localization)
	var bbcode_text = "[center]"
	if card_stats.damage > 0:
		bbcode_text += "[color=#4ade80]新增 +%d 行[/color]\n" % card_stats.damage
	if card_stats.block > 0:
		bbcode_text += "[color=#f87171]刪除 -%d 行[/color]\n" % card_stats.block
	if card_stats.damage == 0 and card_stats.block == 0:
		bbcode_text += "[color=#9ca3af]中繼資料變更[/color]"
	bbcode_text += "[/center]"
		
	desc_label.text = bbcode_text
	desc_label.add_theme_font_size_override("normal_font_size", 13)
	
	# Setup combo highlight if active
	if is_combo_card:
		type_label.text = "[COMBO] " + type_label.text
		type_label.add_theme_color_override("font_color", Color(1.0, 0.85, 0.2))
		# Delay start combo glow slightly to prevent race conditions during draw animation
		get_tree().create_timer(0.4).timeout.connect(func():
			if is_inside_tree() and is_combo_card:
				start_combo_glow()
		)
	else:
		stop_combo_glow()

func start_combo_glow() -> void:
	stop_combo_glow()
	
	var style_normal = get_theme_stylebox("normal").duplicate() as StyleBoxFlat
	add_theme_stylebox_override("normal", style_normal)
	
	combo_glow_tween = create_tween().set_loops()
	
	var base_border = Color(1.0, 0.85, 0.2, 0.9) # Glowing gold border
	var dim_border = Color(1.0, 0.85, 0.2, 0.35)
	
	combo_glow_tween.tween_property(self, "scale", original_scale * 1.04, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	combo_glow_tween.parallel().tween_property(style_normal, "border_color", base_border, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	combo_glow_tween.parallel().tween_property(style_normal, "shadow_color", Color(1.0, 0.85, 0.2, 0.6), 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	combo_glow_tween.parallel().tween_property(style_normal, "shadow_size", 16, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	
	combo_glow_tween.tween_property(self, "scale", original_scale, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	combo_glow_tween.parallel().tween_property(style_normal, "border_color", dim_border, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	combo_glow_tween.parallel().tween_property(style_normal, "shadow_color", Color(1.0, 0.85, 0.2, 0.2), 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	combo_glow_tween.parallel().tween_property(style_normal, "shadow_size", 6, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func stop_combo_glow() -> void:
	if combo_glow_tween:
		combo_glow_tween.kill()
		combo_glow_tween = null
	scale = original_scale

func _ready():
	original_y = position.y
	original_scale = scale
	mouse_entered.connect(_on_hover)
	mouse_exited.connect(_on_unhover)
	
	hover_sound = AudioStreamPlayer.new()
	hover_sound.stream = preload("res://Assets/Sounds/hover.wav")
	add_child(hover_sound)
	
	play_sound = AudioStreamPlayer.new()
	play_sound.stream = preload("res://Assets/Sounds/play.wav")
	add_child(play_sound)

var original_rotation: float = 0.0

func _on_hover():
	original_rotation = rotation_degrees
	stop_combo_glow() # Pause combo glow during hover
	scale = original_scale
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	# Cancel scale animation to keep text crisp, increase vertical displacement
	tween.tween_property(self, "position:y", original_y - 45.0, 0.15)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.15)
	z_index = 100
	if hover_sound:
		hover_sound.play()

func _on_unhover():
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:y", original_y, 0.15)
	tween.parallel().tween_property(self, "rotation_degrees", original_rotation, 0.15)
	z_index = 0
	if is_combo_card:
		start_combo_glow() # Resume combo glow

func animate_draw(target_position: Vector2):
	var tween = create_tween().set_trans(Tween.TRANS_SPRING).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "scale", original_scale, 0.4).from(Vector2.ZERO)
	tween.parallel().tween_property(self, "position", target_position, 0.4)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.4).from(-180.0)

func _exit_tree() -> void:
	stop_combo_glow()
