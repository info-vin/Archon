extends Node

const SAVE_PATH = "user://archon_progress.json"

# --- RPG Balance Constants ---
const SECTOR_2_CR_THRESHOLD = 500
const SECTOR_3_CR_THRESHOLD = 1000
const BASE_XP_PER_LEVEL = 100.0

const REWARD_S_CR = 40
const REWARD_A_CR = 30
const REWARD_B_CR = 20

const REWARD_S_XP = 100.0
const REWARD_A_XP = 50.0
const REWARD_B_XP = 25.0

const LOSS_CR_PENALTY = 15

const CARD_KEYWORD = "keyword_search"
const CARD_DENSE = "dense_search"
const CARD_RERANKER = "reranker"
# -----------------------------


var career_level: int = 3
var max_player_hp: float = 100.0
var unlocked_action_cards: Array = ["keyword_search", "dense_search", "reranker"]
var equipped_action_cards: Array = ["keyword_search", "dense_search", "reranker"]
var has_completed_tutorial: bool = false
var language: String = "zh_TW"
var bgm_volume: float = 1.0

var player_inventory: Array = []
var material_inventory: Dictionary = {"data_core_s": 0, "data_core_a": 0, "data_core_b": 0, "scrap": 0}

# A+B+C Progression System
var clearance_rating: int = 0
var highest_sector: int = 1
var cognitive_level: int = 1
var current_xp: float = 0.0
var topology_points: int = 0
var unlocked_talents: Array = []

func _ready() -> void:
    load_progress()

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
        "unlocked_talents": unlocked_talents
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
        var data = json.data
        if typeof(data) == TYPE_DICTIONARY:
            career_level = data.get("career_level", 3)
            max_player_hp = data.get("max_player_hp", 100.0)
            unlocked_action_cards = data.get("unlocked_action_cards", ["keyword_search", "dense_search", "reranker"])
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
            
            _enforce_equipment_limit()
            _apply_settings()
            return
            
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
    unlocked_action_cards = ["keyword_search", "dense_search", "reranker"]
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
    _apply_settings()
    save_progress()

func wipe_run_progress() -> void:
    save_progress()

func get_current_sector() -> int:
    if clearance_rating >= SECTOR_3_CR_THRESHOLD:
        return 3
    elif clearance_rating >= SECTOR_2_CR_THRESHOLD:
        return 2
    else:
        return 1

func _check_level_up() -> void:
    var xp_needed = BASE_XP_PER_LEVEL * cognitive_level
    while current_xp >= xp_needed:
        current_xp -= xp_needed
        cognitive_level += 1
        topology_points += 1
        xp_needed = BASE_XP_PER_LEVEL * cognitive_level

func award_battle_loot(rank: String) -> void:
    var xp_gain = 0.0
    var cr_gain = 0
    if rank == "S":
        material_inventory["data_core_s"] = material_inventory.get("data_core_s", 0) + 1
        xp_gain = REWARD_S_XP
        cr_gain = REWARD_S_CR
    elif rank == "A":
        material_inventory["data_core_a"] = material_inventory.get("data_core_a", 0) + 1
        xp_gain = REWARD_A_XP
        cr_gain = REWARD_A_CR
    elif rank == "B":
        material_inventory["data_core_b"] = material_inventory.get("data_core_b", 0) + 1
        xp_gain = REWARD_B_XP
        cr_gain = REWARD_B_CR
        
    clearance_rating += cr_gain
    highest_sector = max(highest_sector, get_current_sector())
    
    current_xp += xp_gain
    _check_level_up()
        
    var drop_pool = [CARD_KEYWORD]
    var sec = get_current_sector()
    if sec >= 2:
        drop_pool.append(CARD_DENSE)
    if sec >= 3:
        drop_pool.append(CARD_RERANKER)
        
    var drop_card = drop_pool.pick_random()
    player_inventory.append({"base_id": drop_card, "level": 1})
    save_progress()

func penalize_battle_loss() -> void:
    clearance_rating = max(0, clearance_rating - LOSS_CR_PENALTY)
    save_progress()

