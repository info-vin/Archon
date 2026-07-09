extends Node
class_name CardManagementMenuController

var game_board_scene = "res://src/views/GameBoard.tscn"
var teammate_dash_scene = "res://src/views/TeammateDashboard.tscn"
var main_menu_scene = "res://src/views/MainMenu.tscn"

var view: Control
var save_manager: Node

# Mock Database (Mapped from legacy DB IDs to Cyberpunk theme)
var mock_database = {
	"action_keyword": {"id": "action_keyword", "name_key": "card_name_keyword_search", "desc_key": "card_desc_keyword_search", "texture": "res://assets/images/action_keyword.png", "cost": 1},
	"action_dense": {"id": "action_dense", "name_key": "card_name_dense_search", "desc_key": "card_desc_dense_search", "texture": "res://assets/images/action_dense.png", "cost": 2},
	"action_reranker": {"id": "action_reranker", "name_key": "card_name_reranker", "desc_key": "card_desc_reranker", "texture": "res://assets/images/action_reranker.png", "cost": 3},
	"action_emp": {"id": "action_emp", "name_key": "card_name_emp_blast", "desc_key": "card_desc_emp_blast", "texture": "res://assets/images/action_emp.png", "cost": 5},
	"action_leech": {"id": "action_leech", "name_key": "card_name_data_leech", "desc_key": "card_desc_data_leech", "texture": "res://assets/images/action_leech.png", "cost": 1}
}

func _init(v: Control = null) -> void:
	if v:
		_setup_with_view(v)

func _ready() -> void:
	if get_parent() and get_parent() is Control and view == null:
		await get_parent().ready
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
	
	if "equipped_list" in view and view.equipped_list and view.equipped_list.has_signal("card_dropped"):
		view.equipped_list.card_dropped.connect(_on_card_dropped.bind(true))
	if "unlocked_list" in view and view.unlocked_list and view.unlocked_list.has_signal("card_dropped"):
		view.unlocked_list.card_dropped.connect(_on_card_dropped.bind(false))
		
	if "btn_save" in view and view.btn_save:
		view.btn_save.pressed.connect(_on_save_loadout)

func _inject_mock_data():
	if not save_manager: return
	if save_manager.unlocked_action_cards.size() == 0:
		save_manager.unlocked_action_cards = mock_database.keys()
		save_manager.equipped_action_cards = ["action_keyword", "action_dense", "action_reranker"]
		save_manager.save_progress()

func _refresh_lists() -> void:
	_inject_mock_data() # Force inject if empty
	
	var max_cards = 3
	var max_tokens = 10 # Default squad tokens
	
	if save_manager:
		max_cards = save_manager.get_max_equipped_cards()
		
	var equipped_ids = save_manager.equipped_action_cards if save_manager else ["action_keyword", "action_reranker"]
	var unlocked_ids = mock_database.keys() # Force show all cards for UI preview
	
	var current_cost = 0
	var equipped_cards = []
	for cid in equipped_ids:
		if mock_database.has(cid):
			var c = mock_database[cid].duplicate()
			c["name"] = tr(c["name_key"])
			c["stats"] = "%s: %d\n%s: %s" % [tr("menu_cost_limit"), c["cost"], tr("menu_effect"), tr(c["desc_key"])]
			equipped_cards.append(c)
			current_cost += c["cost"]
			
	var equipable_cards = []
	for cid in unlocked_ids:
		if not cid in equipped_ids and mock_database.has(cid):
			var c = mock_database[cid].duplicate()
			c["name"] = tr(c["name_key"])
			c["stats"] = "%s: %d\n%s: %s" % [tr("menu_cost_limit"), c["cost"], tr("menu_effect"), tr(c["desc_key"])]
			equipable_cards.append(c)
			
	if view.has_method("update_limit_label"):
		view.update_limit_label(equipped_cards.size(), max_cards, current_cost, max_tokens)
	if view.has_method("populate_lists"):
		view.populate_lists(equipable_cards, equipped_cards)
	
	if "stat_cost" in view and view.stat_cost:
		view.stat_cost.text = "%s: %d Token" % [tr("menu_base_cost"), current_cost]
		view.stat_upload.text = "%s: %d Mbps" % [tr("menu_upload_rate"), (12 + (equipped_cards.size() * 5))]
		view.stat_cdr.text = "%s: +%d%%" % [tr("menu_cdr"), (current_cost * 5)]
		view.stat_stealth.text = "%s: +%d%%" % [tr("menu_stealth"), (current_cost * 2)]

func _on_card_dropped(card_node: Node, target_is_equipped: bool) -> void:
	if not card_node.has_meta("card_id"): return
	var card_id = card_node.get_meta("card_id")
	
	var currently_equipped = false
	if save_manager and card_id in save_manager.equipped_action_cards:
		currently_equipped = true
		
	if target_is_equipped and not currently_equipped:
		_on_equip_card(card_id)
	elif not target_is_equipped and currently_equipped:
		_on_unequip_card(card_id)

func _on_equip_card(card_id: String) -> void:
	if not save_manager: return
	var max_cards = save_manager.get_max_equipped_cards()
	
	if not card_id in save_manager.equipped_action_cards:
		if save_manager.equipped_action_cards.size() >= max_cards:
			save_manager.equipped_action_cards.pop_front() # Auto-kick oldest
		save_manager.equipped_action_cards.append(card_id)
		save_manager.save_progress()
		_refresh_lists()

func _on_unequip_card(card_id: String) -> void:
	if not save_manager: return
	if card_id in save_manager.equipped_action_cards:
		save_manager.equipped_action_cards.erase(card_id)
		save_manager.save_progress()
		_refresh_lists()

func _on_save_loadout() -> void:
	var loadout_name = view.input_loadout.text.strip_edges()
	if loadout_name == "":
		loadout_name = "Loadout-Auto"
		
	if OS.has_feature("dedicated_server"):
		loadout_name = "Loadout-Auto-Headless"
		
	print("[Loadout Saved] ", loadout_name)
	# Future: save_manager.save_loadout(loadout_name, equipped_action_cards)


func _on_return_menu() -> void:
	if main_menu_scene:
		view.get_tree().change_scene_to_file(main_menu_scene)

func _on_teammate_dash() -> void:
	if teammate_dash_scene:
		view.get_tree().change_scene_to_file(teammate_dash_scene)

func _on_start_dive() -> void:
	if game_board_scene:
		view.get_tree().change_scene_to_file(game_board_scene)
