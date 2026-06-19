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

# Decoupled Controllers
var timer_ui
var hud_controller
var combat_juice: Node
var help_overlay: Control = null

var cjk_font: Font
var hud_container: TokenHud

@onready var player_name = $UILayer/UIRoot/PlayerHUD/PlayerName
@onready var enemy_name = $UILayer/UIRoot/EnemyHUD/EnemyName
var player_avatar: TextureRect
var enemy_avatar: TextureRect
var player_hp_text: Label
var enemy_hp_text: Label
var turn_label: Label

func _ready() -> void:
	cjk_font = load(config.cjk_font_path)
	_setup_audio()
	_setup_ui_overrides()
	_setup_game_controllers()
	_setup_hud_and_avatars()
	show_difficulty_selection()

func _setup_audio() -> void:
	hit_sound = MainUIHelpers.create_sound(self, config.hit_sound_path)
	error_sound = MainUIHelpers.create_sound(self, config.error_sound_path)

func _setup_ui_overrides() -> void:
	action_log.add_theme_font_override("normal_font", cjk_font)
	action_log.add_theme_font_override("bold_font", cjk_font)
	action_log.add_theme_font_override("italics_font", cjk_font)
	action_log.add_theme_font_override("bold_italics_font", cjk_font)
	
	mana_label.add_theme_font_override("font", cjk_font)
	combo_label.add_theme_font_override("font", cjk_font)
	enemy_intent.add_theme_font_override("font", cjk_font)
	result_label.add_theme_font_override("font", cjk_font)
	restart_button.add_theme_font_override("font", cjk_font)
	
	mana_label.visible = false
	end_turn_button.visible = false
	fighter_left.visible = false
	fighter_right.visible = false

func _setup_game_controllers() -> void:
	deck_manager = DeckManager.new()
	git_parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	
	game_state = preload("res://Scripts/Logic/GameState.gd").new()
	game_state.deck_manager = deck_manager
	game_state.git_parser = git_parser
	
	# Connect Model flow signals
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
	game_state.turn_changed.connect(_on_turn_changed)

	# Instantiate and setup CombatJuice
	var CombatJuiceScript = preload("res://Scripts/UI/CombatJuice.gd")
	combat_juice = CombatJuiceScript.new()
	add_child(combat_juice)
	combat_juice.setup(self, hit_sound, error_sound)

	# Connect juice signals
	game_state.player_took_damage.connect(combat_juice.handle_player_damaged)
	game_state.enemy_took_damage.connect(combat_juice.handle_enemy_damaged)
	game_state.player_gained_block.connect(combat_juice.handle_player_gained_block)

	var DeckControllerScript = preload("res://Scripts/Logic/DeckController.gd")
	DeckControllerScript.initialize_deck(deck_manager, git_parser)
	
	end_turn_button.pressed.connect(_on_end_turn_pressed)
	restart_button.pressed.connect(restart_game)

func _setup_hud_and_avatars() -> void:
	var TokenHudScript = preload("res://Scripts/UI/TokenHud.gd")
	hud_container = TokenHudScript.new()
	hud_container.setup_hud(cjk_font)
	$UILayer/UIRoot/PlayerHUD.add_child(hud_container)
	
	player_name.text = "專案主管 (Tech Lead)"
	player_name.add_theme_font_override("font", cjk_font)
	enemy_name.add_theme_font_override("font", cjk_font)

	player_avatar = MainUIHelpers.create_avatar($UILayer/UIRoot, config.player_avatar_path, Vector2(87, 150))
	enemy_avatar = MainUIHelpers.create_avatar($UILayer/UIRoot, "", Vector2(819, 150))

	player_hp_text = MainUIHelpers.create_hp_text(player_hp_bar, cjk_font)
	enemy_hp_text = MainUIHelpers.create_hp_text(enemy_hp_bar, cjk_font)
	
	turn_label = Label.new()
	turn_label.text = "第 1 回合 (Turn 1)"
	turn_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	turn_label.add_theme_font_override("font", cjk_font)
	turn_label.add_theme_font_size_override("font_size", 24)
	turn_label.position = Vector2(576 - 120, 80) 
	turn_label.size = Vector2(240, 40)
	$UILayer/UIRoot.add_child(turn_label)
	
	timer_ui = preload("res://Scripts/UI/TimerUI.gd").new()
	timer_ui.setup(config, config.turn_timer_seconds)
	$UILayer/UIRoot.add_child(timer_ui)
	
	hud_controller = preload("res://Scripts/UI/HUDController.gd").new()
	hud_controller.setup(player_hp_bar, enemy_hp_bar, player_hp_text, enemy_hp_text, turn_label, enemy_intent, hud_container)

