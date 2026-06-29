extends Control

@onready var hand_container: HBoxContainer = $MarginContainer/VBoxContainer/HandContainer
@onready var event_queue: Node = $EventQueue

var card_chip_scene = preload("res://src/views/CardChip.tscn")

@onready var ap_label: Label = $MarginContainer/VBoxContainer/TopBar/APLabel
@onready var context_label: Label = $MarginContainer/VBoxContainer/TopBar/ContextLabel
@onready var crisis_hp_label: Label = $MarginContainer/VBoxContainer/TopBar/CrisisHPLabel
@onready var sla_progress: ProgressBar = $MarginContainer/VBoxContainer/TopBar/SLAPorgressBar
@onready var sla_text: Label = $MarginContainer/VBoxContainer/TopBar/SLAPorgressBar/SLAText

@onready var tutorial_panel: ColorRect = $TutorialPanel
@onready var start_button: Button = $TutorialPanel/VBox/StartButton

@onready var game_over_panel: ColorRect = $GameOverPanel
@onready var game_over_title: Label = $GameOverPanel/VBox/Title
@onready var restart_button: Button = $GameOverPanel/VBox/RestartButton

func _ready():
	# Allow any Autoload (like EventBus) to register card draws.
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		if event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.connect(_on_card_drawn)
			
	start_button.pressed.connect(_on_start_pressed)
	restart_button.pressed.connect(_on_restart_pressed)
	
	if Engine.has_singleton("GameState"):
		var game_state = Engine.get_singleton("GameState")
		game_state.ap_changed.connect(_on_ap_changed)
		game_state.context_updated.connect(_on_context_updated)
		game_state.hp_changed.connect(_on_hp_changed)
		game_state.sla_changed.connect(_on_sla_changed)
		game_state.game_over.connect(_on_game_over)
		# Initialize UI
		_on_ap_changed(game_state.current_ap)
		_on_hp_changed(game_state.crisis_hp)
		_on_sla_changed(game_state.sla_timer)
		
	# Show tutorial initially, hide game over
	tutorial_panel.show()
	game_over_panel.hide()

func _on_start_pressed():
	tutorial_panel.hide()
	if Engine.has_singleton("GameState"):
		Engine.get_singleton("GameState").start_game()

func _on_restart_pressed():
	game_over_panel.hide()
	# clear hand
	for child in hand_container.get_children():
		child.queue_free()
	if Engine.has_singleton("GameState"):
		Engine.get_singleton("GameState").start_game()

func _on_ap_changed(new_ap: int):
	ap_label.text = "AP: %d" % new_ap

func _on_context_updated(purity: float):
	context_label.text = "Context Purity: %d%%" % int(purity * 100)

func _on_hp_changed(new_hp: float):
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

func _on_sla_changed(new_sla: float):
	sla_progress.value = new_sla
	var mins = int(new_sla) / 60
	var secs = int(new_sla) % 60
	sla_text.text = "SLA: %02d:%02d" % [mins, secs]
	
	if new_sla < 60.0:
		sla_progress.modulate = Color.RED
	else:
		sla_progress.modulate = Color.WHITE

func _on_game_over(is_victory: bool):
	game_over_panel.show()
	if is_victory:
		game_over_title.text = "危機解除！"
		game_over_title.add_theme_color_override("font_color", Color.GREEN)
	else:
		game_over_title.text = "系統崩潰！(SLA 超時或幻覺反噬)"
		game_over_title.add_theme_color_override("font_color", Color.RED)

func _on_card_drawn(card: Resource):
	event_queue.add_animation(func():
		await _anim_draw_card(card)
	)

func _anim_draw_card(card: Resource):
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
