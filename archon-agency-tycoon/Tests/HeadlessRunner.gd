extends SceneTree

func _initialize() -> void:
	print("=== Running all tests headlessly ===")
	
	# Clean Room Protocol: Remove savegame to prevent state pollution
	if FileAccess.file_exists("user://savegame.save"):
		DirAccess.remove_absolute("user://savegame.save")
		print("Cleaned up old savegame.save")
	
	# Manually inject Autoloads for -s mode
	var event_bus = preload("res://Scripts/Autoloads/EventBus.gd").new()
	event_bus.name = "EventBus"
	root.add_child(event_bus)
	
	var sim_engine = preload("res://Scripts/Logic/SimulationEngine.gd").new()
	sim_engine.name = "SimulationEngine"
	root.add_child(sim_engine)
	
	var audio_mgr = preload("res://Scripts/Autoloads/AudioManager.gd").new()
	audio_mgr.name = "AudioManager"
	root.add_child(audio_mgr)
	
	var test_files = [
		preload("res://Tests/Unit/test_agent_manager.gd"),
		preload("res://Tests/Unit/test_task_manager.gd"),
		preload("res://Tests/Unit/test_save_system.gd"),
		preload("res://Tests/Unit/test_tycoon_manager.gd"),
		preload("res://Tests/Unit/test_modular_agent.gd"),
		preload("res://Tests/Unit/test_office_view.gd"),
		preload("res://Tests/Unit/test_help_menu.gd"),
		preload("res://Tests/Unit/test_character_creator.gd"),
		preload("res://Tests/Unit/test_config_injection.gd"),
		preload("res://Tests/Unit/test_l2_main_integration.gd")
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
