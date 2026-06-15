extends Button

@onready var cost_label = $VBox/TopRow/CostLabel
@onready var name_label = $VBox/NameLabel
@onready var desc_label = $VBox/DescLabel
@onready var type_label = $VBox/TopRow/TypeLabel

var card_index: int = -1
var original_y: float = 0.0
var original_scale: Vector2 = Vector2.ONE

# Sound effect nodes (to be assigned by MainUI or auto-created)
var hover_sound: AudioStreamPlayer
var play_sound: AudioStreamPlayer

func setup(card_stats: CardStats, index: int) -> void:
	card_index = index
	
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
	
	# Determine theme colors based on Category (unified solid dark background for optimal readability, preserving neon borders)
	var bg_color = Color(0.08, 0.09, 0.13, 1.0)
	var border_color = Color(0.3, 0.8, 1, 0.8)
	
	type_label.text = card_stats.category
	if card_stats.category == "Feature":
		type_label.text = "功能 (Feature)"
		border_color = Color(0.4, 1.0, 0.4, 0.8)
	elif card_stats.category == "Docs":
		type_label.text = "說明文件 (Docs)"
		border_color = Color(0.4, 1.0, 1.0, 0.8)
	elif card_stats.category == "Merge":
		type_label.text = "分支合併 (Merge)"
		border_color = Color(1.0, 0.85, 0.4, 0.8)
	elif card_stats.category == "Fix":
		type_label.text = "修復 (Fix)"
		border_color = Color(1.0, 0.4, 0.4, 0.8)
	elif card_stats.category == "Refactor":
		type_label.text = "重構 (Refactor)"
		border_color = Color(0.4, 0.4, 1.0, 0.8)
	elif card_stats.category == "Performance":
		type_label.text = "效能 (Performance)"
		border_color = Color(1.0, 1.0, 0.4, 0.8)
	elif card_stats.category == "Chore":
		type_label.text = "雜務 (Chore)"
		border_color = Color(0.6, 0.6, 0.6, 0.8)
	elif card_stats.category == "Test":
		type_label.text = "測試 (Test)"
		border_color = Color(0.75, 0.6, 0.9, 0.8)
	elif card_stats.category == "Style":
		type_label.text = "樣式 (Style)"
		border_color = Color(1.0, 0.6, 0.8, 0.8)
	elif card_stats.category == "Agent":
		type_label.text = "自動化 (Agent)"
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
		bbcode_text += "[color=#4ade80]+%d 行新增 (Additions)[/color]\n" % card_stats.damage
	if card_stats.block > 0:
		bbcode_text += "[color=#f87171]-%d 行刪除 (Deletions)[/color]\n" % card_stats.block
	if card_stats.damage == 0 and card_stats.block == 0:
		bbcode_text += "[color=#9ca3af]中繼資料變更 (Metadata)[/color]"
	bbcode_text += "[/center]"
		
	desc_label.text = bbcode_text
	desc_label.add_theme_font_size_override("normal_font_size", 13)

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

func animate_draw(target_position: Vector2):
	var tween = create_tween().set_trans(Tween.TRANS_SPRING).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "scale", original_scale, 0.4).from(Vector2.ZERO)
	tween.parallel().tween_property(self, "position", target_position, 0.4)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.4).from(-180.0)
