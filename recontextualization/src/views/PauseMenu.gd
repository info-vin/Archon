extends ColorRect

signal resume_game
signal save_progress
signal load_progress
signal quit_to_menu
signal quit_game

func _ready() -> void:
    $VBoxContainer/ResumeButton.pressed.connect(func(): resume_game.emit())
    $VBoxContainer/SaveButton.pressed.connect(func(): save_progress.emit())
    $VBoxContainer/LoadButton.pressed.connect(func(): load_progress.emit())
    $VBoxContainer/MenuButton.pressed.connect(func(): quit_to_menu.emit())
    $VBoxContainer/QuitButton.pressed.connect(func(): quit_game.emit())
    
    visibility_changed.connect(_on_visibility_changed)

func _on_visibility_changed() -> void:
    if visible:
        get_tree().paused = true
    else:
        get_tree().paused = false
