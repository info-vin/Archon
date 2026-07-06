extends Node
class_name CharacterDashboardController

@export var main_menu_scene: PackedScene

var view: Control
var save_manager: Node

func _init(v: Control = null) -> void:
	if v:
		_setup_with_view(v)

func _ready() -> void:
	if get_parent() and get_parent() is Control and view == null:
		_setup_with_view(get_parent())

func _setup_with_view(v: Control) -> void:
	view = v
	save_manager = view.get_node_or_null("/root/SaveManager")
	
	_connect_signals()
	_update_profile()

func _connect_signals() -> void:
	view.request_return_menu.connect(_on_return_menu)

func _update_profile() -> void:
	if save_manager == null: return
	
	var sector = save_manager.get_current_sector()
	var account_xp = save_manager.account_xp
	
	view.update_profile(sector, account_xp)

func _on_return_menu() -> void:
	if main_menu_scene:
		view.get_tree().change_scene_to_packed(main_menu_scene)
