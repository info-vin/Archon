extends Node2D

enum Difficulty { EASY, NORMAL, HARD, EXPERT }
var difficulty: Difficulty = Difficulty.NORMAL

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
var enemy_block: int = 0
var enemy_strength: int = 0
var game_turn_counter: int = 0

# Combo System
var current_combo_category: String = ""
var combo_count: int = 0

@onready var background_node = $Background
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

# Turn Timer & Help system
var turn_timer: float = 30.0
var timer_label: Label
var help_overlay: ColorRect = null

func _ready() -> void:
	# Dynamic font fallback: keep browser native emojis visible while supporting Traditional Chinese characters
	var default_font = ThemeDB.fallback_font
	if default_font is FontFile:
		while default_font.get_fallback_count() > 0:
			default_font.remove_fallback(0)
			
		var emoji_font = SystemFont.new()
		emoji_font.font_names = PackedStringArray([
			"Apple Color Emoji",
			"Segoe UI Emoji",
			"Noto Color Emoji",
			"Android Emoji",
			"Emoji",
			"Segoe UI Symbol"
		])
		default_font.add_fallback(emoji_font)
		
		var custom_font = load("res://Assets/Fonts/arial_unicode.ttf")
		default_font.add_fallback(custom_font)
		
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
	
	# Hide the End Turn button as requested (shortcut Space/Enter and auto-timer will handle it)
	end_turn_button.visible = false
	
	# Scale characters down by 10% from center
	fighter_left.pivot_offset = fighter_left.size / 2
	fighter_left.scale = Vector2(0.9, 0.9)
	fighter_right.pivot_offset = fighter_right.size / 2
	fighter_right.scale = Vector2(0.9, 0.9)
	
	# Restore beautiful standard emojis (font size 120 keeps them elegant and avoids overlapping cards)
	fighter_left.text = "🥷"
	fighter_left.add_theme_font_size_override("font_size", 120)
	fighter_right.text = "🐛"
	fighter_right.add_theme_font_size_override("font_size", 120)
	
	# Create turn timer label in the middle of health bars (size 32)
	timer_label = Label.new()
	timer_label.text = "30s"
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	timer_label.add_theme_font_size_override("font_size", 32)
	timer_label.position = Vector2(516, 25)
	timer_label.size = Vector2(120, 60)
	$UILayer/UIRoot.add_child(timer_label)
	
	show_difficulty_selection()

func _process(delta: float) -> void:
	if end_turn_button.disabled or game_over_overlay.visible:
		timer_label.visible = false
		return
	
	timer_label.visible = true
	turn_timer -= delta
	if turn_timer <= 0.0:
		turn_timer = 30.0
		_on_end_turn_pressed()
	else:
		var display_time = ceil(turn_timer)
		timer_label.text = str(display_time) + "s"
		if display_time <= 5:
			# Enlarged font size for last 5 seconds and color red
			timer_label.add_theme_font_size_override("font_size", 44)
			timer_label.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
		else:
			timer_label.add_theme_font_size_override("font_size", 32)
			timer_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
			
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"): # Space or Enter
		if not end_turn_button.disabled:
			_on_end_turn_pressed()
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_H:
			show_help_overlay()
		elif event.keycode == KEY_ESCAPE:
			hide_help_overlay()

func show_help_overlay() -> void:
	if help_overlay != null:
		help_overlay.queue_free()
		
	help_overlay = ColorRect.new()
	help_overlay.name = "HelpOverlay"
	help_overlay.color = Color(0, 0, 0, 0.9)
	help_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	$UILayer/UIRoot.add_child(help_overlay)
	
	# Wrap in CenterContainer for perfect centering in browser WASM exports
	var center_container = CenterContainer.new()
	center_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	help_overlay.add_child(center_container)
	
	var v_box = VBoxContainer.new()
	v_box.alignment = BoxContainer.ALIGNMENT_CENTER
	v_box.add_theme_constant_override("separation", 15)
	center_container.add_child(v_box)
	
	var title = Label.new()
	title.text = "遊戲說明 (GAME MANUAL)"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 28)
	title.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	v_box.add_child(title)
	
	var rules = Label.new()
	rules.text = "【核心規則】\n" + \
		"1. 玩家為 Tech Lead [TECH LEAD]，敵人為專案技術債 Bug。\n" + \
		"2. 卡牌來自真實 Git commit，依照變更行數決定 Token 花費、攻擊與防禦。\n" + \
		"3. 每次出牌會累積 COMBO，傷害會以乘數放大！\n" + \
		"4. 重構自癒：打出 [重構] 卡牌時，可額外獲得傷害值 50% 的防禦護盾。\n" + \
		"5. 回合時間：每回合有 30 秒限制，或當 Token 消耗完時會自動結束回合。\n\n" + \
		"【快捷鍵說明】\n" + \
		"• [H] 鍵：開啟此遊戲說明\n" + \
		"• [ESC] 鍵：關閉遊戲說明\n" + \
		"• [Space / Enter] 鍵：結束玩家回合"
	rules.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	rules.add_theme_font_size_override("font_size", 16)
	v_box.add_child(rules)
	
	var close_btn = Button.new()
	close_btn.text = "關閉說明 (ESC)"
	close_btn.custom_minimum_size = Vector2(200, 40)
	close_btn.pressed.connect(hide_help_overlay)
	v_box.add_child(close_btn)

