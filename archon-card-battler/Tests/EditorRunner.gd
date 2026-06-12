@tool
extends EditorScript

func _run() -> void:
	print("=== Running all tests in Godot Editor ===")
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
		# Use reflection/method calls since MiniTest now has run_test_suite()
		test_instance.run_test_suite()
		total_passed += test_instance.tests_passed
		total_failed += test_instance.tests_failed
		
	print("\n=== TOTAL PASSED: ", total_passed, " | TOTAL FAILED: ", total_failed, " ===")
