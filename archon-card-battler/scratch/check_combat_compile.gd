extends SceneTree

func _init() -> void:
	print("Preloading GameState.gd...")
	var script = load("res://Scripts/Logic/GameState.gd")
	if script == null:
		print("Failed to load GameState.gd!")
	else:
		print("Loaded GameState.gd successfully: ", script)
	quit()

