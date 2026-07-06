extends Node

# Reference to the View (Parent node)
@onready var view = get_parent()

func _ready() -> void:
	# 1. Initialize View from Data/State
	var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
	if sm != null:
		view.set_initial_settings(sm.language, sm.bgm_volume)

	# 2. Connect View Signals to Controller Logic
	view.request_new_career.connect(_on_new_career_requested)
	view.request_continue.connect(_on_continue_requested)
	view.request_card_management.connect(_on_card_management_requested)
	view.request_quit.connect(_on_quit_requested)
	view.request_language_change.connect(_on_language_change_requested)
	view.request_volume_change.connect(_on_volume_change_requested)

func _on_new_career_requested() -> void:
	var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
	if sm != null:
		sm.max_player_hp = 100.0
		sm.has_completed_tutorial = false
		sm.save_progress()
	get_tree().change_scene_to_file("res://src/views/TransitionVideo.tscn")

func _on_continue_requested() -> void:
	get_tree().change_scene_to_file("res://src/views/TransitionVideo.tscn")

func _on_card_management_requested() -> void:
	get_tree().change_scene_to_file("res://src/views/CardManagementMenu.tscn")

func _on_quit_requested() -> void:
	get_tree().quit()

func _on_language_change_requested(new_lang: String) -> void:
	var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
	if sm != null:
		sm.language = new_lang
		sm.save_progress()
		sm._apply_settings()

func _on_volume_change_requested(new_volume: float) -> void:
	var sm: Node = (Engine.get_singleton("SaveManager") if Engine.has_singleton("SaveManager") else get_node_or_null("/root/SaveManager"))
	if sm != null:
		sm.bgm_volume = new_volume
		sm.save_progress()
		sm._apply_settings()
