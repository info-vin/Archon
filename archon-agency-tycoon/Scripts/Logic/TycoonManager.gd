extends Node
class_name TycoonManager

var save_adapter: SaveAdapter

var funds: int = 500
var reputation: int = 100
var current_phase: int = 1

func set_save_adapter(adapter: SaveAdapter) -> void:
    save_adapter = adapter

func save_game() -> bool:
    if save_adapter == null:
        push_error("Cannot save: No SaveAdapter provided.")
        return false
        
    var data = {
        "funds": funds,
        "reputation": reputation,
        "current_phase": current_phase
    }
    
    return save_adapter.save_data(data)

func load_game() -> bool:
    if save_adapter == null:
        push_error("Cannot load: No SaveAdapter provided.")
        return false
        
    var data = save_adapter.load_data()
    if data.is_empty():
        return false
        
    if data.has("funds"): funds = data["funds"]
    if data.has("reputation"): reputation = data["reputation"]
    if data.has("current_phase"): current_phase = data["current_phase"]
    
    return true

func setup_connections(task_manager) -> void:
    if not task_manager.task_completed.is_connected(_on_task_completed):
        task_manager.task_completed.connect(_on_task_completed)

func _on_task_completed(task_id: int, reward: int) -> void:
    funds += reward

