extends SceneTree

func _init():
	print("--- Starting Headless Tests ---")
	
	# Clean up save file if exists to ensure statelessness
	if FileAccess.file_exists("user://savegame.save"):
		var dir = DirAccess.open("user://")
		if dir:
			dir.remove("savegame.save")
		print("Purged user://savegame.save")

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
		
	print("--- Test Results ---")
	print("Passed: ", tests_passed)
	print("Failed: ", tests_failed)
	
	if tests_failed > 0:
		quit(1)
	else:
		quit(0)
