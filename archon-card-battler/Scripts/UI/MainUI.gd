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

var cjk_font = preload("res://Assets/Fonts/arial_unicode.ttf")

# Dynamic vector icon HUD elements
var hud_container: HBoxContainer
var token_icon: VectorIcon
var token_label: Label
var block_icon: VectorIcon
var block_label: Label
var deck_icon: VectorIcon
var deck_label: Label
var discard_icon: VectorIcon
var discard_label: Label

# Dynamic textures and HP overlays
@onready var player_name = $UILayer/UIRoot/PlayerHUD/PlayerName
@onready var enemy_name = $UILayer/UIRoot/EnemyHUD/EnemyName
var player_avatar: TextureRect
var enemy_avatar: TextureRect
var player_hp_text: Label
var enemy_hp_text: Label

func _ready() -> void:
	hit_sound = AudioStreamPlayer.new()
	hit_sound.stream = preload("res://Assets/Sounds/hit.wav")
	add_child(hit_sound)
	
	error_sound = AudioStreamPlayer.new()
	error_sound.stream = preload("res://Assets/Sounds/error.wav")
	add_child(error_sound)
	
	# Apply CJK font to all controls displaying Traditional Chinese
	action_log.add_theme_font_override("normal_font", cjk_font)
	action_log.add_theme_font_override("bold_font", cjk_font)
	action_log.add_theme_font_override("italics_font", cjk_font)
	action_log.add_theme_font_override("bold_italics_font", cjk_font)
	
	mana_label.add_theme_font_override("font", cjk_font)
	enemy_intent.add_theme_font_override("font", cjk_font)
	result_label.add_theme_font_override("font", cjk_font)
	restart_button.add_theme_font_override("font", cjk_font)
	
	deck_manager = DeckManager.new()
	git_parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	
	_init_deck()
	
	end_turn_button.pressed.connect(_on_end_turn_pressed)
	restart_button.pressed.connect(restart_game)
	
	# Hide legacy mana label
	mana_label.visible = false
	
	# Dynamically assemble the premium Vector HUD layout
	hud_container = HBoxContainer.new()
	hud_container.add_theme_constant_override("separation", 12)
	
	var VectorIconScript = preload("res://Scripts/UI/VectorIcon.gd")
	
	# 1. Tokens
	token_icon = VectorIconScript.new()
	token_icon.type = VectorIcon.IconType.TOKEN
	token_icon.color = Color(0.0, 0.8, 1.0)
	token_icon.custom_minimum_size = Vector2(18, 18)
	hud_container.add_child(token_icon)
	
	token_label = Label.new()
	token_label.add_theme_font_override("font", cjk_font)
	token_label.add_theme_font_size_override("font_size", 16)
	hud_container.add_child(token_label)
	
	# Separator 1
	var sep1 = Label.new()
	sep1.text = "|"
	sep1.add_theme_font_override("font", cjk_font)
	sep1.add_theme_font_size_override("font_size", 16)
	sep1.modulate = Color(0.3, 0.3, 0.3)
	hud_container.add_child(sep1)
	
	# 2. Block
	block_icon = VectorIconScript.new()
	block_icon.type = VectorIcon.IconType.BLOCK
	block_icon.color = Color(0.2, 0.9, 0.6)
	block_icon.custom_minimum_size = Vector2(18, 18)
	hud_container.add_child(block_icon)
	
	block_label = Label.new()
	block_label.add_theme_font_override("font", cjk_font)
	block_label.add_theme_font_size_override("font_size", 16)
	hud_container.add_child(block_label)
	
	# Separator 2
	var sep2 = Label.new()
	sep2.text = "|"
	sep2.add_theme_font_override("font", cjk_font)
	sep2.add_theme_font_size_override("font_size", 16)
	sep2.modulate = Color(0.3, 0.3, 0.3)
	hud_container.add_child(sep2)
	
	# 3. Deck
	deck_icon = VectorIconScript.new()
	deck_icon.type = VectorIcon.IconType.DECK
	deck_icon.color = Color(1.0, 0.8, 0.2)
	deck_icon.custom_minimum_size = Vector2(18, 18)
	hud_container.add_child(deck_icon)
	
	deck_label = Label.new()
	deck_label.add_theme_font_override("font", cjk_font)
	deck_label.add_theme_font_size_override("font_size", 16)
	hud_container.add_child(deck_label)
	
	# Separator 3
	var sep3 = Label.new()
	sep3.text = "|"
	sep3.add_theme_font_override("font", cjk_font)
	sep3.add_theme_font_size_override("font_size", 16)
	sep3.modulate = Color(0.3, 0.3, 0.3)
	hud_container.add_child(sep3)
	
	# 4. Discard
	discard_icon = VectorIconScript.new()
	discard_icon.type = VectorIcon.IconType.DISCARD
	discard_icon.color = Color(1.0, 0.4, 0.4)
	discard_icon.custom_minimum_size = Vector2(18, 18)
	hud_container.add_child(discard_icon)
	
	discard_label = Label.new()
	discard_label.add_theme_font_override("font", cjk_font)
	discard_label.add_theme_font_size_override("font_size", 16)
	hud_container.add_child(discard_label)
	
	$UILayer/UIRoot/PlayerHUD.add_child(hud_container)

	
	# Hide the End Turn button as requested (shortcut Space/Enter and auto-timer will handle it)
	end_turn_button.visible = false
	
	# Update HUD Names to CJK Traditional Chinese
	player_name.text = "專案主管 (Tech Lead)"
	player_name.add_theme_font_override("font", cjk_font)
	enemy_name.add_theme_font_override("font", cjk_font)
	
	# Hide legacy text fighter labels
	fighter_left.visible = false
	fighter_right.visible = false
	
	# Initialize premium 9:16 character image TextureRect nodes dynamically
	player_avatar = TextureRect.new()
	player_avatar.custom_minimum_size = Vector2(120, 180)
	player_avatar.size = Vector2(120, 180)
	player_avatar.position = Vector2(20, 130)
	player_avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	player_avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	player_avatar.texture = load("res://Assets/Images/player_lead.png")
	$UILayer/UIRoot.add_child(player_avatar)
	
	enemy_avatar = TextureRect.new()
	enemy_avatar.custom_minimum_size = Vector2(120, 180)
	enemy_avatar.size = Vector2(120, 180)
	enemy_avatar.position = Vector2(982, 130)
	enemy_avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	enemy_avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	$UILayer/UIRoot.add_child(enemy_avatar)
	
	# Configure absolute numeric HP text overlays on progress bars
	player_hp_bar.show_percentage = false
	player_hp_text = Label.new()
	player_hp_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	player_hp_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	player_hp_text.add_theme_font_override("font", cjk_font)
	player_hp_text.add_theme_font_size_override("font_size", 16)
	player_hp_text.add_theme_color_override("font_color", Color(1, 1, 1))
	player_hp_bar.add_child(player_hp_text)
	player_hp_text.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	enemy_hp_bar.show_percentage = false
	enemy_hp_text = Label.new()
	enemy_hp_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	enemy_hp_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	enemy_hp_text.add_theme_font_override("font", cjk_font)
	enemy_hp_text.add_theme_font_size_override("font_size", 16)
	enemy_hp_text.add_theme_color_override("font_color", Color(1, 1, 1))
	enemy_hp_bar.add_child(enemy_hp_text)
	enemy_hp_text.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	# Create turn timer label in the middle of health bars (size 64)
	timer_label = Label.new()
	timer_label.text = "30s"
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	timer_label.add_theme_font_size_override("font_size", 64)
	timer_label.position = Vector2(576 - 120, 15)
	timer_label.size = Vector2(240, 120)
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
			# Enlarged 2x font size for last 5 seconds and color red
			timer_label.add_theme_font_size_override("font_size", 88)
			timer_label.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
		else:
			# Normal 2x font size
			timer_label.add_theme_font_size_override("font_size", 64)
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
	help_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	$UILayer/UIRoot.add_child(help_overlay)
	help_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	# Wrap in CenterContainer for perfect centering in browser WASM exports
	var center_container = CenterContainer.new()
	help_overlay.add_child(center_container)
	center_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	var v_box = VBoxContainer.new()
	v_box.alignment = BoxContainer.ALIGNMENT_CENTER
	v_box.add_theme_constant_override("separation", 15)
	center_container.add_child(v_box)
	
	var title = Label.new()
	title.text = "遊戲說明 (GAME MANUAL)"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 28)
	title.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	title.add_theme_font_override("font", cjk_font)
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
	rules.add_theme_font_override("font", cjk_font)
	v_box.add_child(rules)
	
	var close_btn = Button.new()
	close_btn.text = "關閉說明 (ESC)"
	close_btn.custom_minimum_size = Vector2(200, 40)
	close_btn.pressed.connect(hide_help_overlay)
	close_btn.add_theme_font_override("font", cjk_font)
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
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	$UILayer/UIRoot.add_child(overlay)
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	# Wrap in CenterContainer for perfect centering in browser WASM exports
	var center_container = CenterContainer.new()
	overlay.add_child(center_container)
	center_container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
	var v_box = VBoxContainer.new()
	v_box.alignment = BoxContainer.ALIGNMENT_CENTER
	v_box.add_theme_constant_override("separation", 20)
	center_container.add_child(v_box)
	
	var title = Label.new()
	title.text = "SELECT DIFFICULTY / 選擇難度"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 40)
	title.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0))
	title.add_theme_font_override("font", cjk_font)
	v_box.add_child(title)
	
	var desc = Label.new()
	desc.text = "（難度將影響敵人的血量、每回合自動增加的護盾與隨時間成長的力量）"
	desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	desc.add_theme_font_size_override("font_size", 16)
	desc.add_theme_font_override("font", cjk_font)
	v_box.add_child(desc)
	
	var btn_easy = Button.new()
	btn_easy.text = "簡單 (Easy) - Target: <5 Turns"
	btn_easy.custom_minimum_size = Vector2(300, 50)
	btn_easy.pressed.connect(func(): select_difficulty(Difficulty.EASY, overlay))
	btn_easy.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_easy)
	
	var btn_normal = Button.new()
	btn_normal.text = "普通 (Normal) - Target: ~8 Turns"
	btn_normal.custom_minimum_size = Vector2(300, 50)
	btn_normal.pressed.connect(func(): select_difficulty(Difficulty.NORMAL, overlay))
	btn_normal.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_normal)
	
	var btn_hard = Button.new()
	btn_hard.text = "困難 (Hard) - Target: 20-50 Turns"
	btn_hard.custom_minimum_size = Vector2(300, 50)
	btn_hard.pressed.connect(func(): select_difficulty(Difficulty.HARD, overlay))
	btn_hard.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_hard)
	
	var btn_expert = Button.new()
	btn_expert.text = "超難 (Expert) - Target: 50+ Turns"
	btn_expert.custom_minimum_size = Vector2(300, 50)
	btn_expert.pressed.connect(func(): select_difficulty(Difficulty.EXPERT, overlay))
	btn_expert.add_theme_font_override("font", cjk_font)
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
			enemy_name.text = "程式缺陷 (Bug - Easy)"
			enemy_avatar.texture = load("res://Assets/Images/bug_easy.png")
			background_node.texture = load("res://Assets/Background/easy_bg.jpg")
		Difficulty.NORMAL:
			player_max_mana = 5
			enemy_max_hp = 200
			enemy_damage = 10
			enemy_name.text = "程式錯誤 (Bug - Normal)"
			enemy_avatar.texture = load("res://Assets/Images/bug_normal.png")
			background_node.texture = load("res://Assets/Background/landscape.jpg")
		Difficulty.HARD:
			player_max_mana = 5
			enemy_max_hp = 400
			enemy_damage = 12
			enemy_name.text = "系統漏洞 (Bug - Hard)"
			enemy_avatar.texture = load("res://Assets/Images/bug_hard.png")
			background_node.texture = load("res://Assets/Background/hard_bg.jpg")
		Difficulty.EXPERT:
			player_max_mana = 4
			enemy_max_hp = 600
			enemy_damage = 15
			enemy_name.text = "核心崩潰 (Bug - Expert)"
			enemy_avatar.texture = load("res://Assets/Images/bug_expert.png")
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
		animate_fighter(player_avatar, 50)
		spawn_floating_text(enemy_avatar.global_position + Vector2(100, 100), "-" + str(final_damage), Color(1, 0.2, 0.2))
		
	if card.block > 0: 
		msg += " gained " + str(card.block) + " Block."
		spawn_floating_text(player_avatar.global_position + Vector2(100, 100), "+" + str(card.block) + " [Block]", Color(0.2, 0.8, 1))
	
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
		spawn_floating_text(player_avatar.global_position + Vector2(100, 100), "+" + str(bonus_block) + " [Block]", Color(0.3, 0.6, 1.0))
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
		spawn_floating_text(enemy_avatar.global_position + Vector2(100, 100), "-20 [Agent]", Color(0.7, 0.4, 1.0))
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
		# Smart auto end turn: if mana is lower than cost of any card in hand
		check_smart_end_turn()

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
	if game_over_overlay.visible or end_turn_button.disabled:
		return
	log_action("Player ended turn.")
	enemy_turn()

