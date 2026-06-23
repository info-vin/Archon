extends SceneTree

func _init():
	print("Loading Main.tscn for screenshot...")
	var main_scene = load("res://Scenes/Main/Main.tscn")
	var instance = main_scene.instantiate()
	root.add_child(instance)
	
	# Create timer to wait for 1 frame/rendering
	# In a custom main loop, we must manually pump the tree or just wait a bit.
	var timer = Timer.new()
	timer.wait_time = 0.5
	timer.autostart = true
	timer.one_shot = true
	timer.timeout.connect(_on_timeout)
	root.add_child(timer)

func _on_timeout():
	print("Taking screenshot...")
	var img = root.get_viewport().get_texture().get_image()
	img.save_png("res://game_screenshot.png")
	print("Screenshot saved.")
	quit()
