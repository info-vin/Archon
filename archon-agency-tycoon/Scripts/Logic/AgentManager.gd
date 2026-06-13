extends Node
class_name AgentManager

var agents: Array[AgentResource] = []

func add_agent(agent: AgentResource) -> int:
    agents.append(agent)
    return agents.size() - 1

func get_agent(index: int) -> AgentResource:
    if index >= 0 and index < agents.size():
        return agents[index]
    return null

func get_available_agents_by_role(role: int) -> Array[int]:
    var available: Array[int] = []
    for i in range(agents.size()):
        var agent = agents[i]
        # role check, state must be IDLE (0), energy >= 10
        if agent.role == role and agent.state == 0 and agent.energy >= 10:
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
    for agent in agents:
        if agent.state == AgentResource.AgentState.RESTING:
            agent.energy += 20
            if agent.energy > 100:
                agent.energy = 100
        elif agent.energy <= 0:
            agent.energy = 0
            agent.state = AgentResource.AgentState.EXHAUSTED
