extends Control

@onready var hand_container: HBoxContainer = $MarginContainer/VBoxContainer/HandContainer
@onready var event_queue: Node = $EventQueue

var card_chip_scene = preload("res://src/views/CardChip.tscn")

@onready var poison_label: Label = $MarginContainer/VBoxContainer/TopBar/PoisonLabel
@onready var rate_limit_label: Label = $MarginContainer/VBoxContainer/TopBar/RateLimitLabel
@onready var ap_label: Label = $MarginContainer/VBoxContainer/TopBar/APLabel
@onready var context_label: Label = $MarginContainer/VBoxContainer/TopBar/ContextLabel
@onready var crisis_hp_label: Label = $MarginContainer/VBoxContainer/TopBar/CrisisHPLabel
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

var backend_client_script = preload("res://src/network/BackendClient.gd")
var backend_client: Node

func _ready() -> void:
	# Instantiate BackendClient
	backend_client = backend_client_script.new()
	add_child(backend_client)
	backend_client.request_completed.connect(_on_search_completed)
	backend_client.request_failed.connect(_on_search_failed)

	# Allow any Autoload (like EventBus) to register card draws.
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		if event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.connect(_on_card_drawn)
			
	start_button.pressed.connect(_on_start_pressed)
	restart_button.pressed.connect(_on_restart_pressed)
	deliver_button.pressed.connect(_on_deliver_pressed)
	query_input.text_submitted.connect(_on_query_submitted)
	
	if Engine.has_singleton("GameState"):
		var game_state = Engine.get_singleton("GameState")
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
		
		if Engine.has_singleton("SaveManager"):
			var sm = Engine.get_singleton("SaveManager")
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
	
	if Engine.has_singleton("SaveManager"):
		var sm = Engine.get_singleton("SaveManager")
		if not sm.has_completed_tutorial:
			tutorial_panel.hide()
			var t_mgr_scene = preload("res://src/managers/tutorial/TutorialManager.gd")
			var t_mgr = t_mgr_scene.new()
			add_child(t_mgr)
			# Start game immediately for tutorial
			if Engine.has_singleton("GameState"):
				Engine.get_singleton("GameState").is_tutorial_active = true
				Engine.get_singleton("GameState").start_game()
		else:
			if Engine.has_singleton("GameState"):
				Engine.get_singleton("GameState").is_tutorial_active = false
			tutorial_panel.show()
	else:
		tutorial_panel.show()

func _on_start_pressed() -> void:
	tutorial_panel.hide()
	if Engine.has_singleton("GameState"):
		Engine.get_singleton("GameState").start_game()

func _on_restart_pressed() -> void:
	get_tree().change_scene_to_file("res://src/views/MainMenu.tscn")

func _on_ap_changed(new_ap: int) -> void:
	ap_label.text = "AP: %d" % new_ap

func _on_context_updated(purity: float) -> void:
	context_label.text = "Context Purity: %d%%" % int(purity * 100)

func _on_player_hp_changed(new_hp: float) -> void:
	player_hp_bar.value = new_hp

func _on_hp_changed(new_hp: float) -> void:
	var old_text = crisis_hp_label.text
	crisis_hp_label.text = "Crisis HP: %d" % int(new_hp)
	
	# Only flash if it's a decrease (taking damage)
	if old_text != "Crisis HP: %d" % int(new_hp) and not old_text.is_empty():
		event_queue.add_animation(func():
			var tween = create_tween()
			crisis_hp_label.modulate = Color.RED
			
			# Shake effect
			var original_pos = crisis_hp_label.position
			tween.tween_property(crisis_hp_label, "position", original_pos + Vector2(10, 0), 0.05)
			tween.tween_property(crisis_hp_label, "position", original_pos - Vector2(10, 0), 0.05)
			tween.tween_property(crisis_hp_label, "position", original_pos + Vector2(5, 0), 0.05)
			tween.tween_property(crisis_hp_label, "position", original_pos, 0.05)
			
			tween.parallel().tween_property(crisis_hp_label, "modulate", Color.WHITE, 0.3)
			await tween.finished
		)

