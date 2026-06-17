extends SceneTree

func _init():
	var main_scene = load("res://Scenes/Main/Main.tscn")
	if not main_scene:
		print("Error: Could not load Main.tscn")
		quit(1)
		return
		
	var root_node = main_scene.instantiate()
	root_node.instant_positioning = true
	root.add_child(root_node)
	
	# Wait a few frames for the UI to layout and Sprites to position
	process_frame.connect(_on_frame)

var frame_count = 0
func _on_frame():
	frame_count += 1
	if frame_count == 10:
		var img = root.get_viewport().get_texture().get_image()
		var dest_path = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/screenshots/ui_screenshot.png"
		var err = img.save_png(dest_path)
		if err == OK:
			print("🟢 SUCCESSFULLY EXPORTED UI SCREENSHOT TO: ", dest_path)
		else:
			print("🔴 FAILED TO EXPORT UI SCREENSHOT: ", err)
		quit(0)