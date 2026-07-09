class_name MatchBuilder
extends Node

func build_match(game_state: Node) -> void:
	var sm = _safe_get_node(game_state, "SaveManager")
	
	_setup_tutorial(game_state, sm)
	_setup_difficulty(game_state, sm)
	_draw_starting_hand(game_state, sm)

func _safe_get_node(context: Node, singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if context.is_inside_tree():
		return context.get_node_or_null("/root/" + singleton_name)
	return null

func _setup_tutorial(game_state: Node, sm: Node) -> void:
	var has_completed_tutorial = false
	if sm != null:
		has_completed_tutorial = sm.has_completed_tutorial
		
	if not has_completed_tutorial:
		game_state.is_tutorial_active = true
		var t_mgr_scene = preload("res://src/managers/tutorial/TutorialManager.gd")
		var t_mgr = t_mgr_scene.new()
		game_state.add_child(t_mgr)
	else:
		game_state.is_tutorial_active = false

func _setup_difficulty(game_state: Node, sm: Node) -> void:
	if sm != null:
		game_state.max_player_hp = sm.max_player_hp
		game_state.player_hp = game_state.max_player_hp
		

		
		var sec = ProgressionSystem.get_current_sector(sm)
		
		game_state.base_poisoning_ratio = GameBalanceConfig.get_sector_poison(sec)
		game_state.data_poisoning_ratio = game_state.base_poisoning_ratio
		
		game_state.max_crisis_hp = GameBalanceConfig.get_sector_base_hp(sec)
		game_state.crisis_hp = game_state.max_crisis_hp

func _draw_starting_hand(game_state: Node, sm: Node) -> void:
	var card_reg = _safe_get_node(game_state, "CardRegistry")
	var event_bus = _safe_get_node(game_state, "EventBus")
	
	if card_reg != null and event_bus != null:
		var equipped = ["action_keyword", "action_dense", "action_reranker"]
		if sm != null:
			equipped = sm.equipped_action_cards
			
		for card_id in equipped:
			var card = card_reg.get_card(card_id)
			if card:
				event_bus.card_drawn.emit(card)
