extends SceneTree

func _initialize() -> void:
	print("=== Running all tests headlessly ===")
	var test_files = [
		preload("res://Tests/Unit/test_agent_manager.gd"),
		preload("res://Tests/Unit/test_task_manager.gd"),
		preload("res://Tests/Unit/test_save_system.gd"),
		preload("res://Tests/Unit/test_tycoon_manager.gd"),
		preload("res://Tests/Unit/test_modular_agent.gd"),
		preload("res://Tests/Unit/test_office_view.gd"),
		preload("res://Tests/Unit/test_help_menu.gd"),
		preload("res://Tests/Unit/test_character_creator.gd")
	]
	
	var total_passed = 0
	var total_failed = 0
	for test_class in test_files:
		var test_instance = test_class.new()
		test_instance.tree = self
		await test_instance.run_test_suite()
		total_passed += test_instance.tests_passed
		total_failed += test_instance.tests_failed
		
	print("\n=== TOTAL PASSED: ", total_passed, " | TOTAL FAILED: ", total_failed, " ===")
	
	if total_failed > 0:
		quit(1)
	else:
		quit(0)
