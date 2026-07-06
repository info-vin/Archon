extends Node

var tests_passed = 0
var tests_failed = 0

func assert_eq(actual, expected, message: String = "") -> bool:
	if actual == expected:
		return true
	print("FAIL: Expected ", expected, " but got ", actual, ". ", message)
	return false

func run_tests(runner) -> bool:
	print("Running test_graphrag_chain...")
	
	if Engine.has_singleton("EventBus"):
		Engine.unregister_singleton("EventBus")
	if Engine.has_singleton("GameState"):
		Engine.unregister_singleton("GameState")
		
	var event_bus = preload("res://src/autoloads/EventBus.gd").new()
	Engine.register_singleton("EventBus", event_bus)
	
	var game_state = preload("res://src/autoloads/GameState.gd").new()
	Engine.register_singleton("GameState", game_state)
	
	game_state._ready()
	game_state.start_game()
	game_state.is_tutorial_active = false
	
	# Give the player enough AP to play GraphRAG
	game_state.current_ap = 10
	var initial_hp = game_state.crisis_hp
	var initial_ap = game_state.current_ap
	
	var card_script = preload("res://src/models/cards/CardData.gd")
	
	# 1. Create a Data Chip (1 AP)
	var data_chip = card_script.new()
	data_chip.set("type", 2) # DATA_CHIP
	data_chip.set("similarity", 0.9)
	data_chip.set("ap_cost", 1)
	
	game_state.hand_context.add_card(data_chip)
	event_bus.request_play_card.emit(data_chip)
	
	# 2. Create the GraphRAG card (5 AP)
	var graph_rag_card = card_script.new()
	graph_rag_card.set("type", 1) # ACTION
	graph_rag_card.set("id", "graph_rag")
	graph_rag_card.set("ap_cost", 5)
	
	game_state.hand_context.add_card(graph_rag_card)
	event_bus.request_play_card.emit(graph_rag_card)
	
	if not assert_eq(game_state.current_ap, initial_ap - 6, "AP should decrease by 6 (1 for chip, 5 for GraphRAG)"): tests_failed += 1
	if not assert_eq(game_state.active_context.size(), 2, "Context should have 2 cards (Data Chip + GraphRAG)"): tests_failed += 1
	
	# 3. Deliver Context
	game_state.deliver_context()
	
	# Expected Math:
	# Base Firepower = 1000
	# Purity = 1.0 (Only Data Chip counts towards purity, ACTION card is ignored)
	# GraphRAG Chain Multiplier = 1.5
	# Base Damage = 1000 * 1.5 * 1.0 = 1500
	# Compression = 0.9 (First delivery)
	# Final Damage = 1500 * 0.9 = 1350
	
	if not assert_eq(game_state.current_ap, initial_ap - 7, "AP should decrease by 7 total (1 chip, 5 GraphRAG, 1 delivery)"): tests_failed += 1
	if not assert_eq(game_state.active_context.size(), 0, "Context should be cleared after delivery"): tests_failed += 1
	if not assert_eq(game_state.crisis_hp, initial_hp - 1350.0, "HP should decrease by 1350 due to 1.5x chain multiplier"): tests_failed += 1
	
	# Cleanup
	Engine.unregister_singleton("EventBus")
	event_bus.free()
	Engine.unregister_singleton("GameState")
	game_state.free()
	
	if tests_failed == 0:
		print("test_graphrag_chain PASSED")
		return true
	return false
