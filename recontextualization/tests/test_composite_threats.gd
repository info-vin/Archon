extends RefCounted

func run_tests(scene_tree: SceneTree) -> bool:
	print("Running test_composite_threats...")
	var passed = true
	
	if Engine.has_singleton("EventBus"):
		Engine.unregister_singleton("EventBus")
	if Engine.has_singleton("GameState"):
		Engine.unregister_singleton("GameState")
		
	# Manually instantiate singletons
	var event_bus = preload("res://src/autoloads/EventBus.gd").new()
	Engine.register_singleton("EventBus", event_bus)
	
	var game_state = preload("res://src/autoloads/GameState.gd").new()
	Engine.register_singleton("GameState", game_state)
	
	# Run ready manually for headless testing (since we just created it)
	game_state._ready()
	game_state.start_game()
	game_state.is_tutorial_active = false
	
	var initial_sla = game_state.sla_timer
	var initial_hp = game_state.player_hp
	
	# Test 1: SLA Penalty for Action Card
	var action_card = preload("res://src/models/cards/CardData.gd").new()
	action_card.set("type", 1) # ACTION
	action_card.set("id", "some_action")
	action_card.set("ap_cost", 3)
	
	if Engine.has_singleton("EventBus"):
		game_state.hand_context.add_card(action_card)
		Engine.get_singleton("EventBus").request_play_card.emit(action_card)
		
	# Cost 3 * 2.0 = 6.0 seconds penalty
	if abs(game_state.sla_timer - (initial_sla - 6.0)) > 0.1:
		print("FAIL: SLA Penalty not applied correctly. Expected %f, got %f" % [initial_sla - 6.0, game_state.sla_timer])
		passed = false
	else:
		print("PASS: SLA Penalty applied (-6.0s for AP cost 3).")
		
	# Test 2: Reranker and Hallucination Logic
	var card_script = preload("res://src/models/cards/CardData.gd")
	var data_chip = card_script.new()
	data_chip.set("type", 2) # DATA_CHIP
	data_chip.set("similarity", 0.9)
	data_chip.set("ap_cost", 1)
	
	var noise_chip = card_script.new()
	noise_chip.set("type", 3) # NOISE_CHIP
	noise_chip.set("similarity", 0.3) # Under 0.5 threshold -> noise
	noise_chip.set("ap_cost", 1)
	
	# Add both to context
	game_state.hand_context.add_card(data_chip)
	event_bus.request_play_card.emit(data_chip)
	game_state.hand_context.add_card(noise_chip)
	event_bus.request_play_card.emit(noise_chip)
	
	if game_state.active_context.size() != 2:
		print("FAIL: Context size should be 2. Got ", game_state.active_context.size())
		passed = false
		
	# Play Reranker Card
	var reranker_card = card_script.new()
	reranker_card.set("type", 1) # ACTION
	reranker_card.set("id", "action_reranker")
	reranker_card.set("ap_cost", 3)
	
	game_state.hand_context.add_card(reranker_card)
	event_bus.request_play_card.emit(reranker_card)
	
	# Reranker should remove noise_chip (similarity 0.3 < 0.5)
	if game_state.active_context.size() != 1:
		print("FAIL: Reranker did not remove noise chip. Context size got ", game_state.active_context.size())
		passed = false
	elif game_state.active_context.cards[0] != data_chip:
		print("FAIL: Reranker removed the wrong card!")
		passed = false
	else:
		print("PASS: Reranker filtered out similarity < 0.5 noise chip successfully.")
		
	# Add noise chip back to test hallucination penalty
	game_state.hand_context.add_card(noise_chip)
	event_bus.request_play_card.emit(noise_chip)
	
	var crisis_before = game_state.crisis_hp
	game_state.deliver_context()
	
	# With 1 noise chip, purity is 0.5 < 1.0 -> Delivery damage = 0, player HP decreases by 1 * 20.0 = 20.0
	if game_state.player_hp != initial_hp - 20.0:
		print("FAIL: Hallucination HP penalty mismatch. Expected %f, got %f" % [initial_hp - 20.0, game_state.player_hp])
		passed = false
	elif game_state.crisis_hp != crisis_before:
		print("FAIL: Impact damage should be 0 on hallucination. HP changed to ", game_state.crisis_hp)
		passed = false
	else:
		print("PASS: Hallucination formula matched TDD (0 damage, -20.0 player HP).")
		
	# Test 3: Rate Limit Compression
	# First delivery happened above. delivery_count should be 1. compression should be 0.9.
	if game_state.delivery_count != 1:
		print("FAIL: Delivery count not incremented. Got ", game_state.delivery_count)
		passed = false
	
	if abs(game_state.rate_limit_compression - 0.9) > 0.01:
		print("FAIL: Rate limit compression not updated correctly. Expected 0.9, got ", game_state.rate_limit_compression)
		passed = false
	else:
		print("PASS: Rate Limit Compression updated to 0.9.")
		
	# Test 4: Data Poisoning Growth
	# Manually simulate SLA dropping by 150 seconds (half of 300)
	game_state.env_mgr._process(150.0)
	# SLA was 300 - 6 (action_card) - 6 (reranker) - 2 (delivery) = 286
	# After 150 seconds elapsed, SLA is 136. Elapsed is 164.
	# Poison should be (164/300) * 0.5 = 0.27
	if abs(game_state.data_poisoning_ratio - 0.27) > 0.01:
		print("FAIL: Data Poisoning ratio not scaling correctly. Expected 0.27, got ", game_state.data_poisoning_ratio)
		passed = false
	else:
		print("PASS: Data Poisoning ratio scaled to 0.27 after 164s SLA loss.")
		
	# Cleanup
	Engine.unregister_singleton("EventBus")
	event_bus.free()
	Engine.unregister_singleton("GameState")
	game_state.free()
	
	return passed
