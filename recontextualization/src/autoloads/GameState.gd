extends Node

signal ap_changed(new_ap: int)
signal hp_changed(new_hp: float)
signal player_hp_changed(new_hp: float)
signal player_died()
signal context_updated(purity: float)

var current_ap: int = 10
var enemy_hp: float = 10000.0
var max_enemy_hp: float = 10000.0

var player_hp: float = 100.0
var max_player_hp: float = 100.0

# Composite Threat Mechanics
var sla_timer: float = 300.0
var rate_limit_compression: float = 1.0
var data_poisoning_ratio: float = 0.0

var active_context = preload("res://src/models/DeckData.gd").new()

func _ready() -> void:
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		if event_bus.has_signal("card_played"):
			event_bus.card_played.connect(_on_card_played)

func apply_hallucination_penalty(purity: float) -> void:
	if purity < 1.0:
		# Hallucination Penalty: P < 1.0 triggers damage to player
		var penalty: float = (1.0 - purity) * 10.0
		player_hp -= penalty
		if player_hp <= 0:
			player_hp = 0
			player_died.emit()
		player_hp_changed.emit(player_hp)

func _on_card_played(card: Resource) -> void:
	# Deduct AP (cost is 1 for now, or from card.get("ap_cost") if available)
	var cost = card.get("ap_cost") if card.get("ap_cost") != null else 1
	current_ap -= cost
	ap_changed.emit(current_ap)
	
	# Check card type
	# CardType: ACTION = 1, DATA_CHIP = 2, NOISE_CHIP = 3
	var type_val = card.get("type") if card.get("type") != null else 1
	
	if type_val == 2 or type_val == 3:
		# It's a context chip
		active_context.add_card(card)
		var purity = active_context.calculate_context_purity(0.5)
		context_updated.emit(purity)
		
	elif type_val == 1:
		# It's an Action Card (Execution)
		var purity = active_context.calculate_context_purity(0.5)
		apply_hallucination_penalty(purity)
		
		var damage = active_context.calculate_delivery_damage(1000.0, 0.5, false)
		enemy_hp -= damage
		if enemy_hp < 0:
			enemy_hp = 0
		hp_changed.emit(enemy_hp)
		
		# Reset context after action
		active_context.clear()
		context_updated.emit(0.0)

