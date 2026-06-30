extends SceneTree

func _init():
	print("--- Running Godot Test ---")
	call_deferred("run_test")

func run_test():
	# Load main menu and click New Career
	var root = get_root()
	var main_scene = load("res://src/views/MainMenu.tscn").instantiate()
	root.add_child(main_scene)
	main_scene._on_new_career_pressed()
	
	# Wait 2 seconds for GameBoard to load and Tutorial to show
	await create_timer(2.0).timeout
	
	print("--- Tree ---")
	var gb = root.get_node("GameBoard")
	if gb:
		gb.print_tree_pretty()
	else:
		print("GameBoard not found!")
	quit()
