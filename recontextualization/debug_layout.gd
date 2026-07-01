extends SceneTree

func _init():
    var timer = create_timer(0.5)
    await timer.timeout
    
    var board = preload("res://src/views/GameBoard.tscn").instantiate()
    root.add_child(board)
    var t_overlay = preload("res://src/views/tutorial/TutorialOverlay.tscn").instantiate()
    root.add_child(t_overlay)
    
    await create_timer(0.5).timeout
    
    var play_area = board.get_node("MarginContainer/VBoxContainer/PlayArea")
    print("=== LAYOUT DEBUG ===")
    print("PlayArea Global Pos: ", play_area.global_position)
    print("PlayArea Size: ", play_area.size)
    print("PlayArea Mouse Filter: ", play_area.mouse_filter)
    print("PlayArea size_flags_horizontal: ", play_area.size_flags_horizontal)
    
    var dialog = t_overlay.get_node("DialogBox")
    print("DialogBox Global Pos: ", dialog.global_position)
    print("DialogBox Size: ", dialog.size)
    
    print("=== END ===")
    quit()
