extends SceneTree

func _init() -> void:
	print("=== Running all tests headlessly ===")
	var test_files = [
		preload("res://Tests/Unit/test_card_stats.gd"),
		preload("res://Tests/Unit/test_git_parser.gd"),
		preload("res://Tests/Unit/test_combat_logic.gd"),
		preload("res://Tests/Unit/test_deck_manager.gd")
	]
	
	var total_passed = 0
	var total_failed = 0
	for test_class in test_files:
		var test_instance = test_class.new()
		test_instance.run_test_suite()
		total_passed += test_instance.tests_passed
		total_failed += test_instance.tests_failed
		
	print("\n=== TOTAL PASSED: ", total_passed, " | TOTAL FAILED: ", total_failed, " ===")
	
	if total_failed > 0:
		quit(1)
	else:
		quit(0)