func _process(delta: float) -> void:
	if end_turn_button.disabled or game_over_overlay.visible:
		timer_ui.visible = false
		turn_label.visible = false
		return

	timer_ui.visible = true
	turn_label.visible = true
	
	if timer_ui.tick(delta):
		timer_ui.reset(config.turn_timer_seconds)
		_on_end_turn_pressed()
			
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		if not end_turn_button.disabled:
			_on_end_turn_pressed()
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_H:
			show_help_overlay()
		elif event.keycode == KEY_R:
			restart_game()
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
		0:
			enemy_name.text = "程式缺陷 (Bug - Easy)"
			enemy_avatar.texture = load(config.bug_easy_path)
			background_node.texture = load(config.bg_easy_path)
		1:
			enemy_name.text = "程式錯誤 (Bug - Normal)"
			enemy_avatar.texture = load(config.bug_normal_path)
			background_node.texture = load(config.bg_normal_path)
		2:
			enemy_name.text = "系統漏洞 (Bug - Hard)"
			enemy_avatar.texture = load(config.bug_hard_path)
			background_node.texture = load(config.bg_hard_path)
		3:
			enemy_name.text = "核心崩潰 (Bug - Expert)"
			enemy_avatar.texture = load(config.bug_expert_path)
			background_node.texture = load(config.bg_expert_path)
			
	game_state.select_difficulty(diff)
	end_turn_button.disabled = false
	game_state.start_player_turn()

func play_card(index: int) -> void:
	if index >= game_state.hand.size(): return
	var card = game_state.hand[index]
	
	if game_state.player_mana < card.cost:
		combat_juice.play_error()
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
	var DeckControllerScript = preload("res://Scripts/Logic/DeckController.gd")
	DeckControllerScript.initialize_deck(deck_manager, git_parser)
	game_state.deck_manager = deck_manager
	game_state.hand.clear()
	action_log.text = "[b]Combat Log[/b]\n"
	show_difficulty_selection()

func log_action(msg: String) -> void:
	action_log.append_text(msg + "\n")
	var scrollbar = action_log.get_v_scroll_bar()
	scrollbar.value = scrollbar.max_value

func _on_player_hp_changed(current_hp: int, max_hp: int) -> void:
	hud_controller.update_hp(true, current_hp, max_hp)

func _on_enemy_hp_changed(current_hp: int, max_hp: int) -> void:
	hud_controller.update_hp(false, current_hp, max_hp)

func _on_player_block_changed(current_block: int) -> void:
	hud_controller.update_block(true, current_block)

func _on_enemy_block_changed(current_block: int) -> void:
	var final_enemy_dmg = game_state.enemy_damage + game_state.enemy_strength
	hud_controller.update_intent(final_enemy_dmg, game_state.enemy_block, game_state.enemy_strength)

func _on_mana_changed(current_mana: int, max_mana: int) -> void:
	hud_controller.update_mana(current_mana, max_mana)

var combo_tween: Tween

func _on_combo_changed(combo_count: int, combo_category: String) -> void:
	if combo_count > 1:
		var multiplier = 1.0 + (combo_count - 1) * 0.5
		combo_label.text = str(multiplier) + "x COMBO!"
		combo_label.pivot_offset = combo_label.size / 2
		if combo_tween:
			combo_tween.kill()
		combo_tween = self.create_tween().set_trans(Tween.TRANS_SPRING)
		combo_tween.tween_property(combo_label, "scale", Vector2(1.5, 1.5), 0.2).from(Vector2(0.5, 0.5))
		combo_tween.tween_property(combo_label, "scale", Vector2(1, 1), 0.2)
	else:
		combo_label.text = ""

func _update_enemy_intent() -> void:
	var final_enemy_dmg = game_state.enemy_damage + game_state.enemy_strength
	hud_controller.update_intent(final_enemy_dmg, game_state.enemy_block, game_state.enemy_strength)

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
	
	if config and config.get("turn_timer_seconds") != null:
		timer_ui.reset(config.get("turn_timer_seconds"))
	else:
		timer_ui.reset(30.0)
	
	var hand_controller = load("res://Scripts/UI/HandController.gd")
	hand_controller.render_hand(hand_area, game_state, config, Callable(self, "play_card"))

func _on_turn_changed(turn: int) -> void:
	hud_controller.update_turn(turn)
