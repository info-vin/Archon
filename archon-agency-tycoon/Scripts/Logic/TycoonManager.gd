extends Node
class_name TycoonManager

var save_adapter: SaveAdapter

var funds: int = 500
var reputation: int = 100
var current_phase: int = 1

# Crisis management: dictionary of room_name -> tick_duration
var active_crises: Dictionary = {}

signal crisis_spawned(room_name: String)
signal crisis_spread(from_room: String, to_room: String)
signal crisis_resolved(room_name: String)

func set_save_adapter(adapter: SaveAdapter) -> void:
    save_adapter = adapter

func save_game() -> bool:
    if save_adapter == null:
        push_error("Cannot save: No SaveAdapter provided.")
        return false
        
    var data = {
        "funds": funds,
        "reputation": reputation,
        "current_phase": current_phase,
        "active_crises": active_crises
    }
    
    var result = save_adapter.save_data(data)
    if result is bool:
        return result
    return await result

func load_game() -> bool:
    if save_adapter == null:
        push_error("Cannot load: No SaveAdapter provided.")
        return false
        
    var data = save_adapter.load_data()
    if data is Dictionary:
        if data.is_empty():
            return false
        _apply_save_data(data)
        return true
    
    var awaited_data = await data
    if awaited_data.is_empty():
        return false
    _apply_save_data(awaited_data)
    return true

func _apply_save_data(data: Dictionary) -> void:
    if data.has("funds"): funds = int(data["funds"])
    if data.has("reputation"): reputation = int(data["reputation"])
    if data.has("current_phase"): current_phase = int(data["current_phase"])
    if data.has("active_crises"): active_crises = data["active_crises"]

func setup_connections(task_manager) -> void:
    if not task_manager.task_completed.is_connected(_on_task_completed):
        task_manager.task_completed.connect(_on_task_completed)
    if not task_manager.rush_failed.is_connected(_on_rush_failed):
        task_manager.rush_failed.connect(_on_rush_failed)

func spawn_crisis(room_name: String) -> void:
    if not active_crises.has(room_name):
        active_crises[room_name] = 0
        crisis_spawned.emit(room_name)

func _on_task_completed(task_id: int, reward: int) -> void:
    funds += reward

func _on_rush_failed(task_id: int, agent_id: int) -> void:
    reputation = max(0, reputation - 10)
    # Map agent role to room name
    var room_name = "DevRoom"
    spawn_crisis(room_name)

# Process crisis spreading and energy drain
func process_crisis_tick(agent_manager: AgentManager) -> void:
    var rooms_to_drain = active_crises.keys()
    
    # Adjacency map for room spreading
    var adjacencies = {
        "DevRoom": ["SalesRoom", "BreakRoom"],
        "SalesRoom": ["DevRoom", "QARoom"],
        "QARoom": ["SalesRoom", "BreakRoom"],
        "BreakRoom": ["DevRoom", "QARoom"]
    }
    
    for room in rooms_to_drain:
        active_crises[room] += 1
        var duration = active_crises[room]
        
        # 1. Drain energy from agents in this room dynamically by role mapping
        for i in range(agent_manager.agents.size()):
            var agent = agent_manager.agents[i]
            var matches_room = false
            if room == "DevRoom" and agent.role == AgentResource.AgentRole.DEV: matches_room = true
            elif room == "SalesRoom" and agent.role == AgentResource.AgentRole.SALES: matches_room = true
            elif room == "QARoom" and agent.role == AgentResource.AgentRole.QA: matches_room = true
            
            if matches_room:
                agent_manager.drain_agent_energy(i, 5)
            
        # 2. Spread crisis if it has lasted > 3 ticks (20% chance)
        if duration > 3 and randf() <= 0.2:
            var adj_list = adjacencies.get(room, [])
            if adj_list.size() > 0:
                var target_room = adj_list[randi() % adj_list.size()]
                if not active_crises.has(target_room):
                    spawn_crisis(target_room)
                    crisis_spread.emit(room, target_room)

func resolve_crisis(room_name: String, qa_agent) -> void:
    if not active_crises.has(room_name):
        return
        
    # Crisis resolves faster with high debug_logic
    var resolution_power = 1 + int(qa_agent.debug_logic / 5)
    
    # We reduce the duration or directly resolve it if it's worked on
    active_crises.erase(room_name)
    crisis_resolved.emit(room_name)


