extends Node2D

var deck_manager: DeckManager
var git_parser: GitLogParser
var game_state: GameState

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
	
	# Initialize GameState
	game_state = preload("res://Scripts/Logic/GameState.gd").new()
	game_state.deck_manager = deck_manager
	game_state.git_parser = git_parser
	
	# Connect signals
	game_state.player_hp_changed.connect(_on_player_hp_changed)
	game_state.enemy_hp_changed.connect(_on_enemy_hp_changed)
	game_state.player_block_changed.connect(_on_player_block_changed)
	game_state.enemy_block_changed.connect(_on_enemy_block_changed)
	game_state.mana_changed.connect(_on_mana_changed)
	game_state.combo_changed.connect(_on_combo_changed)
	game_state.log_event.connect(log_action)
	game_state.game_over_triggered.connect(show_game_over)
	game_state.smart_end_turn_triggered.connect(_on_end_turn_pressed)
	game_state.draw_finished.connect(update_hand_ui)
	
	# Connect juice signals
	game_state.player_took_damage.connect(_on_player_took_damage)
	game_state.enemy_took_damage.connect(_on_enemy_took_damage)
	game_state.player_gained_block.connect(_on_player_gained_block)
	
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
	player_avatar.custom_minimum_size = Vector2(216, 324)
	player_avatar.size = Vector2(216, 324)
	player_avatar.position = Vector2(87, 150)
	player_avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	player_avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	player_avatar.texture = load("res://Assets/Images/player_lead.png")
	$UILayer/UIRoot.add_child(player_avatar)
	$UILayer/UIRoot.move_child(player_avatar, 0)
	
	enemy_avatar = TextureRect.new()
	enemy_avatar.custom_minimum_size = Vector2(216, 324)
	enemy_avatar.size = Vector2(216, 324)
	enemy_avatar.position = Vector2(819, 150)
	enemy_avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	enemy_avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	$UILayer/UIRoot.add_child(enemy_avatar)
	$UILayer/UIRoot.move_child(enemy_avatar, 0)
	
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
			timer_label.add_theme_font_size_override("font_size", 88)
			timer_label.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
		else:
			timer_label.add_theme_font_size_override("font_size", 64)
			timer_label.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
			
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
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
	end_turn_button.disabled = true
	
	var overlay = ColorRect.new()
	overlay.name = "DifficultyOverlay"
	overlay.color = Color(0, 0, 0, 0.8)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	$UILayer/UIRoot.add_child(overlay)
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	
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
	btn_easy.pressed.connect(func(): select_difficulty(0, overlay))
	btn_easy.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_easy)
	
	var btn_normal = Button.new()
	btn_normal.text = "普通 (Normal) - Target: ~8 Turns"
	btn_normal.custom_minimum_size = Vector2(300, 50)
	btn_normal.pressed.connect(func(): select_difficulty(1, overlay))
	btn_normal.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_normal)
	
	var btn_hard = Button.new()
	btn_hard.text = "困難 (Hard) - Target: 20-50 Turns"
	btn_hard.custom_minimum_size = Vector2(300, 50)
	btn_hard.pressed.connect(func(): select_difficulty(2, overlay))
	btn_hard.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_hard)
	
	var btn_expert = Button.new()
	btn_expert.text = "超難 (Expert) - Target: 50+ Turns"
	btn_expert.custom_minimum_size = Vector2(300, 50)
	btn_expert.pressed.connect(func(): select_difficulty(3, overlay))
	btn_expert.add_theme_font_override("font", cjk_font)
	v_box.add_child(btn_expert)

func select_difficulty(diff: int, overlay: Node) -> void:
	overlay.queue_free()
	
	match diff:
		0: # EASY
			enemy_name.text = "程式缺陷 (Bug - Easy)"
			enemy_avatar.texture = load("res://Assets/Images/bug_easy.png")
			background_node.texture = load("res://Assets/Background/easy_bg.jpg")
		1: # NORMAL
			enemy_name.text = "程式錯誤 (Bug - Normal)"
			enemy_avatar.texture = load("res://Assets/Images/bug_normal.png")
			background_node.texture = load("res://Assets/Background/landscape.jpg")
		2: # HARD
			enemy_name.text = "系統漏洞 (Bug - Hard)"
			enemy_avatar.texture = load("res://Assets/Images/bug_hard.png")
			background_node.texture = load("res://Assets/Background/hard_bg.jpg")
		3: # EXPERT
			enemy_name.text = "核心崩潰 (Bug - Expert)"
			enemy_avatar.texture = load("res://Assets/Images/bug_expert.png")
			background_node.texture = load("res://Assets/Background/expert_bg.jpg")
			
	game_state.select_difficulty(diff)
	end_turn_button.disabled = false
	game_state.start_player_turn()

func _init_deck() -> void:
	var logs = git_parser.get_local_git_logs()
	for i in range(15):
		var log_str = logs[i % logs.size()]
		var card = git_parser.generate_card_from_log(log_str)
		deck_manager.add_card(card)

func play_card(index: int) -> void:
	if index >= game_state.hand.size(): return
	var card = game_state.hand[index]
	
	if game_state.player_mana < card.cost:
		shake_camera(5.0)
		error_sound.play()
		log_action("[color=#ef4444][ERR] Not enough Tokens to play " + card.card_name + "[/color]")
		return
		
	if card.damage > 0:
		animate_fighter(player_avatar, 50)
		
	game_state.play_card(card)

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

