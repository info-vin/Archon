extends Node
class_name CardManagementMenuController

var game_board_scene = "res://src/views/GameBoard.tscn"
var teammate_dash_scene = "res://src/views/TeammateDashboard.tscn"
var main_menu_scene = "res://src/views/MainMenu.tscn"

var view: Control
var save_manager: Node

# Mock Database (Mapped from legacy DB IDs to Cyberpunk theme)
var mock_database = {
	"keyword_search": {"id": "keyword_search", "name": "基礎覆寫", "stats": "Cost: 1\n效果: 破解基礎防火牆", "texture": "res://assets/images/chip_green_target.png", "cost": 1},
	"dense_search": {"id": "dense_search", "name": "深度注入", "stats": "Cost: 2\n效果: 取得節點最高權限", "texture": "res://assets/images/chip_green_target.png", "cost": 2},
	"reranker": {"id": "reranker", "name": "量子護盾", "stats": "Cost: 2\n效果: 抵擋一次追蹤", "texture": "res://assets/images/chip_red_noise.png", "cost": 2},
	"filter_by_date": {"id": "filter_by_date", "name": "神經毒素", "stats": "Cost: 3\n效果: 每秒損毀目標節點", "texture": "res://assets/images/chip_red_noise.png", "cost": 3},
	"author_query": {"id": "author_query", "name": "透視掃描", "stats": "Cost: 1\n效果: 顯示隱藏路徑", "texture": "res://assets/images/chip_green_target.png", "cost": 1},
	"web_crawler": {"id": "web_crawler", "name": "核心超頻", "stats": "Cost: 3\n效果: 技能冷卻減半", "texture": "res://assets/images/chip_red_noise.png", "cost": 3}
}

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

func _inject_mock_data():
	if not save_manager: return
	if save_manager.unlocked_action_cards.size() == 0:
		save_manager.unlocked_action_cards = ["hack_basic", "hack_adv", "def_shield", "atk_virus", "util_scan", "util_overclock"]
		save_manager.equipped_action_cards = ["hack_basic", "def_shield"]
		save_manager.save_progress()

func _refresh_lists() -> void:
	_inject_mock_data() # Force inject if empty
	
	var max_cards = 3
	var max_tokens = 10 # Default squad tokens
	
	if save_manager:
		max_cards = save_manager.get_max_equipped_cards()
		
	var equipped_ids = save_manager.equipped_action_cards if save_manager else ["keyword_search", "reranker"]
	var unlocked_ids = save_manager.unlocked_action_cards if save_manager else mock_database.keys()
	
	var current_cost = 0
	var equipped_cards = []
	for cid in equipped_ids:
		if mock_database.has(cid):
			equipped_cards.append(mock_database[cid])
			current_cost += mock_database[cid]["cost"]
			
	var equipable_cards = []
	for cid in unlocked_ids:
		if not cid in equipped_ids and mock_database.has(cid):
			equipable_cards.append(mock_database[cid])
			
	view.update_limit_label(equipped_cards.size(), max_cards, current_cost, max_tokens)
	view.populate_lists(equipable_cards, equipped_cards)

func _on_equip_card(card_id: String) -> void:
	if not save_manager: return
	var max_cards = save_manager.get_max_equipped_cards()
	if save_manager.equipped_action_cards.size() < max_cards:
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
