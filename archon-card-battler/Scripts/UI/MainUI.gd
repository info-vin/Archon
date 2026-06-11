extends Node2D

var deck_manager: DeckManager
var git_parser: GitLogParser
var hand: Array[CardStats] = []

# Game State
var player_hp: int = 100
var player_max_hp: int = 100
var player_mana: int = 5
var player_max_mana: int = 5
var player_block: int = 0
var enemy_hp: int = 200
var enemy_max_hp: int = 200
var enemy_damage: int = 10

# Combo System
var current_combo_category: String = ""
var combo_count: int = 0

@onready var action_log = $UILayer/UIRoot/LogArea/ActionLog
@onready var enemy_hp_bar = $UILayer/UIRoot/EnemyHUD/EnemyHP
@onready var enemy_intent = $UILayer/UIRoot/EnemyHUD/EnemyIntent
@onready var player_hp_bar = $UILayer/UIRoot/PlayerHUD/PlayerHP
@onready var mana_label = $UILayer/UIRoot/PlayerHUD/ManaLabel
@onready var combo_label = $UILayer/UIRoot/ComboLabel
@onready var fighter_left = $UILayer/UIRoot/FighterLeft
@onready var fighter_right = $UILayer/UIRoot/FighterRight
@onready var hand_area = $UILayer/UIRoot/HandArea
@onready var end_turn_button = $UILayer/UIRoot/EndTurnButton
@onready var camera = $Camera2D

@onready var game_over_overlay = $TopLayer/GameOverOverlay
@onready var result_label = $TopLayer/GameOverOverlay/VBox/ResultLabel
@onready var restart_button = $TopLayer/GameOverOverlay/VBox/RestartButton

var hit_sound: AudioStreamPlayer
var error_sound: AudioStreamPlayer

func _ready() -> void:
	hit_sound = AudioStreamPlayer.new()
	hit_sound.stream = preload("res://Assets/Sounds/hit.wav")
	add_child(hit_sound)
	
	error_sound = AudioStreamPlayer.new()
	error_sound.stream = preload("res://Assets/Sounds/error.wav")
	add_child(error_sound)
	
	deck_manager = DeckManager.new()
	git_parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	
	_init_deck()
	
	end_turn_button.pressed.connect(_on_end_turn_pressed)
	restart_button.pressed.connect(restart_game)
	
	update_ui()
	start_player_turn()

func _init_deck() -> void:
	var mock_logs = [
		"Refactor auth module\n 4 files changed, 120 insertions(+), 30 deletions(-)",
		"Fix memory leak in parser\n 2 files changed, 15 insertions(+), 8 deletions(-)",
		"Update README.md\n 1 file changed, 5 insertions(+)",
		"Clean up dead CSS\n 3 files changed, 200 deletions(-)",
		"Implement RLS rules\n 2 files changed, 45 insertions(+), 5 deletions(-)",
		"Hotfix production crash\n 1 file changed, 2 insertions(+), 2 deletions(-)",
		"Upgrade dependencies\n 5 files changed, 300 insertions(+), 150 deletions(-)"
	]
	
	for i in range(15):
		var log_str = mock_logs[randi() % mock_logs.size()]
		var card = git_parser.generate_card_from_log(log_str)
		card.cost = mini(card.cost, 2) 
		card.damage = maxi(mini(card.damage / 10, 25), 0) 
		card.block = maxi(mini(card.block / 10, 20), 0) 
		deck_manager.add_card(card)

func start_player_turn() -> void:
	player_mana = player_max_mana
	player_block = 0
	current_combo_category = ""
	combo_count = 0
	combo_label.text = ""
	
	hand.clear()
	for i in range(4): # Draw 4 cards to keep hand cleaner
		var c = deck_manager.draw_card()
		if c != null:
			hand.append(c)
		else:
			log_action("Deck is empty!")
			break
	
	log_action("\n[b][color=#3b82f6]--- Player Turn Started ---[/color][/b]")
	update_ui()

func play_card(index: int) -> void:
	if index >= hand.size(): return
	var card = hand[index]
	
	if player_mana < card.cost:
		shake_camera(5.0)
		error_sound.play()
		log_action("[color=#ef4444]❌ Not enough Tokens to play " + card.card_name + "[/color]")
		return
		
	# Pay cost
	player_mana -= card.cost
	
	# Combo Logic (Any card played builds the combo!)
	combo_count += 1
	if combo_count > 1:
		show_combo_animation(card.category)
	
	var multiplier = 1.0 + (combo_count - 1) * 0.5
	var final_damage = int(float(card.damage) * multiplier)
	
	# Apply effects
	enemy_hp -= final_damage
	player_block += card.block
	
	var msg = "[color=#fde047]Played: " + card.card_name + "[/color]\n"
	if final_damage > 0: 
		if combo_count > 1:
			msg += " dealt " + str(final_damage) + " DMG. (" + str(multiplier) + "x COMBO!)"
		else:
			msg += " dealt " + str(final_damage) + " DMG."
		shake_camera(final_damage * 0.5)
		hit_sound.play()
		animate_fighter(fighter_left, 50)
		spawn_floating_text(fighter_right.global_position + Vector2(100, 100), "-" + str(final_damage), Color(1, 0.2, 0.2))
		
	if card.block > 0: 
		msg += " gained " + str(card.block) + " Block."
		spawn_floating_text(fighter_left.global_position + Vector2(100, 100), "+" + str(card.block) + "🛡️", Color(0.2, 0.8, 1))
	log_action(msg)
	
	hand.remove_at(index)
	update_ui()
	check_win_condition()