func animate_fighter(fighter: Node, distance: float):
	var tween = create_tween().set_trans(Tween.TRANS_ELASTIC)
	var original_pos = fighter.position
	tween.tween_property(fighter, "position:x", original_pos.x + distance, 0.1)
	tween.tween_property(fighter, "position:x", original_pos.x, 0.3)

func _on_end_turn_pressed() -> void:
	if game_over_overlay.visible or end_turn_button.disabled:
		return
	log_action("Player ended turn.")
	game_state.enemy_turn()

func show_game_over(win: bool) -> void:
	end_turn_button.disabled = true
	game_over_overlay.visible = true
	
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
	deck_manager = DeckManager.new()
	_init_deck()
	game_state.deck_manager = deck_manager
	game_state.hand.clear()
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

func _on_player_hp_changed(current_hp: int, max_hp: int) -> void:
	player_hp_bar.max_value = float(max_hp)
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(player_hp_bar, "value", float(current_hp), 0.3)
	if player_hp_text:
		player_hp_text.text = "%d / %d HP" % [current_hp, max_hp]

func _on_enemy_hp_changed(current_hp: int, max_hp: int) -> void:
	enemy_hp_bar.max_value = float(max_hp)
	var tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(enemy_hp_bar, "value", float(current_hp), 0.3)
	if enemy_hp_text:
		enemy_hp_text.text = "%d / %d HP" % [current_hp, max_hp]

func _on_player_block_changed(current_block: int) -> void:
	block_label.text = str(current_block)

func _on_enemy_block_changed(current_block: int) -> void:
	_update_enemy_intent()

func _on_mana_changed(current_mana: int, max_mana: int) -> void:
	token_label.text = "%d/%d" % [current_mana, max_mana]

func _on_combo_changed(combo_count: int, combo_category: String) -> void:
	if combo_count > 1:
		var multiplier = 1.0 + (combo_count - 1) * 0.5
		combo_label.text = str(multiplier) + "x COMBO!"
		combo_label.pivot_offset = combo_label.size / 2
		var tween = create_tween().set_trans(Tween.TRANS_SPRING)
		tween.tween_property(combo_label, "scale", Vector2(1.5, 1.5), 0.2).from(Vector2(0.5, 0.5))
		tween.tween_property(combo_label, "scale", Vector2(1, 1), 0.2)
	else:
		combo_label.text = ""

func _on_player_took_damage(amount: int) -> void:
	shake_camera(15.0)
	hit_sound.play()
	animate_fighter(player_avatar, -50)
	spawn_floating_text(player_avatar.global_position + Vector2(100, 100), "-" + str(amount), Color(1, 0.2, 0.2))

func _on_enemy_took_damage(amount: int) -> void:
	shake_camera(amount * 0.5)
	hit_sound.play()
	spawn_floating_text(enemy_avatar.global_position + Vector2(100, 100), "-" + str(amount), Color(1, 0.2, 0.2))

func _on_player_gained_block(amount: int) -> void:
	spawn_floating_text(player_avatar.global_position + Vector2(100, 100), "+" + str(amount) + " [Block]", Color(0.2, 0.8, 1))

func _update_enemy_intent() -> void:
	var final_enemy_dmg = game_state.enemy_damage + game_state.enemy_strength
	var intent_text = "Intent: [Attack] %d DMG" % final_enemy_dmg
	if game_state.enemy_block > 0:
		intent_text += " | [Block] %d" % game_state.enemy_block
	if game_state.enemy_strength > 0:
		intent_text += " (+%d [Str])" % game_state.enemy_strength
	enemy_intent.text = intent_text

func update_hand_ui() -> void:
	token_label.text = "%d/%d" % [game_state.player_mana, game_state.player_max_mana]
	block_label.text = str(game_state.player_block)
	deck_label.text = str(deck_manager.get_deck_size())
	discard_label.text = str(deck_manager.get_discard_size())
	
	_update_enemy_intent()
	
	# Clean turn timer when player hand is updated (turn start)
	turn_timer = 30.0
	
	for child in hand_area.get_children():
		child.queue_free()
		
	var card_scene = preload("res://Scenes/UI/CardUI.tscn")
	var hand_width = hand_area.size.x if hand_area.size.x > 0 else 650.0
	var card_width = 180.0
	var total_cards = game_state.hand.size()
	
	var max_spacing = 130.0
	var required_width = card_width + (total_cards - 1) * max_spacing
	var spacing = max_spacing
	if required_width > hand_width:
		spacing = (hand_width - card_width) / max(1, total_cards - 1)
	if total_cards <= 1: spacing = 0
	
	var total_width = card_width + (total_cards - 1) * spacing
	var start_x = (hand_width - total_width) / 2.0
	
	for i in range(total_cards):
		var card = game_state.hand[i]
		var card_ui = card_scene.instantiate()
		hand_area.add_child(card_ui)
		
		var target_x = start_x + (i * spacing)
		
		var t = 0.5 if total_cards <= 1 else float(i) / float(total_cards - 1)
		var curve_y = abs(t - 0.5) * abs(t - 0.5) * 150.0
		var rotation_deg = lerpf(-15.0, 15.0, t)
		
		card_ui.position = Vector2(target_x, 10 + curve_y)
		card_ui.rotation_degrees = rotation_deg
		card_ui.original_y = card_ui.position.y
		
		card_ui.setup(card, i)
		card_ui.pressed.connect(func(): play_card(card_ui.card_index))
		card_ui.animate_draw(card_ui.position)
