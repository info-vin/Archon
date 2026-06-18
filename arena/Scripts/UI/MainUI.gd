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

var config: Resource = preload("res://Scripts/Resources/GameConfig.tres")

# Turn Timer & Help system
var turn_timer: float
var timer_label: Label
var help_overlay: Control = null

var cjk_font: Font

# Dynamic vector icon HUD elements
var hud_container: TokenHud

# Dynamic textures and HP overlays
@onready var player_name = $UILayer/UIRoot/PlayerHUD/PlayerName
@onready var enemy_name = $UILayer/UIRoot/EnemyHUD/EnemyName
var player_avatar: TextureRect
var enemy_avatar: TextureRect
var player_hp_text: Label
var enemy_hp_text: Label

func _ready() -> void:
	cjk_font = load(config.cjk_font_path)
	hit_sound = MainUIHelpers.create_sound(self, config.hit_sound_path)
	error_sound = MainUIHelpers.create_sound(self, config.error_sound_path)
	turn_timer = config.turn_timer_seconds
	
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
	
	# Hide legacy components
	mana_label.visible = false
	end_turn_button.visible = false
	fighter_left.visible = false
	fighter_right.visible = false
	
	# Dynamically assemble HUD
	var TokenHudScript = preload("res://Scripts/UI/TokenHud.gd")
	hud_container = TokenHudScript.new()
	hud_container.setup_hud(cjk_font)
	$UILayer/UIRoot/PlayerHUD.add_child(hud_container)
	
	player_name.text = "專案主管 (Tech Lead)"
	player_name.add_theme_font_override("font", cjk_font)
	enemy_name.add_theme_font_override("font", cjk_font)
	
	# Setup avatars
	player_avatar = MainUIHelpers.create_avatar(self, config.player_avatar_path, Vector2(87, 150))
	enemy_avatar = MainUIHelpers.create_avatar(self, "", Vector2(819, 150))
	
	# Configure HP texts
	player_hp_text = MainUIHelpers.create_hp_text(player_hp_bar, cjk_font)
	enemy_hp_text = MainUIHelpers.create_hp_text(enemy_hp_bar, cjk_font)
	
	# Create turn timer label
	timer_label = Label.new()
	timer_label.text = str(int(config.turn_timer_seconds)) + "s"
	timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	timer_label.add_theme_font_size_override("font_size", config.timer_font_size_normal)
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
		turn_timer = config.turn_timer_seconds
		_on_end_turn_pressed()
	else:
		var display_time = ceil(turn_timer)
		timer_label.text = str(display_time) + "s"
		if display_time <= 5:
			timer_label.add_theme_font_size_override("font_size", config.timer_font_size_alert)
			timer_label.add_theme_color_override("font_color", Color(1.0, 0.2, 0.2))
		else:
			timer_label.add_theme_font_size_override("font_size", config.timer_font_size_normal)
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
	var overlay_mgr = load("res://Scripts/UI/OverlayManager.gd")
	help_overlay = overlay_mgr.show_help_overlay(self, cjk_font)
	help_overlay.closed.connect(func(): help_overlay = null)

func hide_help_overlay() -> void:
	var overlay_mgr = load("res://Scripts/UI/OverlayManager.gd")
	overlay_mgr.hide_help_overlay(help_overlay)
	help_overlay = null

func show_difficulty_selection() -> void:
	end_turn_button.disabled = true
	var overlay_mgr = load("res://Scripts/UI/OverlayManager.gd")
	overlay_mgr.show_difficulty_selection(self, cjk_font, Callable(self, "select_difficulty"))

