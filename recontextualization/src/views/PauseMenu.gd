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
    $VBoxContainer/MenuButton.pressed.connect(func(): $MenuConfirm.popup_centered())
    $VBoxContainer/QuitButton.pressed.connect(func(): $QuitConfirm.popup_centered())
    
    $MenuConfirm.confirmed.connect(func(): quit_to_menu.emit())
    $QuitConfirm.confirmed.connect(func(): quit_game.emit())
    
    visibility_changed.connect(_on_visibility_changed)

func _on_visibility_changed() -> void:
    if visible:
        get_tree().paused = true
    else:
        get_tree().paused = false
