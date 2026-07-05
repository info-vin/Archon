extends Node

var tests_passed = 0
var tests_failed = 0

func assert_eq(actual, expected, message: String = "") -> bool:
	if actual == expected:
		return true
	print("FAIL: Expected ", expected, " but got ", actual, ". ", message)
	return false

func run_tests(runner) -> bool:
	print("Running test_state_machine...")
	
	# Manually instantiate singletons
	var event_bus = preload("res://src/autoloads/EventBus.gd").new()
	Engine.register_singleton("EventBus", event_bus)
	
	var game_state = preload("res://src/autoloads/GameState.gd").new()
	Engine.register_singleton("GameState", game_state)
	
	# Run ready manually for headless testing (since we just created it)
	game_state._ready()
	game_state.start_game()
	game_state.is_tutorial_active = false
	
	var initial_hp = game_state.crisis_hp
	var initial_ap = game_state.current_ap
	
	var card_script = preload("res://src/models/cards/CardData.gd")
	
	# Create a Data Chip
	var data_chip = card_script.new()
	data_chip.set("type", 2) # DATA_CHIP
	data_chip.set("similarity", 0.9)
	data_chip.set("ap_cost", 1)
	
	# Emit request_play_card (equivalent to dragging Data Chip to PlayArea)
	game_state.hand_context.add_card(data_chip, 0.0)
	event_bus.request_play_card.emit(data_chip)
	
	if not assert_eq(game_state.current_ap, initial_ap - 1, "AP should decrease by 1"): tests_failed += 1
	if not assert_eq(game_state.active_context.size(), 1, "Context should have 1 card"): tests_failed += 1
	
	# Explicitly call deliver_context (representing clicking the Deliver button)
	game_state.deliver_context()
	
	# Context had 1 card (similarity 0.9 > 0.5), purity = 1.0. Base damage 1000 * 1.0 = 1000
	# Delivery cost 1 AP
	# Rate Limit Compression applies on 1st delivery (count=1 -> 0.9 compression) -> damage = 900
	if not assert_eq(game_state.current_ap, initial_ap - 2, "AP should decrease by 2 total (1 for chip, 1 for delivery)"): tests_failed += 1
	if not assert_eq(game_state.active_context.size(), 0, "Context should be cleared after delivery"): tests_failed += 1
	if not assert_eq(game_state.crisis_hp, initial_hp - 900.0, "HP should decrease by 900"): tests_failed += 1
	
	# Test SLA Timer
	var initial_sla = game_state.sla_timer
	game_state._process(10.0)
	if not assert_eq(game_state.sla_timer, initial_sla - 10.0, "SLA should decrease by 10"): tests_failed += 1
	
	game_state._process(300.0)
	if not assert_eq(game_state.sla_timer, 0.0, "SLA should hit 0"): tests_failed += 1
	if not assert_eq(game_state.is_game_active, false, "Game should end on SLA 0"): tests_failed += 1
	
	# Cleanup
	Engine.unregister_singleton("EventBus")
	event_bus.free()
	Engine.unregister_singleton("GameState")
	game_state.free()
	
	if tests_failed == 0:
		print("test_state_machine PASSED")
		return true
	return false