func select_difficulty(diff: int) -> void:
	match diff:
		0: # EASY
			enemy_name.text = "程式缺陷 (Bug - Easy)"
			enemy_avatar.texture = load(config.bug_easy_path)
			background_node.texture = load(config.bg_easy_path)
		1: # NORMAL
			enemy_name.text = "程式錯誤 (Bug - Normal)"
			enemy_avatar.texture = load(config.bug_normal_path)
			background_node.texture = load(config.bg_normal_path)
		2: # HARD
			enemy_name.text = "系統漏洞 (Bug - Hard)"
			enemy_avatar.texture = load(config.bug_hard_path)
			background_node.texture = load(config.bg_hard_path)
		3: # EXPERT
			enemy_name.text = "核心崩潰 (Bug - Expert)"
			enemy_avatar.texture = load(config.bug_expert_path)
			background_node.texture = load(config.bg_expert_path)
			
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
		CombatVFX.shake_camera(self, camera, 5.0)
		error_sound.play()
		log_action("[color=#ef4444][ERR] Not enough Tokens to play " + card.card_name + "[/color]")
		return
		
	if card.damage > 0:
		CombatVFX.animate_fighter(self, player_avatar, 50)
		
	game_state.play_card(card)

func _on_end_turn_pressed() -> void:
	if game_over_overlay.visible or end_turn_button.disabled:
		return
	log_action("Player ended turn.")
	game_state.enemy_turn()

func show_game_over(win: bool) -> void:
	end_turn_button.disabled = true
	GameOverHelper.show(self, game_over_overlay, result_label, restart_button, win)

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

func _on_player_hp_changed(current_hp: int, max_hp: int) -> void:
	MainUIHelpers.update_hp_bar(self, player_hp_bar, player_hp_text, current_hp, max_hp)

func _on_enemy_hp_changed(current_hp: int, max_hp: int) -> void:
	MainUIHelpers.update_hp_bar(self, enemy_hp_bar, enemy_hp_text, current_hp, max_hp)

func _on_player_block_changed(current_block: int) -> void:
	if hud_container and hud_container.block_label:
		hud_container.block_label.text = str(current_block)

func _on_enemy_block_changed(current_block: int) -> void:
	_update_enemy_intent()

func _on_mana_changed(current_mana: int, max_mana: int) -> void:
	if hud_container and hud_container.token_label:
		hud_container.token_label.text = "%d/%d" % [current_mana, max_mana]

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
	CombatVFX.shake_camera(self, camera, 15.0)
	hit_sound.play()
	CombatVFX.animate_fighter(self, player_avatar, -50)
	CombatVFX.spawn_floating_text(self, $UILayer, player_avatar.global_position + Vector2(100, 100), "-" + str(amount), Color(1, 0.2, 0.2))

func _on_enemy_took_damage(amount: int) -> void:
	CombatVFX.shake_camera(self, camera, amount * 0.5)
	hit_sound.play()
	CombatVFX.spawn_floating_text(self, $UILayer, enemy_avatar.global_position + Vector2(100, 100), "-" + str(amount), Color(1, 0.2, 0.2))

func _on_player_gained_block(amount: int) -> void:
	CombatVFX.spawn_floating_text(self, $UILayer, player_avatar.global_position + Vector2(100, 100), "+" + str(amount) + " [Block]", Color(0.2, 0.8, 1))

func _update_enemy_intent() -> void:
	var final_enemy_dmg = game_state.enemy_damage + game_state.enemy_strength
	var intent_text = "Intent: [Attack] %d DMG" % final_enemy_dmg
	if game_state.enemy_block > 0:
		intent_text += " | [Block] %d" % game_state.enemy_block
	if game_state.enemy_strength > 0:
		intent_text += " (+%d [Str])" % game_state.enemy_strength
	enemy_intent.text = intent_text

func update_hand_ui() -> void:
	if hud_container:
		hud_container.update_values(
			game_state.player_mana,
			game_state.player_max_mana,
			game_state.player_block,
			deck_manager.get_deck_size(),
			deck_manager.get_discard_size()
		)
	
	_update_enemy_intent()
	
	# Clean turn timer when player hand is updated (turn start)
	if config and config.get("turn_timer_seconds") != null:
		turn_timer = config.get("turn_timer_seconds")
	else:
		turn_timer = 30.0
	
	var hand_controller = load("res://Scripts/UI/HandController.gd")
	hand_controller.render_hand(hand_area, game_state, config, Callable(self, "play_card"))