func enemy_turn() -> void:
	if game_over_overlay.visible or end_turn_button.disabled:
		return
		
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
	animate_fighter(enemy_avatar, -50)
	
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

# Helper for smart turn ending
func check_smart_end_turn() -> void:
	if hand.is_empty():
		await get_tree().create_timer(0.8).timeout
		if hand.is_empty():
			_on_end_turn_pressed()
		return
		
	var min_cost = 99
	for card in hand:
		if card.cost < min_cost:
			min_cost = card.cost
			
	if player_mana < min_cost:
		await get_tree().create_timer(0.8).timeout
		# Recheck in case mana/hand altered during delay
		var recheck_min_cost = 99
		for card in hand:
			if card.cost < recheck_min_cost:
				recheck_min_cost = card.cost
		if hand.is_empty() or player_mana < recheck_min_cost:
			_on_end_turn_pressed()

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
	
	# Centering and widening the result VBox Container to span full width and height
	var vbox = $TopLayer/GameOverOverlay/VBox
	vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	vbox.offset_left = 0
	vbox.offset_right = 0
	vbox.offset_top = 0
	vbox.offset_bottom = 0
	vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	
	result_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	result_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	result_label.add_theme_font_size_override("font_size", 48)
	
	restart_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	
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
	
	if player_hp_text:
		player_hp_text.text = "%d / %d HP" % [player_hp, player_max_hp]
	if enemy_hp_text:
		enemy_hp_text.text = "%d / %d HP" % [enemy_hp, enemy_max_hp]
	
	# Update Enemy Intent to show strength and block (no emojis)
	var final_enemy_dmg = enemy_damage + enemy_strength
	var intent_text = "Intent: [Attack] %d DMG" % final_enemy_dmg
	if enemy_block > 0:
		intent_text += " | [Block] %d" % enemy_block
	if enemy_strength > 0:
		intent_text += " (+%d [Str])" % enemy_strength
	enemy_intent.text = intent_text
	
	token_label.text = "%d/%d" % [player_mana, player_max_mana]
	block_label.text = str(player_block)
	deck_label.text = str(deck_manager.get_deck_size())
	discard_label.text = str(deck_manager.get_discard_size())
	
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
