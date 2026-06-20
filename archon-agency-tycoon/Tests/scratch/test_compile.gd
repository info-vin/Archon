extends SceneTree
func _initialize() -> void:
	var script = load("res://Scripts/Logic/TycoonManager.gd")
	print("Script loaded successfully: ", script != null)
	quit()
