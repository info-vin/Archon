class_name EnvironmentManager
extends Node

signal sla_changed(new_sla: float)
signal poisoning_updated(ratio: float)

var game_state: Node


func _ready() -> void:
	game_state = get_parent()

func _process(delta: float) -> void:
	if game_state.is_game_active and not game_state.is_tutorial_active and game_state.sla_timer > 0.0:
		game_state.sla_timer -= delta
		sla_changed.emit(game_state.sla_timer)
		
		var elapsed = game_state.max_sla - game_state.sla_timer
		var target_poison = min(GameBalanceConfig.MAX_POISON_RATIO_LIMIT, game_state.base_poisoning_ratio + (elapsed / game_state.max_sla * GameBalanceConfig.POISON_TIME_SCALE))
		if abs(target_poison - game_state.data_poisoning_ratio) > 0.01:
			game_state.data_poisoning_ratio = target_poison
			poisoning_updated.emit(game_state.data_poisoning_ratio)
			
		if game_state.sla_timer <= 0.0:
			game_state.sla_timer = 0.0
			game_state.is_game_active = false
			game_state.game_over.emit(false, "")

func deduct_sla(amount: float) -> void:
	if game_state.is_game_active and not game_state.is_tutorial_active:
		game_state.sla_timer -= amount
		if game_state.sla_timer <= 0.0:
			game_state.sla_timer = 0.0
			game_state.is_game_active = false
			game_state.game_over.emit(false, "")
		sla_changed.emit(game_state.sla_timer)
