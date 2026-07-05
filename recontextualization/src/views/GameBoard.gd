extends Control

@onready var hand_container: Container = $MarginContainer/VBoxContainer/HandContainer
@onready var event_queue: Node = $EventQueue

@export var main_menu_scene: PackedScene
@export var video_victory: VideoStream
@export var video_defeat_glitch: VideoStream
@export var video_defeat_shutdown: VideoStream

var card_chip_scene = preload("res://src/views/CardChip.tscn")
var CombatJuice = preload("res://src/views/components/CombatJuice.gd")

@onready var poison_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/PoisonBar
@onready var rate_limit_label: Label = $MarginContainer/VBoxContainer/TopBar/RateLimitLabel
@onready var ap_label: Label = $MarginContainer/VBoxContainer/TopBar/APLabel
@onready var purity_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/PurityBar
@onready var crisis_hp_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/CrisisHPBar
@onready var career_label: Label = $MarginContainer/VBoxContainer/TopBar/CareerLabel
@onready var player_hp_bar: ProgressBar = $MarginContainer/VBoxContainer/TopBar/PlayerHPBar
@onready var sla_progress: ProgressBar = $MarginContainer/VBoxContainer/TopBar/SLAPorgressBar
@onready var sla_text: Label = $MarginContainer/VBoxContainer/TopBar/SLAPorgressBar/SLAText

@onready var query_input: LineEdit = $MarginContainer/VBoxContainer/QueryBar/QueryInput
@onready var deliver_button: Button = $MarginContainer/VBoxContainer/QueryBar/DeliverButton

@onready var tutorial_panel: ColorRect = $TutorialPanel
@onready var start_button: Button = $TutorialPanel/VBox/StartButton

@onready var game_over_panel: ColorRect = $GameOverPanel
@onready var game_over_title: Label = $GameOverPanel/VBox/Title
@onready var restart_button: Button = $GameOverPanel/VBox/RestartButton
@onready var end_game_video: VideoStreamPlayer = $EndGameVideoPlayer

@onready var pause_menu: ColorRect = $PauseMenu

var backend_client_script = preload("res://src/network/BackendClient.gd")
var backend_client: Node
func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null

func _ready() -> void:
	# Allow any Autoload (like EventBus) to register card draws.
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		if event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.connect(_on_card_drawn)
		if event_bus.has_signal("card_played"):
			event_bus.card_played.connect(_on_card_played)

	var style_green = StyleBoxFlat.new()
	style_green.bg_color = Color(0.2, 0.8, 0.2, 1.0)
	purity_bar.add_theme_stylebox_override("fill", style_green)

	var style_red = StyleBoxFlat.new()
	style_red.bg_color = Color(1.0, 0.2, 0.2, 1.0)
	poison_bar.add_theme_stylebox_override("fill", style_red)

	var style_dark_red = StyleBoxFlat.new()
	style_dark_red.bg_color = Color(0.6, 0.0, 0.0, 1.0)
	crisis_hp_bar.add_theme_stylebox_override("fill", style_dark_red)

	start_button.pressed.connect(_on_start_pressed)
	restart_button.pressed.connect(_on_restart_pressed)
	deliver_button.pressed.connect(_on_deliver_pressed)
	query_input.text_submitted.connect(_on_query_submitted)
	
	if pause_menu:
		pause_menu.resume_game.connect(func(): pause_menu.hide())
		pause_menu.save_progress.connect(func(): 
			var sm = _safe_get_node("SaveManager")
			if sm != null: sm.save_progress()
		)
		pause_menu.load_progress.connect(func():
			var sm = _safe_get_node("SaveManager")
			if sm != null: sm.load_progress()
			pause_menu.hide()
			get_tree().reload_current_scene()
		)
		pause_menu.quit_to_menu.connect(func():
			pause_menu.hide()
			if main_menu_scene:
				get_tree().change_scene_to_packed(main_menu_scene)
		)
		pause_menu.quit_game.connect(func():
			get_tree().quit()
		)
	
	var game_state = _safe_get_node("GameState")
	if game_state != null:
		game_state.ap_changed.connect(_on_ap_changed)
		game_state.context_updated.connect(_on_context_updated)
		game_state.hp_changed.connect(_on_hp_changed)
		game_state.player_hp_changed.connect(_on_player_hp_changed)
		game_state.sla_changed.connect(_on_sla_changed)
		game_state.game_over.connect(_on_game_over)
		game_state.poisoning_updated.connect(_on_poisoning_updated)
		game_state.rate_limit_updated.connect(_on_rate_limit_updated)
		game_state.search_triggered.connect(_on_search_triggered)
		game_state.context_purified.connect(_on_context_purified)
		
		var sm = _safe_get_node("SaveManager")
		if sm != null:
			career_label.text = "L" + str(sm.career_level)
			player_hp_bar.max_value = sm.max_player_hp
		
		# Initialize UI
		_on_ap_changed(game_state.current_ap)
		_on_hp_changed(game_state.crisis_hp)
		_on_player_hp_changed(game_state.player_hp)
		_on_sla_changed(game_state.sla_timer)
		_on_poisoning_updated(game_state.data_poisoning_ratio)
		_on_rate_limit_updated(game_state.rate_limit_compression)
		
	game_over_panel.hide()
	
	var sm = _safe_get_node("SaveManager")
	if sm != null:
		if not sm.has_completed_tutorial:
			tutorial_panel.hide()
			# Start game immediately for tutorial
			if game_state != null:
				game_state.is_tutorial_active = true
				game_state.start_game()
		else:
			if game_state != null:
				game_state.is_tutorial_active = false
			tutorial_panel.show()
	else:
		tutorial_panel.show()

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		if not tutorial_panel.visible and not game_over_panel.visible:
			if pause_menu:
				pause_menu.visible = not pause_menu.visible

