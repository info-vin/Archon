extends HBoxContainer
class_name TokenHud

var token_label: Label
var block_label: Label
var deck_label: Label
var discard_label: Label

func setup_hud(cjk_font: Font) -> void:
	add_theme_constant_override("separation", 12)
	
	var VectorIconScript = preload("res://Scripts/UI/VectorIcon.gd")
	
	# 1. Tokens
	var token_icon = VectorIconScript.new()
	token_icon.type = VectorIcon.IconType.TOKEN
	token_icon.color = Color(0.0, 0.8, 1.0)
	token_icon.custom_minimum_size = Vector2(18, 18)
	add_child(token_icon)
	
	token_label = Label.new()
	token_label.add_theme_font_override("font", cjk_font)
	token_label.add_theme_font_size_override("font_size", 16)
	add_child(token_label)
	
	# Separator 1
	var sep1 = Label.new()
	sep1.text = "|"
	sep1.add_theme_font_override("font", cjk_font)
	sep1.add_theme_font_size_override("font_size", 16)
	sep1.modulate = Color(0.3, 0.3, 0.3)
	add_child(sep1)
	
	# 2. Block
	var block_icon = VectorIconScript.new()
	block_icon.type = VectorIcon.IconType.BLOCK
	block_icon.color = Color(0.2, 0.9, 0.6)
	block_icon.custom_minimum_size = Vector2(18, 18)
	add_child(block_icon)
	
	block_label = Label.new()
	block_label.add_theme_font_override("font", cjk_font)
	block_label.add_theme_font_size_override("font_size", 16)
	add_child(block_label)
	
	# Separator 2
	var sep2 = Label.new()
	sep2.text = "|"
	sep2.add_theme_font_override("font", cjk_font)
	sep2.add_theme_font_size_override("font_size", 16)
	sep2.modulate = Color(0.3, 0.3, 0.3)
	add_child(sep2)
	
	# 3. Deck
	var deck_icon = VectorIconScript.new()
	deck_icon.type = VectorIcon.IconType.DECK
	deck_icon.color = Color(1.0, 0.8, 0.2)
	deck_icon.custom_minimum_size = Vector2(18, 18)
	add_child(deck_icon)
	
	deck_label = Label.new()
	deck_label.add_theme_font_override("font", cjk_font)
	deck_label.add_theme_font_size_override("font_size", 16)
	add_child(deck_label)
	
	# Separator 3
	var sep3 = Label.new()
	sep3.text = "|"
	sep3.add_theme_font_override("font", cjk_font)
	sep3.add_theme_font_size_override("font_size", 16)
	sep3.modulate = Color(0.3, 0.3, 0.3)
	add_child(sep3)
	
	# 4. Discard
	var discard_icon = VectorIconScript.new()
	discard_icon.type = VectorIcon.IconType.DISCARD
	discard_icon.color = Color(1.0, 0.4, 0.4)
	discard_icon.custom_minimum_size = Vector2(18, 18)
	add_child(discard_icon)
	
	discard_label = Label.new()
	discard_label.add_theme_font_override("font", cjk_font)
	discard_label.add_theme_font_size_override("font_size", 16)
	add_child(discard_label)

func update_values(mana: int, max_mana: int, block: int, deck_size: int, discard_size: int) -> void:
	if token_label:
		token_label.text = "%d/%d" % [mana, max_mana]
	if block_label:
		block_label.text = str(block)
	if deck_label:
		deck_label.text = str(deck_size)
	if discard_label:
		discard_label.text = str(discard_size)
