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
