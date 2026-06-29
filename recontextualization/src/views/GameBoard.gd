extends Control

@onready var hand_container: HBoxContainer = $MarginContainer/VBoxContainer/HandContainer
@onready var event_queue: Node = $EventQueue

var card_chip_scene = preload("res://src/views/CardChip.tscn")

@onready var ap_label: Label = $MarginContainer/VBoxContainer/TopBar/APLabel
@onready var context_label: Label = $MarginContainer/VBoxContainer/TopBar/ContextLabel
@onready var boss_hp_label: Label = $MarginContainer/VBoxContainer/TopBar/BossHPLabel

func _ready():
	# Allow any Autoload (like EventBus) to register card draws.
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		if event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.connect(_on_card_drawn)
			
	if Engine.has_singleton("GameState"):
		var game_state = Engine.get_singleton("GameState")
		game_state.ap_changed.connect(_on_ap_changed)
		game_state.context_updated.connect(_on_context_updated)
		game_state.hp_changed.connect(_on_hp_changed)
		# Initialize UI
		_on_ap_changed(game_state.current_ap)
		_on_hp_changed(game_state.enemy_hp)

func _on_ap_changed(new_ap: int):
	ap_label.text = "AP: %d" % new_ap

func _on_context_updated(purity: float):
	context_label.text = "Context Purity: %d%%" % int(purity * 100)

func _on_hp_changed(new_hp: float):
	var old_text = boss_hp_label.text
	boss_hp_label.text = "Boss HP: %d" % int(new_hp)
	
	# Only flash if it's a decrease (taking damage)
	if old_text != "Boss HP: %d" % int(new_hp) and not old_text.is_empty():
		event_queue.add_animation(func():
			var tween = create_tween()
			boss_hp_label.modulate = Color.RED
			
			# Shake effect
			var original_pos = boss_hp_label.position
			tween.tween_property(boss_hp_label, "position", original_pos + Vector2(10, 0), 0.05)
			tween.tween_property(boss_hp_label, "position", original_pos - Vector2(10, 0), 0.05)
			tween.tween_property(boss_hp_label, "position", original_pos + Vector2(5, 0), 0.05)
			tween.tween_property(boss_hp_label, "position", original_pos, 0.05)
			
			tween.parallel().tween_property(boss_hp_label, "modulate", Color.WHITE, 0.3)
			await tween.finished
		)

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
