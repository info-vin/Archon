extends Control

@onready var video_player: VideoStreamPlayer = $VideoStreamPlayer

func _ready() -> void:
    video_player.play()
    video_player.finished.connect(_on_video_finished)

func _input(event: InputEvent) -> void:
    if (event is InputEventKey and event.pressed) or (event is InputEventMouseButton and event.pressed):
        _skip_intro()

func _on_video_finished() -> void:
    _skip_intro()

func _skip_intro() -> void:
    get_tree().change_scene_to_file("res://src/views/GameBoard.tscn")
