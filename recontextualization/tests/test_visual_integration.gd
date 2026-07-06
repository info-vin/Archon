extends RefCounted

func run_tests(scene_tree: SceneTree) -> bool:
	print("Running test_visual_integration...")
	
	var passed = true
	var game_board_scene = preload("res://src/views/GameBoard.tscn")
	var game_board = game_board_scene.instantiate()
	scene_tree.root.add_child(game_board)
	
	var card = load("res://src/models/cards/resources/keyword_search.tres")
	
	# Simulate drawing a card directly
	game_board.anim_draw_card(card)
	
	print("Waiting for visual animation to complete...")
	await scene_tree.create_timer(1.0).timeout
	
	# Check if hand container has children
	var hand = game_board.get_node("MarginContainer/VBoxContainer/HandContainer")
	if hand.get_child_count() == 1:
		print("Test captured expected visual instantiation.")
	else:
		print("FAIL: Expected 1 children in hand, got ", hand.get_child_count())
		passed = false
	
	game_board.queue_free()
	
	if passed:
		print("test_visual_integration PASSED")
	return passed
