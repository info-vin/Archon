extends RefCounted

func run_tests(scene_tree: SceneTree) -> bool:
	print("Running test_composite_threats...")
	var passed = true
	
	# Manually instantiate singletons
	var event_bus = preload("res://src/autoloads/EventBus.gd").new()
	Engine.register_singleton("EventBus", event_bus)
	
	var game_state = preload("res://src/autoloads/GameState.gd").new()
	Engine.register_singleton("GameState", game_state)
	
	# Run ready manually for headless testing (since we just created it)
	game_state._ready()
	game_state.start_game()
	
	var initial_sla = game_state.sla_timer
	
	# Test 1: SLA Penalty for Action Card
	var action_card = preload("res://src/models/cards/CardData.gd").new()
	action_card.set("type", 1) # Action
	action_card.set("ap_cost", 3)
	
	if Engine.has_singleton("EventBus"):
		Engine.get_singleton("EventBus").card_played.emit(action_card)
		
	# Cost 3 * 2.0 = 6.0 seconds penalty
	if abs(game_state.sla_timer - (initial_sla - 6.0)) > 0.1:
		print("FAIL: SLA Penalty not applied correctly. Expected %f, got %f" % [initial_sla - 6.0, game_state.sla_timer])
		passed = false
	else:
		print("PASS: SLA Penalty applied (-6.0s for AP cost 3).")
		
	# Test 2: Rate Limit Compression
	# First delivery happened above. delivery_count should be 1. compression should be 0.9.
	if game_state.delivery_count != 1:
		print("FAIL: Delivery count not incremented. Got ", game_state.delivery_count)
		passed = false
	
	if abs(game_state.rate_limit_compression - 0.9) > 0.01:
		print("FAIL: Rate limit compression not updated correctly. Expected 0.9, got ", game_state.rate_limit_compression)
		passed = false
	else:
		print("PASS: Rate Limit Compression updated to 0.9.")
		
	# Test 3: Data Poisoning Growth
	# Manually simulate SLA dropping by 150 seconds (half of 300)
	game_state._process(150.0)
	# Poison should be (156/300) * 0.5 = 0.26
	if abs(game_state.data_poisoning_ratio - 0.26) > 0.01:
		print("FAIL: Data Poisoning ratio not scaling correctly. Expected 0.26, got ", game_state.data_poisoning_ratio)
		passed = false
	else:
		print("PASS: Data Poisoning ratio scaled to 0.26 after 156s SLA loss.")
		
	# Cleanup
	Engine.unregister_singleton("EventBus")
	event_bus.free()
	Engine.unregister_singleton("GameState")
	game_state.free()
	
	return passed