func _on_sla_changed(new_sla: float) -> void:
	sla_progress.value = new_sla
	var mins = int(new_sla) / 60
	var secs = int(new_sla) % 60
	sla_text.text = "SLA: %02d:%02d" % [mins, secs]
	
	if new_sla < 30.0:
		var pulse = (sin(Time.get_ticks_msec() / 150.0) + 1.0) / 2.0
		sla_progress.modulate = Color.WHITE.lerp(Color.RED, pulse)
	elif new_sla < 60.0:
		sla_progress.modulate = Color.RED
	else:
		sla_progress.modulate = Color.WHITE

func _on_game_over(is_victory: bool) -> void:
	game_over_panel.show()
	if is_victory:
		game_over_title.text = "危機解除！"
		game_over_title.add_theme_color_override("font_color", Color.GREEN)
	else:
		game_over_title.text = "系統崩潰！(SLA 超時或幻覺反噬)"
		game_over_title.add_theme_color_override("font_color", Color.RED)

func _on_poisoning_updated(ratio: float) -> void:
	poison_label.text = "Poisoning: %d%%" % int(ratio * 100)
	if ratio > 0.2:
		poison_label.add_theme_color_override("font_color", Color.RED)
	else:
		poison_label.add_theme_color_override("font_color", Color(1.0, 0.5, 0.0, 1.0)) # Orange

func _on_rate_limit_updated(compression: float) -> void:
	if compression < 0.8:
		rate_limit_label.show()
		# Flash animation
		event_queue.add_animation(func():
			var tween = create_tween()
			tween.tween_property(rate_limit_label, "modulate:a", 0.0, 0.2)
			tween.tween_property(rate_limit_label, "modulate:a", 1.0, 0.2)
			await tween.finished
		)
	else:
		rate_limit_label.hide()

func _on_deliver_pressed() -> void:
	if Engine.has_singleton("GameState"):
		Engine.get_singleton("GameState").deliver_context()

func _on_query_submitted(new_text: String) -> void:
	if Engine.has_singleton("GameState"):
		Engine.get_singleton("GameState").trigger_search(1) # 1 = KEYWORD

func _on_search_triggered(match_type: int) -> void:
	var query_text = query_input.text.strip_edges()
	if query_text.is_empty():
		query_text = "default query"
		
	var t_mgr = get_tree().get_first_node_in_group("tutorial_manager")
	if t_mgr != null:
		# Seeded Random (1 perfect, 1 noise)
		var card1 = CardData.new()
		card1.type = CardData.CardType.DATA_CHIP
		card1.similarity = 0.98
		card1.title = "精準資料"
		
		var card2 = CardData.new()
		card2.type = CardData.CardType.NOISE_CHIP
		card2.similarity = 0.2
		card2.title = "雜訊干擾"
		
		if Engine.has_singleton("EventBus"):
			Engine.get_singleton("EventBus").card_drawn.emit(card1)
			Engine.get_singleton("EventBus").card_drawn.emit(card2)
	else:
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
			
		if Engine.has_singleton("EventBus"):
			Engine.get_singleton("EventBus").card_drawn.emit(card)

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
		
		if Engine.has_singleton("EventBus"):
			Engine.get_singleton("EventBus").card_drawn.emit(card)

func _on_context_purified(remaining_cards: Array) -> void:
	var play_area = $MarginContainer/VBoxContainer/PlayArea
	for child in play_area.get_children():
		if child.name == "HintLabel":
			continue
		if child.get("card_data") != null:
			var c_data = child.card_data
			if not remaining_cards.has(c_data):
				event_queue.add_animation(func():
					var tween = create_tween().set_parallel(true)
					tween.tween_property(child, "modulate:a", 0.0, 0.3)
					tween.tween_property(child, "scale", Vector2(0.1, 0.1), 0.3)
					tween.chain().tween_callback(func(): child.queue_free())
					await tween.finished
				)

func _on_card_drawn(card: Resource) -> void:
	# Hand Limit constraint: max 5 cards
	if hand_container.get_child_count() >= 5:
		print("Hand full! Card draw rejected.")
		return

	if Engine.has_singleton("GameState"):
		var ratio = Engine.get_singleton("GameState").data_poisoning_ratio
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
	
	await tween.finished
