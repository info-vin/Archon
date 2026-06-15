extends SceneTree

func _init() -> void:
	print("Preloading test_game_state.gd...")
	var script = load("res://Tests/Unit/test_game_state.gd")
	if script == null:
		print("Failed to load script!")
	else:
		print("Loaded script successfully: ", script)
		print("Instantiating script...")
		var instance = script.new()
		print("Instantiated successfully: ", instance)
	quit()