func hide_help_overlay() -> void:
	if help_overlay != null:
		help_overlay.queue_free()
		help_overlay = null

func show_difficulty_selection() -> void:
	# Block interactions with gameplay behind
	end_turn_button.disabled = true
	
	var overlay = ColorRect.new()
	overlay.name = "DifficultyOverlay"
	overlay.color = Color(0, 0, 0, 0.8)
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	$UILayer/UIRoot.add_child(overlay)
	
	# Wrap in CenterContainer for perfect centering in browser WASM exports
	var center_container = CenterContainer.new()
	center_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	overlay.add_child(center_container)
	
	var v_box = VBoxContainer.new()
	v_box.alignment = BoxContainer.ALIGNMENT_CENTER
	v_box.add_theme_constant_override("separation", 20)
	center_container.add_child(v_box)
	
	var title = Label.new()
	title.text = "SELECT DIFFICULTY / 選擇難度"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 40)
	title.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	v_box.add_child(title)
	
	var desc = Label.new()
	desc.text = "（難度將影響敵人的血量、每回合自動增加的護盾與隨時間成長的力量）"
	desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	desc.add_theme_font_size_override("font_size", 16)
	v_box.add_child(desc)
	
	var btn_easy = Button.new()
	btn_easy.text = "簡單 (Easy) - Target: <5 Turns"
	btn_easy.custom_minimum_size = Vector2(300, 50)
	btn_easy.pressed.connect(func(): select_difficulty(Difficulty.EASY, overlay))
	v_box.add_child(btn_easy)
	
	var btn_normal = Button.new()
	btn_normal.text = "普通 (Normal) - Target: ~8 Turns"
	btn_normal.custom_minimum_size = Vector2(300, 50)
	btn_normal.pressed.connect(func(): select_difficulty(Difficulty.NORMAL, overlay))
	v_box.add_child(btn_normal)
	
	var btn_hard = Button.new()
	btn_hard.text = "困難 (Hard) - Target: 20-50 Turns"
	btn_hard.custom_minimum_size = Vector2(300, 50)
	btn_hard.pressed.connect(func(): select_difficulty(Difficulty.HARD, overlay))
	v_box.add_child(btn_hard)
	
	var btn_expert = Button.new()
	btn_expert.text = "超難 (Expert) - Target: 50+ Turns"
	btn_expert.custom_minimum_size = Vector2(300, 50)
	btn_expert.pressed.connect(func(): select_difficulty(Difficulty.EXPERT, overlay))
	v_box.add_child(btn_expert)

func select_difficulty(diff: Difficulty, overlay: Node) -> void:
	difficulty = diff
	overlay.queue_free()
	
	# Apply configuration based on difficulty
	match difficulty:
		Difficulty.EASY:
			player_max_mana = 5
			enemy_max_hp = 60
			enemy_damage = 5
			fighter_right.text = "🐛"
			background_node.texture = load("res://Assets/Background/easy_bg.jpg")
		Difficulty.NORMAL:
			player_max_mana = 5
			enemy_max_hp = 200
			enemy_damage = 10
			fighter_right.text = "🐜"
			background_node.texture = load("res://Assets/Background/landscape.jpg")
		Difficulty.HARD:
			player_max_mana = 5
			enemy_max_hp = 400
			enemy_damage = 12
			fighter_right.text = "🕷️"
			background_node.texture = load("res://Assets/Background/hard_bg.jpg")
		Difficulty.EXPERT:
			player_max_mana = 4
			enemy_max_hp = 600
			enemy_damage = 15
			fighter_right.text = "👾"
			background_node.texture = load("res://Assets/Background/expert_bg.jpg")
			
	player_hp = player_max_hp
	enemy_hp = enemy_max_hp
	enemy_block = 0
	enemy_strength = 0
	game_turn_counter = 0
	
	end_turn_button.disabled = false
	update_ui()
	start_player_turn()

