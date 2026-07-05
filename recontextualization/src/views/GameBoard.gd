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
	# Instantiate BackendClient
	backend_client = backend_client_script.new()
	add_child(backend_client)
	backend_client.request_completed.connect(_on_search_completed)
	backend_client.request_failed.connect(_on_search_failed)

	var style_green = StyleBoxFlat.new()
	style_green.bg_color = Color(0.2, 0.8, 0.2, 1.0)
	purity_bar.add_theme_stylebox_override("fill", style_green)

	var style_red = StyleBoxFlat.new()
	style_red.bg_color = Color(1.0, 0.2, 0.2, 1.0)
	poison_bar.add_theme_stylebox_override("fill", style_red)

	var style_dark_red = StyleBoxFlat.new()
	style_dark_red.bg_color = Color(0.6, 0.0, 0.0, 1.0)
	crisis_hp_bar.add_theme_stylebox_override("fill", style_dark_red)

	# Allow any Autoload (like EventBus) to register card draws.
	var event_bus = _safe_get_node("EventBus")
	if event_bus != null:
		if event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.connect(_on_card_drawn)
			
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
			var t_mgr_scene = preload("res://src/managers/tutorial/TutorialManager.gd")
			var t_mgr = t_mgr_scene.new()
			add_child(t_mgr)
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
	var game_state = _safe_get_node("GameState")
	if game_state != null:
		game_state.deliver_context()

func _on_query_submitted(new_text: String) -> void:
	var game_state = _safe_get_node("GameState")
	if game_state != null:
		game_state.trigger_search(1) # 1 = KEYWORD

func _on_search_triggered(match_type: int) -> void:
	var query_text = query_input.text.strip_edges()
	if query_text.is_empty():
		query_text = "default query"
		
	# Always use backend client. BackendClient handles tutorial mock data internally.
	backend_client.search(query_text, 0.5, 5)

func _on_search_completed(response: Dictionary) -> void:
	if not response.has("results"):
		return
	var results = response.get("results")
	for chunk in results:
		var card = CardData.new()
		card.type = CardData.CardType.DATA_CHIP
		card.similarity = chunk.get("similarity", 0.0)
		card.title = chunk.get("content", "Data Chunk").left(20) + "..."
		
		# Set match type based on string
		var mt = chunk.get("match_type", "keyword")
		if mt == "keyword":
			card.match_type = CardData.MatchType.KEYWORD
		elif mt == "vector":
			card.match_type = CardData.MatchType.VECTOR
		else:
			card.match_type = CardData.MatchType.HYBRID
			
		var event_bus = _safe_get_node("EventBus")
		if event_bus != null:
			event_bus.card_drawn.emit(card)

func _on_search_failed(error_code: int, message: String) -> void:
	print("Search failed (Code: %d, Message: %s). Activating Standalone Fallback!" % [error_code, message])
	var num_cards = randi_range(3, 4)
	var base_title = query_input.text if not query_input.text.is_empty() else "RAG Chunk"
	
	for i in range(num_cards):
		var card = CardData.new()
		card.type = CardData.CardType.DATA_CHIP
		card.similarity = randf_range(0.3, 0.98)
		card.title = "[MOCK] %s #%d" % [base_title.left(15), i + 1]
		card.match_type = randi_range(1, 3) # Random MatchType
		
		var event_bus = _safe_get_node("EventBus")
		if event_bus != null:
			event_bus.card_drawn.emit(card)

func _on_context_purified(remaining_cards: Array) -> void:
	var play_area = $MarginContainer/VBoxContainer/PlayArea
	for child in play_area.get_children():
		if child.name == "HintLabel":
			continue
		if child.get("card_data") != null:
			var c_data = child.card_data
			if not remaining_cards.has(c_data):
				event_queue.add_animation(func():
					if not is_instance_valid(child):
						return
					var tween = create_tween().set_parallel(true)
					tween.tween_property(child, "modulate:a", 0.0, 0.3)
					tween.tween_property(child, "scale", Vector2(0.1, 0.1), 0.3)
					tween.chain().tween_callback(func(): 
						if is_instance_valid(child):
							child.queue_free()
					)
					await get_tree().create_timer(0.3).timeout
				)

func _on_card_drawn(card: Resource) -> void:
	# Hand Limit constraint: max 5 cards
	if hand_container.get_child_count() >= 5:
		print("Hand full! Card draw rejected.")
		return

	var game_state = _safe_get_node("GameState")
	if game_state != null:
		var ratio = game_state.data_poisoning_ratio
		if randf() < ratio:
			var type_val = card.get("type") if card.get("type") != null else 1
			if type_val == 2: # DATA_CHIP = 2
				card.set("type", 3) # Convert to Noise Chip (NOISE_CHIP = 3)
				var current_title = card.get("title")
				card.set("title", "[CORRUPTED] " + (current_title if current_title != null else ""))

	event_queue.add_animation(func():
		await _anim_draw_card(card)
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
