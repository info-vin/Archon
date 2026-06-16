extends Node
class_name TycoonManager

var save_adapter: SaveAdapter
var config: Resource

var funds: int = 500
var reputation: int = 100
var current_phase: int = 1

# Crisis management: dictionary of room_name -> tick_duration
var active_crises: Dictionary = {}

signal crisis_spawned(room_name: String)
signal crisis_spread(from_room: String, to_room: String)
signal crisis_resolved(room_name: String)

func _init() -> void:
    var res = load("res://GameConfig.tres")
    if res:
        set_config(res)

func set_save_adapter(adapter: SaveAdapter) -> void:
    save_adapter = adapter

func set_config(p_config: Resource) -> void:
    config = p_config
    if config:
        funds = config.recruit_cost # Wait, let's verify if config.initial_funds exists
        if "initial_funds" in config:
            funds = config.initial_funds
        if "initial_reputation" in config:
            reputation = config.initial_reputation

func save_game(agent_manager = null, task_manager = null) -> bool:
    if save_adapter == null:
        push_error("Cannot save: No SaveAdapter provided.")
        return false
        
    var data = {
        "tycoon": {
            "funds": funds,
            "reputation": reputation,
            "current_phase": current_phase,
            "active_crises": active_crises
        },
        "agents": agent_manager.to_dict() if agent_manager else {},
        "tasks": task_manager.to_dict() if task_manager else {}
    }
    
    var result = save_adapter.save_data(data)
    if result is bool:
        return result
    return await result

func load_game(agent_manager = null, task_manager = null) -> bool:
    if save_adapter == null:
        push_error("Cannot load: No SaveAdapter provided.")
        return false
        
    var data = save_adapter.load_data()
    if data is Dictionary:
        if data.is_empty():
            return false
        _apply_save_data(data, agent_manager, task_manager)
        return true
    
    var awaited_data = await data
    if awaited_data.is_empty():
        return false
    _apply_save_data(awaited_data, agent_manager, task_manager)
    return true

func _apply_save_data(data: Dictionary, agent_manager = null, task_manager = null) -> void:
    if data.has("tycoon"):
        var tycoon_data = data["tycoon"]
        if tycoon_data.has("funds"): funds = int(tycoon_data["funds"])
        if tycoon_data.has("reputation"): reputation = int(tycoon_data["reputation"])
        if tycoon_data.has("current_phase"): current_phase = int(tycoon_data["current_phase"])
        if tycoon_data.has("active_crises"): active_crises = tycoon_data["active_crises"]
        
    if data.has("agents") and agent_manager != null:
        agent_manager.from_dict(data["agents"])
        
    if data.has("tasks") and task_manager != null:
        task_manager.from_dict(data["tasks"])

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
    var rep_penalty = config.rush_fail_rep_penalty if config else 10
    reputation = max(0, reputation - rep_penalty)
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
    
    var drain_amount = config.crisis_energy_drain if config else 5
    var spread_duration = config.crisis_spread_duration if config else 3
    var spread_chance = config.crisis_spread_chance if config else 0.2
    
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
                agent_manager.drain_agent_energy(i, drain_amount)
            
        # 2. Spread crisis if it has lasted > spread_duration
        if duration > spread_duration and randf() <= spread_chance:
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
    var divisor = config.stat_divisor if config else 5
    var resolution_power = 1 + int(qa_agent.debug_logic / divisor)
    
    # We reduce the duration or directly resolve it if it's worked on
    active_crises.erase(room_name)
    crisis_resolved.emit(room_name)



