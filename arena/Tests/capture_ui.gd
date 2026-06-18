extends SceneTree

func _init() -> void:
	print("Starting UI Capture...")
	var root = get_root()
	
	# Load the main scene
	var main_scene = load("res://Scenes/Main/Main.tscn").instantiate()
	root.add_child(main_scene)
	
	# Wait a couple of frames to ensure UI layouts are updated
	await create_timer(1.0).timeout
	
	# Capture the screen
	var img = get_root().get_viewport().get_texture().get_image()
	img.save_png("res://proof_refactor_success.png")
	
	print("Capture saved to: res://proof_refactor_success.png")
	quit(0)
