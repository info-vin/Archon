extends Node

var transition_scene = "res://src/views/TransitionVideo.tscn"
var card_menu_scene = "res://src/views/CardManagementMenu.tscn"
var teammate_dashboard_scene = "res://src/views/TeammateDashboard.tscn"

@onready var view = get_parent()

var save_manager: Node:
	get:
		if Engine.has_singleton("SaveManager"):
			return Engine.get_singleton("SaveManager")
		return get_node_or_null("/root/SaveManager")

func _ready() -> void:
	if save_manager != null:
		view.set_initial_settings(save_manager.language, save_manager.bgm_volume)

	view.request_new_career.connect(_on_new_career_requested)
	view.request_continue.connect(_on_continue_requested)
	view.request_teammate_dashboard.connect(_on_teammate_dashboard_requested)
	view.request_card_management.connect(_on_card_management_requested)
	view.request_quit.connect(_on_quit_requested)
	view.request_language_change.connect(_on_language_change_requested)
	view.request_volume_change.connect(_on_volume_change_requested)

func _on_new_career_requested() -> void:
	if save_manager != null:
		save_manager.max_player_hp = 100.0
		save_manager.has_completed_tutorial = false
		save_manager.save_progress()
	if transition_scene: get_tree().change_scene_to_file(transition_scene)

func _on_continue_requested() -> void:
	if transition_scene: get_tree().change_scene_to_file(transition_scene)

func _on_card_management_requested() -> void:
	if card_menu_scene: get_tree().change_scene_to_file(card_menu_scene)

func _on_teammate_dashboard_requested() -> void:
	if teammate_dashboard_scene: get_tree().change_scene_to_file(teammate_dashboard_scene)

func _on_quit_requested() -> void:
	get_tree().quit()

func _on_language_change_requested(new_lang: String) -> void:
	if save_manager != null:
		save_manager.language = new_lang
		save_manager.save_progress()
		save_manager._apply_settings()

func _on_volume_change_requested(new_volume: float) -> void:
	if save_manager != null:
		save_manager.bgm_volume = new_volume
		save_manager.save_progress()
		save_manager._apply_settings()