func _init_deck() -> void:
	var logs = git_parser.get_local_git_logs()
	for i in range(15):
		var log_str = logs[i % logs.size()]
		var card = git_parser.generate_card_from_log(log_str)
		# No manual overrides! Values are cleanly normalized by GitLogParser.gd
		deck_manager.add_card(card)

func start_player_turn() -> void:
	player_mana = player_max_mana
	player_block = 0
	current_combo_category = ""
	combo_count = 0
	combo_label.text = ""
	turn_timer = 30.0 # Reset turn timer on player turn start
	
	for card in hand:
		deck_manager.discard_card(card)
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
		log_action("[color=#ef4444][ERR] Not enough Tokens to play " + card.card_name + "[/color]")
		return
		
	# Pay cost
	player_mana -= card.cost
	
	# Combo Logic (Any card played builds the combo!)
	combo_count += 1
	if combo_count > 1:
		show_combo_animation(card.category)
	
	var multiplier = 1.0 + (combo_count - 1) * 0.5
	var final_damage = int(float(card.damage) * multiplier)
	
	# Apply damage taking enemy block into account
	var damage_to_deal = final_damage
	var absorbed_dmg = 0
	if enemy_block > 0 and damage_to_deal > 0:
		absorbed_dmg = min(damage_to_deal, enemy_block)
		enemy_block -= absorbed_dmg
		damage_to_deal -= absorbed_dmg
		
	if damage_to_deal > 0:
		enemy_hp -= damage_to_deal
	player_block += card.block
	
	var msg = "[color=#fde047]Played: " + card.card_name + "[/color]\n"
	if final_damage > 0: 
		if combo_count > 1:
			msg += " dealt " + str(final_damage) + " DMG. (" + str(multiplier) + "x COMBO!)"
		else:
			msg += " dealt " + str(final_damage) + " DMG."
		if absorbed_dmg > 0:
			msg += " [color=#9ca3af](Block absorbed " + str(absorbed_dmg) + " DMG)[/color]"
		shake_camera(final_damage * 0.5)
		hit_sound.play()
		animate_fighter(fighter_left, 50)
		spawn_floating_text(fighter_right.global_position + Vector2(100, 100), "-" + str(final_damage), Color(1, 0.2, 0.2))
		
	if card.block > 0: 
		msg += " gained " + str(card.block) + " Block."
		spawn_floating_text(fighter_left.global_position + Vector2(100, 100), "+" + str(card.block) + " [Block]", Color(0.2, 0.8, 1))
	
	# Play card effects based on category
	if card.category == "Performance":
		player_mana = min(player_max_mana, player_mana + 2)
		msg += " [color=#facc15][Str] Performance: Restored 2 Tokens![/color]"
	elif card.category == "Merge":
		player_hp = min(player_max_hp, player_hp + 10)
		msg += " [color=#fbbf24][Merge] Healed 10 HP![/color]"
	elif card.category == "Refactor":
		var bonus_block = int(float(final_damage) * 0.5)
		player_block += bonus_block
		msg += " [color=#60a5fa][Refactor] Gained %d Block from damage![/color]" % bonus_block
		spawn_floating_text(fighter_left.global_position + Vector2(100, 100), "+" + str(bonus_block) + " [Block]", Color(0.3, 0.6, 1.0))
	elif card.category == "Test":
		player_block += card.block # Adds another layer of block (doubling it)
		msg += " [color=#c084fc][Test] Doubled Block (+%d Block)![/color]" % card.block
	elif card.category == "Docs":
		var drawn = deck_manager.draw_card()
		if drawn != null:
			hand.append(drawn)
			msg += " [color=#22d3ee][Docs] Drew 1 card (%s).[/color]" % drawn.card_name
	elif card.category == "Style":
		player_block += 10
		msg += " [color=#f472b6][Style] Gained 10 Block![/color]"
	elif card.category == "Agent":
		enemy_hp -= 20
		msg += " [color=#a78bfa][Agent] Dealt 20 direct DMG (bypassed shields)![/color]"
		spawn_floating_text(fighter_right.global_position + Vector2(100, 100), "-20 [Agent]", Color(0.7, 0.4, 1.0))
	elif card.category == "Chore":
		var cards_to_discard = []
		for h_card in hand:
			if h_card != card:
				cards_to_discard.append(h_card)
		for h_card in cards_to_discard:
			deck_manager.discard_card(h_card)
			hand.erase(h_card)
		msg += " [color=#9ca3af][Chore] Discarded hand and drew 2 cards.[/color]"
		for i in range(2):
			var drawn = deck_manager.draw_card()
			if drawn != null:
				hand.append(drawn)

	log_action(msg)
	
	deck_manager.discard_card(card)
	hand.remove_at(hand.find(card)) # Safely find card position since Chore might have modified hand array
	update_ui()
	
	if !check_win_condition():
		# Auto end turn if player mana is 0
		if player_mana == 0:
			# Delay slightly to allow player to see the log
			await get_tree().create_timer(0.8).timeout
			if player_mana == 0: # Double check in case of state change
				_on_end_turn_pressed()

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
	# Gain Block based on difficulty
	var block_to_gain = 0
	if difficulty == Difficulty.HARD:
		block_to_gain = 5
	elif difficulty == Difficulty.EXPERT:
		block_to_gain = 10
		
	if block_to_gain > 0:
		enemy_block += block_to_gain
		log_action("[color=#a78bfa][Bug] Enemy gained " + str(block_to_gain) + " Block.[/color]")

	# Increase Strength
	game_turn_counter += 1
	var turn_interval = 3 if difficulty == Difficulty.HARD else 2
	if difficulty == Difficulty.HARD or difficulty == Difficulty.EXPERT:
		if game_turn_counter > 1 and (game_turn_counter - 1) % turn_interval == 0:
			var strength_gain = 3 if difficulty == Difficulty.HARD else 4
			enemy_strength += strength_gain
			log_action("[color=#f87171][Str+] Enemy Strength increased! Attack permanently gains +" + str(strength_gain) + " DMG.[/color]")

	var final_enemy_damage = enemy_damage + enemy_strength
	log_action("\n[b][color=#ef4444][Bug] Enemy attacks for " + str(final_enemy_damage) + " DMG![/color][/b]")
	animate_fighter(fighter_right, -50)
	
	var actual_damage = max(0, final_enemy_damage - player_block)
	player_block = max(0, player_block - final_enemy_damage)
	player_hp -= actual_damage
	
	if player_block > 0:
		log_action("[Block] absorbed " + str(min(final_enemy_damage, player_block)) + " DMG.")
		
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
		result_label.text = "[SUCCESS] DEPLOYMENT SUCCESS!"
		result_label.add_theme_color_override("font_color", Color(0.2, 1, 0.4))
	else:
		result_label.text = "[CRASH] SYSTEM CRASH"
		result_label.add_theme_color_override("font_color", Color(1, 0.2, 0.2))

