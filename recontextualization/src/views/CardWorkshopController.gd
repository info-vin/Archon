extends Node
class_name CardWorkshopController

const CATALYST_S = "data_core_s"
const CATALYST_A = "data_core_a"
const CATALYST_S_BONUS = 0.5
const CATALYST_A_BONUS = 0.2
const COGNITIVE_BONUS_MULT = 0.01
const COGNITIVE_BONUS_MAX = 0.20

@export_file("*.tscn") var game_board_scene: String

var view: Control
var save_manager: Node

var current_cards_in_furnace: Array = []
var current_catalyst: String = "none"

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
	_refresh_inventory_ui()

func _connect_signals() -> void:
	view.request_add_to_furnace.connect(_on_add_to_furnace)
	view.request_synthesize.connect(_on_synthesize_pressed)
	view.request_return_battle.connect(_on_return_battle)

func _refresh_inventory_ui() -> void:
	if not save_manager:
		return
	view.populate_inventory(save_manager.player_inventory)

func _on_add_to_furnace(card_data: Dictionary) -> void:
	if current_cards_in_furnace.size() < 3:
		if current_cards_in_furnace.size() > 0:
			var first_card = current_cards_in_furnace[0]
			if first_card.get("base_id") != card_data.get("base_id") or first_card.get("level") != card_data.get("level"):
				view.show_status("Error: Must use identical cards!")
				return
		
		current_cards_in_furnace.append(card_data)
		_update_furnace_ui()

func _update_furnace_ui() -> void:
	if current_cards_in_furnace.size() == 3:
		var target_level = current_cards_in_furnace[0].get("level", 1)
		var rate = _calculate_success_rate(target_level, current_catalyst)
		view.show_status("Ready! Success Rate: %.1f%%" % (rate * 100.0))
		view.update_furnace_count(current_cards_in_furnace.size())
	else:
		view.show_status("Furnace: %d/3 Cards" % current_cards_in_furnace.size())
		view.update_furnace_count(current_cards_in_furnace.size())

func _calculate_success_rate(level: int, catalyst: String) -> float:
	var bsr = max(0.10, 1.0 - (level * 0.15))
	var bonus = 0.0
	if catalyst == CATALYST_S:
		bonus = CATALYST_S_BONUS
	elif catalyst == CATALYST_A:
		bonus = CATALYST_A_BONUS
		
	var level_bonus = 0.0
	if save_manager:
		level_bonus = min(COGNITIVE_BONUS_MAX, save_manager.cognitive_level * COGNITIVE_BONUS_MULT)
		
	return min(1.0, bsr + bonus + level_bonus)

func _on_synthesize_pressed() -> void:
	if current_cards_in_furnace.size() < 3:
		return
		
	var target_level = current_cards_in_furnace[0].get("level", 1)
	var base_id = current_cards_in_furnace[0].get("base_id", "Unknown")
	var rate = _calculate_success_rate(target_level, current_catalyst)
	
	if save_manager:
		if current_catalyst != "none":
			if save_manager.material_inventory.has(current_catalyst) and save_manager.material_inventory[current_catalyst] > 0:
				save_manager.material_inventory[current_catalyst] -= 1
			else:
				view.show_status("Error: Catalyst missing!")
				return

		for c in current_cards_in_furnace:
			var idx = save_manager.player_inventory.find(c)
			if idx != -1:
				save_manager.player_inventory.remove_at(idx)
			
		if randf() <= rate:
			view.show_status("Synthesis SUCCESS!")
			save_manager.player_inventory.append({"base_id": base_id, "level": target_level + 1})
			view.play_success_anim()
		else:
			view.show_status("Synthesis FAILED... Yielded scrap.")
			save_manager.material_inventory["scrap"] = save_manager.material_inventory.get("scrap", 0) + 1
			view.play_failure_anim()
			
		save_manager.save_progress()
		
	current_cards_in_furnace.clear()
	current_catalyst = "none"
	_refresh_inventory_ui()
	_update_furnace_ui()

func _on_return_battle() -> void:
	if game_board_scene:
		view.get_tree().change_scene_to_file(game_board_scene)
