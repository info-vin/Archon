extends Node
class_name AgentManager

var agents: Array[AgentResource] = []
var config: Resource

func _init() -> void:
    var res = load("res://GameConfig.tres")
    if res:
        set_config(res)

func set_config(p_config: Resource) -> void:
    config = p_config

func add_agent(agent: AgentResource) -> int:
    agents.append(agent)
    return agents.size() - 1

func get_agent(index: int) -> AgentResource:
    if index >= 0 and index < agents.size():
        return agents[index]
    return null

func get_available_agents_by_role(role: int) -> Array[int]:
    var available: Array[int] = []
    var min_energy = config.min_assign_energy if config else 10
    for i in range(agents.size()):
        var agent = agents[i]
        # role check, state must be IDLE (0), energy >= min_energy
        if agent.role == role and agent.state == 0 and agent.energy >= min_energy:
            available.append(i)
    return available

func drain_agent_energy(agent_id: int, amount: int) -> void:
    var agent = get_agent(agent_id)
    if agent != null:
        agent.energy -= amount
        if agent.energy <= 0:
            agent.energy = 0
            agent.state = AgentResource.AgentState.EXHAUSTED

func process_tick(funds: int = 500) -> void:
    var recovery = config.rest_energy_recovery if config else 20
    for agent in agents:
        var mood_decay: float = 0.0
        if agent.state == AgentResource.AgentState.WORKING:
            mood_decay = 2.0
        elif agent.state == AgentResource.AgentState.IDLE:
            mood_decay = 0.5
            
        if funds < 0:
            mood_decay += 5.0
            
        var mood_recovery: float = 0.0
        if agent.state == AgentResource.AgentState.RESTING:
            mood_recovery = 8.0
        elif agent.state == AgentResource.AgentState.EXHAUSTED:
            mood_decay += 1.0
            
        agent.happiness = clamp(agent.happiness - mood_decay + mood_recovery, 0.0, 100.0)
        
        if agent.happiness <= 20.0 and agent.state != AgentResource.AgentState.STRIKE:
            agent.state = AgentResource.AgentState.STRIKE
            var main_loop = Engine.get_main_loop()
            if main_loop and main_loop.root.has_node("AudioManager"):
                main_loop.root.get_node("AudioManager").play_sfx("sigh")
                
        if agent.state == AgentResource.AgentState.STRIKE and agent.happiness >= 50.0:
            agent.state = AgentResource.AgentState.IDLE
            
        if agent.state == AgentResource.AgentState.RESTING:
            agent.energy += recovery
            if agent.energy > 100:
                agent.energy = 100
        elif agent.state == AgentResource.AgentState.STRIKE:
            agent.energy = min(100, agent.energy + 5)
        else:
            if agent.energy <= 0:
                agent.energy = 0
                if agent.state != AgentResource.AgentState.STRIKE:
                    agent.state = AgentResource.AgentState.EXHAUSTED

func to_dict() -> Dictionary:
    var arr = []
    for a in agents:
        arr.append(a.to_dict())
    return {"agents": arr}

func from_dict(data: Dictionary) -> void:
    agents.clear()
    if data.has("agents") and data["agents"] is Array:
        for a_data in data["agents"]:
            var agent = AgentResource.from_dict(a_data)
            agents.append(agent)

