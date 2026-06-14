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
	cost_label.text = "◆ " + str(card_stats.cost)
	name_label.text = card_stats.card_name
	
	# Determine theme colors based on Category
	var bg_color = Color(0.15, 0.17, 0.23, 1)
	var border_color = Color(0.3, 0.8, 1, 0.8)
	
	type_label.text = card_stats.category
	if card_stats.category == "Feature":
		type_label.text = "功能 (Feature)"
		bg_color = Color(0.15, 0.23, 0.15, 1)
		border_color = Color(0.4, 1.0, 0.4, 0.8)
	elif card_stats.category == "Docs":
		type_label.text = "說明文件 (Docs)"
		bg_color = Color(0.15, 0.23, 0.23, 1)
		border_color = Color(0.4, 1.0, 1.0, 0.8)
	elif card_stats.category == "Merge":
		type_label.text = "分支合併 (Merge)"
		bg_color = Color(0.25, 0.22, 0.15, 1)
		border_color = Color(1.0, 0.85, 0.4, 0.8)
	elif card_stats.category == "Fix":
		type_label.text = "修復 (Fix)"
		bg_color = Color(0.23, 0.15, 0.15, 1)
		border_color = Color(1.0, 0.4, 0.4, 0.8)
	elif card_stats.category == "Refactor":
		type_label.text = "重構 (Refactor)"
		bg_color = Color(0.15, 0.15, 0.23, 1)
		border_color = Color(0.4, 0.4, 1.0, 0.8)
	elif card_stats.category == "Performance":
		type_label.text = "效能 (Performance)"
		bg_color = Color(0.23, 0.23, 0.15, 1)
		border_color = Color(1.0, 1.0, 0.4, 0.8)
	elif card_stats.category == "Chore":
		type_label.text = "雜務 (Chore)"
		bg_color = Color(0.2, 0.2, 0.2, 1)
		border_color = Color(0.6, 0.6, 0.6, 0.8)
	elif card_stats.category == "Test":
		type_label.text = "測試 (Test)"
		bg_color = Color(0.2, 0.15, 0.25, 1)
		border_color = Color(0.75, 0.6, 0.9, 0.8)
	elif card_stats.category == "Style":
		type_label.text = "樣式 (Style)"
		bg_color = Color(0.25, 0.15, 0.2, 1)
		border_color = Color(1.0, 0.6, 0.8, 0.8)
	elif card_stats.category == "Agent":
		type_label.text = "自動化 (Agent)"
		bg_color = Color(0.18, 0.12, 0.25, 1)
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
		bbcode_text += "[color=#4ade80]+%d 程式碼新增 (Insertions)[/color]\n" % card_stats.damage
	if card_stats.block > 0:
		bbcode_text += "[color=#f87171]-%d 程式碼刪除 (Deletions)[/color]\n" % card_stats.block
	if card_stats.damage == 0 and card_stats.block == 0:
		bbcode_text += "[color=#9ca3af]中繼資料變更 (Metadata)...[/color]"
	bbcode_text += "[/center]"
		
	desc_label.text = bbcode_text

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
	tween.tween_property(self, "scale", original_scale * 1.15, 0.15)
	tween.parallel().tween_property(self, "position:y", original_y - 25.0, 0.15)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.15)
	z_index = 100
	if hover_sound:
		hover_sound.play()

func _on_unhover():
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "scale", original_scale, 0.15)
	tween.parallel().tween_property(self, "position:y", original_y, 0.15)
	tween.parallel().tween_property(self, "rotation_degrees", original_rotation, 0.15)
	z_index = 0

func animate_draw(target_position: Vector2):
	var tween = create_tween().set_trans(Tween.TRANS_SPRING).set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "scale", original_scale, 0.4).from(Vector2.ZERO)
	tween.parallel().tween_property(self, "position", target_position, 0.4)
	tween.parallel().tween_property(self, "rotation_degrees", 0.0, 0.4).from(-180.0)