func spawn_floating_text(pos: Vector2, text: String, color: Color):
	var lbl = Label.new()
	lbl.text = text
	lbl.add_theme_font_size_override("font_size", 48)
	lbl.add_theme_color_override("font_color", color)
	lbl.add_theme_color_override("font_shadow_color", Color(0,0,0,1))
	$UILayer.add_child(lbl)
	lbl.global_position = pos - Vector2(50, 50)
	
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(lbl, "global_position:y", lbl.global_position.y - 100, 0.8)
	tween.parallel().tween_property(lbl, "modulate:a", 0.0, 0.8)
	tween.tween_callback(lbl.queue_free)

func show_combo_animation(category: String):
	var multiplier = 1.0 + (combo_count - 1) * 0.5
	combo_label.text = str(multiplier) + "x COMBO!"
	combo_label.pivot_offset = combo_label.size / 2
	var tween = create_tween().set_trans(Tween.TRANS_SPRING)
	tween.tween_property(combo_label, "scale", Vector2(1.5, 1.5), 0.2).from(Vector2(0.5, 0.5))
	tween.tween_property(combo_label, "scale", Vector2(1, 1), 0.2)

func animate_fighter(fighter: Node, distance: float):
	var tween = create_tween().set_trans(Tween.TRANS_ELASTIC)
	var original_pos = fighter.position
	tween.tween_property(fighter, "position:x", original_pos.x + distance, 0.1)
	tween.tween_property(fighter, "position:x", original_pos.x, 0.3)

func _on_end_turn_pressed() -> void:
	log_action("Player ended turn.")
	enemy_turn()

func enemy_turn() -> void:
	log_action("\n[b][color=#ef4444]👾 Enemy attacks for " + str(enemy_damage) + " DMG![/color][/b]")
	animate_fighter(fighter_right, -50)
	
	var actual_damage = max(0, enemy_damage - player_block)
	player_hp -= actual_damage
	
	if player_block > 0:
		log_action("🛡️ Block absorbed " + str(min(enemy_damage, player_block)) + " DMG.")
		
	if actual_damage > 0:
		shake_camera(15.0)
		hit_sound.play()
		log_action("Player took " + str(actual_damage) + " DMG.")
	
	update_ui()
	if !check_win_condition():
		start_player_turn()

func check_win_condition() -> bool:
	if enemy_hp <= 0:
		enemy_hp = 0
		update_ui()
		show_game_over(true)
		return true
	if player_hp <= 0:
		player_hp = 0
		update_ui()
		show_game_over(false)
		return true
	return false

func show_game_over(win: bool) -> void:
	end_turn_button.disabled = true
	game_over_overlay.visible = true
	if win:
		result_label.text = "🎉 DEPLOYMENT SUCCESS!"
		result_label.add_theme_color_override("font_color", Color(0.2, 1, 0.4))
	else:
		result_label.text = "💀 SYSTEM CRASH"
		result_label.add_theme_color_override("font_color", Color(1, 0.2, 0.2))

func restart_game() -> void:
	game_over_overlay.visible = false
	end_turn_button.disabled = false
	player_hp = player_max_hp
	enemy_hp = enemy_max_hp
	deck_manager = DeckManager.new()
	_init_deck()
	action_log.text = "[b]Combat Log[/b]\n"
	start_player_turn()

func log_action(msg: String) -> void:
	action_log.append_text(msg + "\n")
	var scrollbar = action_log.get_v_scroll_bar()
	scrollbar.value = scrollbar.max_value

func shake_camera(intensity: float) -> void:
	var tween = create_tween()
	var original_pos = Vector2(576, 324)
	for i in range(4):
		var offset = Vector2(randf_range(-intensity, intensity), randf_range(-intensity, intensity))
		tween.tween_property(camera, "position", original_pos + offset, 0.05)
	tween.tween_property(camera, "position", original_pos, 0.05)

func update_ui() -> void:
	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(player_hp_bar, "value", float(player_hp), 0.3)
	tween.tween_property(enemy_hp_bar, "value", float(enemy_hp), 0.3)
	
	mana_label.text = "💎 Tokens: %d/%d | 🛡️ Block: %d | 🎴 Deck: %d" % [player_mana, player_max_mana, player_block, deck_manager.get_deck_size()]
	
	for child in hand_area.get_children():
		child.queue_free()
		
	var card_scene = preload("res://Scenes/UI/CardUI.tscn")
	var hand_width = hand_area.size.x if hand_area.size.x > 0 else 650.0
	var card_width = 180.0
	var total_cards = hand.size()
	
	var max_spacing = 100.0 # Tighter overlap
	var required_width = card_width + (total_cards - 1) * max_spacing
	var spacing = max_spacing
	if required_width > hand_width:
		spacing = (hand_width - card_width) / max(1, total_cards - 1)
	if total_cards <= 1: spacing = 0
	
	var total_width = card_width + (total_cards - 1) * spacing
	var start_x = (hand_width - total_width) / 2.0
	
	for i in range(total_cards):
		var card = hand[i]
		var card_ui = card_scene.instantiate()
		hand_area.add_child(card_ui)
		
		var target_x = start_x + (i * spacing)
		
		# Radial Fanning Math
		var t = 0.5 if total_cards <= 1 else float(i) / float(total_cards - 1)
		var curve_y = abs(t - 0.5) * abs(t - 0.5) * 150.0 # Parabola dropping in center
		var rotation_deg = lerpf(-15.0, 15.0, t)
		
		card_ui.position = Vector2(target_x, 50 + curve_y)
		card_ui.rotation_degrees = rotation_deg
		card_ui.original_y = card_ui.position.y # Save for hover tween
		
		card_ui.setup(card, i)
		card_ui.pressed.connect(func(): play_card(card_ui.card_index))
		card_ui.animate_draw(card_ui.position)
