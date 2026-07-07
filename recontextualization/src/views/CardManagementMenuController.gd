extends Node
class_name CardManagementMenuController

var game_board_scene = "res://src/views/GameBoard.tscn"
var teammate_dash_scene = "res://src/views/TeammateDashboard.tscn"
var main_menu_scene = "res://src/views/MainMenu.tscn"

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
	_refresh_lists()

func _connect_signals() -> void:
	view.request_equip_card.connect(_on_equip_card)
	view.request_unequip_card.connect(_on_unequip_card)
	view.request_return_menu.connect(_on_return_menu)
	view.request_teammate_dash.connect(_on_teammate_dash)
	view.request_start_dive.connect(_on_start_dive)

func _refresh_lists() -> void:
	if not save_manager: return
	
	var max_cards = save_manager.get_max_equipped_cards()
	var current_cards = save_manager.equipped_action_cards.size()
	view.update_limit_label(current_cards, max_cards)
	
	var equipable_cards = []
	for card_id in save_manager.unlocked_action_cards:
		if not card_id in save_manager.equipped_action_cards:
			equipable_cards.append(card_id)
			
	var equipped_cards = []
	for card_id in save_manager.equipped_action_cards:
		equipped_cards.append(card_id)
		
	view.populate_lists(equipable_cards, equipped_cards)

func _on_equip_card(card_id: String) -> void:
	if not save_manager: return
	if save_manager.equipped_action_cards.size() < save_manager.get_max_equipped_cards():
		if not card_id in save_manager.equipped_action_cards:
			save_manager.equipped_action_cards.append(card_id)
			save_manager.save_progress()
			_refresh_lists()

func _on_unequip_card(card_id: String) -> void:
	if not save_manager: return
	if card_id in save_manager.equipped_action_cards:
		save_manager.equipped_action_cards.erase(card_id)
		save_manager.save_progress()
		_refresh_lists()

func _on_return_menu() -> void:
	if main_menu_scene:
		view.get_tree().change_scene_to_file(main_menu_scene)

func _on_teammate_dash() -> void:
	if teammate_dash_scene:
		view.get_tree().change_scene_to_file(teammate_dash_scene)

func _on_start_dive() -> void:
	if game_board_scene:
		view.get_tree().change_scene_to_file(game_board_scene)
