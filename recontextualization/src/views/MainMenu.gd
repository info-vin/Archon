extends Control

func _ready() -> void:
    $VBoxContainer/NewCareerButton.pressed.connect(_on_new_career_pressed)
    $VBoxContainer/ContinueButton.pressed.connect(_on_continue_pressed)
    $VBoxContainer/CardManagementButton.pressed.connect(_on_card_management_pressed)
    $VBoxContainer/QuitButton.pressed.connect(_on_quit_pressed)

func _on_new_career_pressed() -> void:
    var sm = get_node_or_null("/root/SaveManager")
    if sm != null:
        # Wipe run progress but maybe keep career level? For "New Career", maybe we reset career level too?
        # Actually, let's keep career level and just start the GameBoard
        sm.max_player_hp = 100.0
        sm.has_completed_tutorial = false
        sm.save_progress()
    get_tree().change_scene_to_file("res://src/views/GameBoard.tscn")

func _on_continue_pressed() -> void:
    get_tree().change_scene_to_file("res://src/views/GameBoard.tscn")

func _on_card_management_pressed() -> void:
    get_tree().change_scene_to_file("res://src/views/CardManagementMenu.tscn")

func _on_quit_pressed() -> void:
    get_tree().quit()
