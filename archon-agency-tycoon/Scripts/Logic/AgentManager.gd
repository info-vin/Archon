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

func process_tick() -> void:
    var recovery = config.rest_energy_recovery if config else 20
    for agent in agents:
        if agent.state == AgentResource.AgentState.RESTING:
            agent.energy += recovery
            if agent.energy > 100:
                agent.energy = 100
        elif agent.energy <= 0:
            agent.energy = 0
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

