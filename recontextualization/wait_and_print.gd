extends SceneTree

func _init():
	call_deferred("run_test")

func run_test():
	var root = get_root()
	
	# Instantiate autoload nodes to mimic the real game
	var sm = load("res://src/autoloads/SaveManager.gd").new()
	sm.name = "SaveManager"
	root.add_child(sm)
	
	var eb = load("res://src/autoloads/EventBus.gd").new()
	eb.name = "EventBus"
	root.add_child(eb)
	
	var gs = load("res://src/autoloads/GameState.gd").new()
	gs.name = "GameState"
	root.add_child(gs)
	
	var cr = load("res://src/managers/CardRegistry.gd").new()
	cr.name = "CardRegistry"
	root.add_child(cr)
	
	# Reset tutorial completed status
	sm.has_completed_tutorial = false
	sm.save_progress()
	
	var main_menu = load("res://src/views/MainMenu.tscn").instantiate()
	root.add_child(main_menu)
	main_scene_click(main_menu)

func main_scene_click(main_menu):
	main_menu._on_new_career_pressed()
	
	# Wait for GameBoard to settle
	await create_timer(1.0).timeout
	
	var gb = get_root().get_node("GameBoard")
	if gb:
		print("--- GameBoard HandContainer children count: ", gb.hand_container.get_child_count())
		print("--- GameBoard HandContainer children: ")
		for child in gb.hand_container.get_children():
			print(child.name, " (", child.get_class(), ")")
	else:
		print("--- GameBoard not found!")
	
	quit()