func restart_game() -> void:
	game_over_overlay.visible = false
	end_turn_button.disabled = false
	player_hp = player_max_hp
	enemy_hp = enemy_max_hp
	deck_manager = DeckManager.new()
	_init_deck()
	action_log.text = "[b]Combat Log[/b]\n"
	show_difficulty_selection()

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
	player_hp_bar.max_value = float(player_max_hp)
	enemy_hp_bar.max_value = float(enemy_max_hp)

	var tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(player_hp_bar, "value", float(player_hp), 0.3)
	tween.tween_property(enemy_hp_bar, "value", float(enemy_hp), 0.3)
	
	# Update Enemy Intent to show strength and block (no emojis)
	var final_enemy_dmg = enemy_damage + enemy_strength
	var intent_text = "Intent: [Attack] %d DMG" % final_enemy_dmg
	if enemy_block > 0:
		intent_text += " | [Block] %d" % enemy_block
	if enemy_strength > 0:
		intent_text += " (+%d [Str])" % enemy_strength
	enemy_intent.text = intent_text
	
	mana_label.text = "💎 Tokens: %d/%d | 🛡️ Block: %d | 🎴 Deck: %d | 🗑️ Discard: %d" % [player_mana, player_max_mana, player_block, deck_manager.get_deck_size(), deck_manager.get_discard_size()]
	
	for child in hand_area.get_children():
		child.queue_free()
		
	var card_scene = preload("res://Scenes/UI/CardUI.tscn")
	var hand_width = hand_area.size.x if hand_area.size.x > 0 else 650.0
	var card_width = 180.0
	var total_cards = hand.size()
	
	var max_spacing = 130.0 # Widen spacing for easier selection
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
		
		# Shifted up to 10 + curve_y (was 50 + curve_y) to prevent card bottom cutoff
		card_ui.position = Vector2(target_x, 10 + curve_y)
		card_ui.rotation_degrees = rotation_deg
		card_ui.original_y = card_ui.position.y # Save for hover tween
		
		card_ui.setup(card, i)
		card_ui.pressed.connect(func(): play_card(card_ui.card_index))
		card_ui.animate_draw(card_ui.position)
