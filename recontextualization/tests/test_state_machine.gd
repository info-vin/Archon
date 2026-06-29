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
	
	var initial_hp = game_state.enemy_hp
	var initial_ap = game_state.current_ap
	
	var card_script = preload("res://src/models/cards/CardData.gd")
	
	# Create a Data Chip
	var data_chip = card_script.new()
	data_chip.set("type", 2)
	data_chip.set("similarity", 0.9)
	data_chip.set("ap_cost", 1)
	
	# Emit card_played
	event_bus.card_played.emit(data_chip)
	
	if not assert_eq(game_state.current_ap, initial_ap - 1, "AP should decrease by 1"): tests_failed += 1
	if not assert_eq(game_state.active_context.size(), 1, "Context should have 1 card"): tests_failed += 1
	
	# Create an Action Chip
	var action_chip = card_script.new()
	action_chip.set("type", 1)
	action_chip.set("ap_cost", 2)
	
	event_bus.card_played.emit(action_chip)
	
	if not assert_eq(game_state.current_ap, initial_ap - 3, "AP should decrease by 2"): tests_failed += 1
	if not assert_eq(game_state.active_context.size(), 0, "Context should be cleared after action"): tests_failed += 1
	
	# Context had 1 card (similarity 0.9 > 0.5), purity = 1.0. Base damage 1000 * 1.0 = 1000
	if not assert_eq(game_state.enemy_hp, initial_hp - 1000.0, "HP should decrease by 1000"): tests_failed += 1
	
	# Cleanup
	Engine.unregister_singleton("EventBus")
	event_bus.free()
	Engine.unregister_singleton("GameState")
	game_state.free()
	
	if tests_failed == 0:
		print("test_state_machine PASSED")
		return true
	return false
