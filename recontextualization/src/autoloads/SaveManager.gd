extends Node

const SAVE_PATH = "user://archon_progress.json"

var career_level: int = 3
var max_player_hp: float = 100.0
var unlocked_action_cards: Array = ["keyword_search", "dense_search", "reranker"]
var equipped_action_cards: Array = ["keyword_search", "dense_search", "reranker"]
var has_completed_tutorial: bool = false

func _ready() -> void:
    load_progress()

func get_max_equipped_cards() -> int:
    # 3 + (career_level - 3) = career_level
    return max(3, career_level)

func save_progress() -> void:
    var data = {
        "career_level": career_level,
        "max_player_hp": max_player_hp,
        "unlocked_action_cards": unlocked_action_cards,
        "equipped_action_cards": equipped_action_cards,
        "has_completed_tutorial": has_completed_tutorial
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
            _enforce_equipment_limit()
            return
            
    _reset_to_default()

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
    save_progress()

func wipe_run_progress() -> void:
    # Called when Game Over happens. We keep meta progression but could reset other things if needed.
    # In Maaack, campaignLevel is reset. Here, we don't have a campaign level yet, 
    # but we might just reload the MainMenu. We persist the meta-progression.
    save_progress()

