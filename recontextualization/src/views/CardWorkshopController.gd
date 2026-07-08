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
    view.request_buy_catalyst.connect(_on_buy_catalyst)

func _refresh_inventory_ui() -> void:
    if not save_manager or save_manager.player_inventory.size() == 0:
        # Inject mock data for visual testing
        var mock_inventory = [
            {"base_id": "keyword_search", "level": 1, "card_name": "深度注入"},
            {"base_id": "keyword_search", "level": 1, "card_name": "深度注入"},
            {"base_id": "keyword_search", "level": 1, "card_name": "深度注入"},
            {"base_id": "cyber_shield", "level": 2, "card_name": "量子護盾"},
            {"base_id": "cyber_shield", "level": 2, "card_name": "量子護盾"}
        ]
        view.populate_inventory(mock_inventory)
        
        # Pre-fill furnace for screenshot
        current_cards_in_furnace.clear()
        current_cards_in_furnace.append(mock_inventory[0])
        current_cards_in_furnace.append(mock_inventory[1])
        current_cards_in_furnace.append(mock_inventory[2])
        _update_furnace_ui()
        return

    view.populate_inventory(save_manager.player_inventory)

func _on_buy_catalyst() -> void:
    # Pseudo shop integration
    current_catalyst = CATALYST_S
    view.show_status("催化媒介已充能！")
    _update_furnace_ui()

func _on_add_to_furnace(card_data: Dictionary) -> void:
    var max_cards = 3
    if current_cards_in_furnace.size() < max_cards:
        if current_cards_in_furnace.size() > 0:
            var first_card = current_cards_in_furnace[0]
            if first_card.get("base_id") != card_data.get("base_id") or first_card.get("level") != card_data.get("level"):
                view.show_status("錯誤：融合需要相同的卡牌！")
                return
        
        current_cards_in_furnace.append(card_data)
        _update_furnace_ui()

func _update_furnace_ui() -> void:
    var max_cards = 3
    if current_cards_in_furnace.size() == max_cards:
        view.show_status("準備就緒")
    else:
        view.show_status("卡牌數量不足")
        
    if view.has_method("update_furnace_slots"):
        view.update_furnace_slots(current_cards_in_furnace)

func can_synthesize() -> bool:
    return current_cards_in_furnace.size() == 3

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
    var max_cards = 3
    if current_cards_in_furnace.size() < max_cards:
        return
        
    var target_level = current_cards_in_furnace[0].get("level", 1)
    var base_id = current_cards_in_furnace[0].get("base_id", "Unknown")
    var rate = _calculate_success_rate(target_level, current_catalyst)
    
    var is_success = true # Always success for demo/visual tests if save_manager is null
    
    if save_manager:
        if current_catalyst != "none":
            # For mockup purposes, we don't strictly deduct if they don't have it, since it's just a demo button
            pass

        for c in current_cards_in_furnace:
            var idx = save_manager.player_inventory.find(c)
            if idx != -1:
                save_manager.player_inventory.remove_at(idx)
            
        is_success = (randf() <= rate)
        if is_success:
            save_manager.player_inventory.append({"base_id": base_id, "level": target_level + 1})
        else:
            save_manager.material_inventory["scrap"] = save_manager.material_inventory.get("scrap", 0) + 1
            
        save_manager.save_progress()
        
    if is_success:
        view.show_status("轉換成功！")
        view.play_success_anim()
    else:
        view.show_status("轉換失敗... 獲得碎塊。")
        view.play_failure_anim()
        
    current_cards_in_furnace.clear()
    current_catalyst = "none"
    _refresh_inventory_ui()
    _update_furnace_ui()

func _on_return_battle() -> void:
    if game_board_scene:
        view.get_tree().change_scene_to_file(game_board_scene)
