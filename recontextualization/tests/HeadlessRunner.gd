extends SceneTree

# Pre-warm global class cache for headless execution to allow clean code in src/
var _warmup1 = preload("res://src/models/cards/CardData.gd")
var _warmup2 = preload("res://src/models/GameBalanceConfig.gd")
var _warmup3 = preload("res://src/models/cards/CardEffectResolver.gd")
var _warmup4 = preload("res://src/managers/BattleRuleEngine.gd")
var _warmup5 = preload("res://src/network/BackendClient.gd")
var _warmup6 = preload("res://src/network/MockDataGenerator.gd")
var _warmup7 = preload("res://src/managers/ProgressionSystem.gd")

func _init():
	print("--- Starting Headless Tests ---")
	
	# Clean up save file if exists to ensure statelessness
	if FileAccess.file_exists("user://archon_progress.json"):
		var dir = DirAccess.open("user://")
		if dir:
			dir.remove("archon_progress.json")
		print("Purged user://archon_progress.json")

	call_deferred("_run_tests")

func _run_tests():
	var tests_passed = 0
	var tests_failed = 0
	
	# Load tests
	var test_math = preload("res://tests/test_deck_math.gd").new()
	if test_math.run_tests():
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_client = preload("res://tests/test_backend_client.gd").new()
	if await test_client.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_visual = preload("res://tests/test_visual_integration.gd").new()
	if await test_visual.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_e2e = preload("res://tests/test_e2e_api_to_ui.gd").new()
	if await test_e2e.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_dnd = preload("res://tests/test_drag_and_drop.gd").new()
	if await test_dnd.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_sm = preload("res://tests/test_state_machine.gd").new()
	if test_sm.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_threats = preload("res://tests/test_composite_threats.gd").new()
	if test_threats.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1

	var test_sm_save = preload("res://tests/test_save_manager.gd").new()
	if test_sm_save.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_meta = preload("res://tests/test_meta_progression.gd").new()
	if test_meta.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1

	var test_fsm = preload("res://tests/test_tutorial_fsm.gd").new()
	if test_fsm.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	# Phase 5.8.9 Verification Tests
	var test_token = preload("res://tests/test_token_capping.gd").new()
	if test_token.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_progression = preload("res://tests/test_teammate_progression.gd").new()
	if test_progression.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_adaptation = preload("res://tests/test_behavior_adaptation.gd").new()
	if test_adaptation.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_dual_brain = preload("res://tests/test_dual_brain_logic.gd").new()
	if test_dual_brain.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	var test_graphrag = preload("res://tests/test_graphrag_chain.gd").new()
	if test_graphrag.run_tests(self):
		tests_passed += 1
	else:
		tests_failed += 1
		
	print("--- Test Results ---")
	print("Passed: ", tests_passed)
	print("Failed: ", tests_failed)
	
	if tests_failed > 0:
		quit(1)
	else:
		quit(0)
