extends SceneTree

func _init():
	call_deferred("run_test")

func run_test():
	var main_menu = load("res://src/views/MainMenu.tscn").instantiate()
	root.add_child(main_menu)
	print("--- Main Menu Loaded ---")
	
	main_menu._on_new_career_pressed()
	print("--- Clicked New Career ---")
	
	await create_timer(1.0).timeout
	
	print("--- Scene Tree after transition ---")
	if current_scene:
		print("Current Scene: ", current_scene.name)
		print_tree_pretty(current_scene, "")
	else:
		print("Current scene is null. Root children:")
		for child in root.get_children():
			print_tree_pretty(child, "")
	
	quit()

func print_tree_pretty(node: Node, indent: String):
	var line = indent + node.name + " (" + node.get_class() + ")"
	if node is CanvasItem and node.is_class("Control"):
		line += " visible: " + str(node.visible)
	elif node is CanvasLayer:
		line += " visible: " + str(node.visible)
	print(line)
	for child in node.get_children():
		print_tree_pretty(child, indent + "  ")