func _on_start_pressed() -> void:
	tutorial_panel.hide()
	var game_state = _safe_get_node("GameState")
	if game_state != null:
		game_state.start_game()

func _on_restart_pressed() -> void:
	if main_menu_scene:
		get_tree().change_scene_to_packed(main_menu_scene)

func _on_ap_changed(new_ap: int) -> void:
	ap_label.text = tr("hud_ap") + ": %d" % new_ap

func _on_context_updated(purity: float) -> void:
	purity_bar.value = purity * 100.0

func _on_player_hp_changed(new_hp: float) -> void:
	player_hp_bar.value = new_hp

func _on_hp_changed(new_hp: float) -> void:
	var old_val = crisis_hp_bar.value
	crisis_hp_bar.value = new_hp
	
	if old_val > new_hp:
		event_queue.add_animation(func():
			var tween = CombatJuice.damage_flash_and_shake(crisis_hp_bar)
			await tween.finished
		)

func _on_sla_changed(new_sla: float) -> void:
	sla_progress.value = new_sla
	var mins = int(new_sla) / 60
	var secs = int(new_sla) % 60
	sla_text.text = "SLA: %02d:%02d" % [mins, secs]
	
	if new_sla < 30.0:
		CombatJuice.warning_pulse(sla_progress, Time.get_ticks_msec())
	elif new_sla < 60.0:
		sla_progress.modulate = Color.RED
	else:
		sla_progress.modulate = Color.WHITE

func _on_game_over(is_victory: bool, rank: String = "") -> void:
	if is_victory:
		game_over_title.text = "危機解除！"
		if rank != "":
			game_over_title.text += " (Rank: " + rank + ")"
		game_over_title.add_theme_color_override("font_color", Color.GREEN)
		if video_victory:
			end_game_video.stream = video_victory
		end_game_video.show()
		end_game_video.play()
		await end_game_video.finished
	else:
		game_over_title.text = "系統崩潰！(SLA 超時或幻覺反噬)"
		game_over_title.add_theme_color_override("font_color", Color.RED)
		if video_defeat_glitch:
			end_game_video.stream = video_defeat_glitch
		end_game_video.show()
		end_game_video.play()
		await end_game_video.finished
		
		# Chain the shutdown video
		if video_defeat_shutdown:
			end_game_video.stream = video_defeat_shutdown
		end_game_video.play()
		await end_game_video.finished
		
	end_game_video.hide()
	game_over_panel.show()

func _on_poisoning_updated(ratio: float) -> void:
	poison_bar.value = ratio * 100.0

func _on_rate_limit_updated(compression: float) -> void:
	if compression < 0.8:
		rate_limit_label.show()
		# Flash animation
		event_queue.add_animation(func():
			var tween = CombatJuice.flash_alpha(rate_limit_label)
			await tween.finished
		)
	else:
		rate_limit_label.hide()

func _on_deliver_pressed() -> void:
	var play_area = $MarginContainer/VBoxContainer/PlayArea
	if not play_area: return
	
	var juice = load("res://src/views/components/CombatJuice.gd")
	if juice: juice.deliver_blast(deliver_button)
	
	var game_state = _safe_get_node("GameState")
	if game_state != null:
		game_state.deliver_context()

func _on_query_submitted(new_text: String) -> void:
	var game_state = _safe_get_node("GameState")
	if game_state != null:
		game_state.trigger_search(1) # 1 = KEYWORD

func _on_search_triggered(match_type: int) -> void:
	# Now just purely visual if needed, GameState handles network.
	pass

func _on_context_purified(remaining_cards: Array) -> void:
	var play_area = $MarginContainer/VBoxContainer/PlayArea
	for child in play_area.get_children():
		if child.name == "HintLabel":
			continue
		if child.get("card_data") != null:
			var c_data = child.card_data
			if not remaining_cards.has(c_data):
				event_queue.add_animation(func():
					var juice = load("res://src/views/components/CombatJuice.gd")
					if juice:
						var tween = juice.card_dissolve(child)
						await tween.finished
					else:
						child.queue_free()
				)

func _on_card_drawn(card: Resource) -> void:
	event_queue.add_animation(func():
		await _anim_draw_card(card)
	)

func _on_card_played(card: Resource) -> void:
	# Find the card in hand and move it to play area
	var target_child = null
	for child in hand_container.get_children():
		if child.has_method("get_card_data") and child.get_card_data() == card:
			target_child = child
			break
			
	if target_child != null:
		event_queue.add_animation(func():
			var play_area = $MarginContainer/VBoxContainer/PlayArea
			target_child.get_parent().remove_child(target_child)
			play_area.add_child(target_child)
			
			var tween = create_tween()
			var target_pos = (play_area.size / 2.0) - (target_child.size / 2.0)
			tween.tween_property(target_child, "position", target_pos, 0.4).set_trans(Tween.TRANS_SPRING)
			tween.parallel().tween_property(target_child, "scale", Vector2(0.8, 0.8), 0.3)
			await get_tree().create_timer(0.4).timeout
		)

func _anim_draw_card(card: Resource) -> void:
	var chip = card_chip_scene.instantiate()
	hand_container.add_child(chip)
	chip.set_card_data(card)
	
	# Initial state: small and transparent
	chip.modulate.a = 0.0
	chip.scale = Vector2(0.1, 0.1)
	
	var tween = create_tween().set_parallel(true)
	tween.tween_property(chip, "modulate:a", 1.0, 0.3).set_ease(Tween.EASE_OUT)
	tween.tween_property(chip, "scale", Vector2(1.0, 1.0), 0.3).set_trans(Tween.TRANS_SPRING)
	
	await get_tree().create_timer(0.3).timeout
