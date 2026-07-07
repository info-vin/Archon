extends Node

const SAVE_PATH = "user://archon_progress.json"

var career_level: int = 3
var max_player_hp: float = 100.0
var unlocked_action_cards: Array = ["keyword_search", "dense_search", "reranker", "filter_by_date", "author_query", "web_crawler"]
var equipped_action_cards: Array = ["keyword_search", "dense_search", "reranker"]
var has_completed_tutorial: bool = false
var language: String = "zh_TW"
var bgm_volume: float = 1.0

var player_inventory: Array = []
var material_inventory: Dictionary = {"data_core_s": 0, "data_core_a": 0, "data_core_b": 0, "scrap": 0}

# A+B+C Progression System (Data Only)
var clearance_rating: int = 0
var highest_sector: int = 1
var cognitive_level: int = 1
var current_xp: float = 0.0
var topology_points: int = 0
var unlocked_talents: Array = []
var teammates: Array = []

func _ready() -> void:
    load_progress()
    var game_state = get_node_or_null("/root/GameState")
    if game_state and game_state.has_signal("game_over"):
        game_state.game_over.connect(_on_game_over)

func _on_game_over(is_victory: bool, rank: String = "") -> void:
    if is_victory:
        ProgressionSystem.award_battle_loot(self, rank)
    else:
        ProgressionSystem.penalize_battle_loss(self)

func get_max_equipped_cards() -> int:
    return max(3, career_level)

func save_progress() -> void:
    var data = {
        "career_level": career_level,
        "max_player_hp": max_player_hp,
        "unlocked_action_cards": unlocked_action_cards,
        "equipped_action_cards": equipped_action_cards,
        "has_completed_tutorial": has_completed_tutorial,
        "language": language,
        "bgm_volume": bgm_volume,
        "player_inventory": player_inventory,
        "material_inventory": material_inventory,
        "clearance_rating": clearance_rating,
        "highest_sector": highest_sector,
        "cognitive_level": cognitive_level,
        "current_xp": current_xp,
        "topology_points": topology_points,
        "unlocked_talents": unlocked_talents,
        "teammates": teammates
    }
    var json_string = JSON.stringify(data)
    var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file:
        file.store_string(json_string)
        file.close()

func load_progress() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        _reset_to_default()
        return
        
    var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
    if not file:
        _reset_to_default()
        return
        
    var json_string = file.get_as_text()
    file.close()
    
    var json = JSON.new()
    var error = json.parse(json_string)
    if error == OK:
        _parse_loaded_data(json.data)
    else:
        _reset_to_default()

func _parse_loaded_data(data) -> void:
    if typeof(data) == TYPE_DICTIONARY:
        career_level = data.get("career_level", 3)
        max_player_hp = data.get("max_player_hp", 100.0)
        unlocked_action_cards = data.get("unlocked_action_cards", ["keyword_search", "dense_search", "reranker", "filter_by_date", "author_query", "web_crawler"])
        equipped_action_cards = data.get("equipped_action_cards", ["keyword_search", "dense_search", "reranker"])
        has_completed_tutorial = data.get("has_completed_tutorial", false)
        language = data.get("language", "zh_TW")
        bgm_volume = data.get("bgm_volume", 1.0)
        player_inventory = data.get("player_inventory", [])
        
        var saved_mats = data.get("material_inventory", {})
        material_inventory = {
            "data_core_s": saved_mats.get("data_core_s", 0),
            "data_core_a": saved_mats.get("data_core_a", 0),
            "data_core_b": saved_mats.get("data_core_b", 0),
            "scrap": saved_mats.get("scrap", 0)
        }
        
        clearance_rating = data.get("clearance_rating", 0)
        highest_sector = data.get("highest_sector", 1)
        cognitive_level = data.get("cognitive_level", 1)
        current_xp = data.get("current_xp", 0.0)
        topology_points = data.get("topology_points", 0)
        unlocked_talents = data.get("unlocked_talents", [])
        teammates = data.get("teammates", [])
        
        _enforce_equipment_limit()
        _apply_settings()
    else:
        _reset_to_default()

func _apply_settings() -> void:
    TranslationServer.set_locale(language)
    var bus_idx = AudioServer.get_bus_index("Master")
    if bus_idx >= 0:
        AudioServer.set_bus_volume_db(bus_idx, linear_to_db(bgm_volume))

func _enforce_equipment_limit() -> void:
    var limit = get_max_equipped_cards()
    if equipped_action_cards.size() > limit:
        equipped_action_cards = equipped_action_cards.slice(0, limit)
        save_progress()

func _reset_to_default() -> void:
    career_level = 3
    max_player_hp = 100.0
    unlocked_action_cards = ["keyword_search", "dense_search", "reranker", "filter_by_date", "author_query", "web_crawler"]
    equipped_action_cards = ["keyword_search", "dense_search", "reranker"]
    has_completed_tutorial = false
    language = "zh_TW"
    bgm_volume = 1.0
    player_inventory = []
    material_inventory = {"data_core_s": 0, "data_core_a": 0, "data_core_b": 0, "scrap": 0}
    clearance_rating = 0
    highest_sector = 1
    cognitive_level = 1
    current_xp = 0.0
    topology_points = 0
    unlocked_talents = []
    teammates = []
    _apply_settings()
    save_progress()

func wipe_run_progress() -> void:
    save_progress()
