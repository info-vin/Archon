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
	
	var game_board = null
	for c in root.get_children():
		if c.name == "GameBoard":
			game_board = c
			break
			
	if game_board:
		print("--- Scene Tree of GameBoard ---")
		game_board.print_tree_pretty()
	
	quit()
