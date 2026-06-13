extends Resource
class_name AgentResource

enum AgentRole { SALES, DEV, QA }
enum AgentState { IDLE, WORKING, RESTING, EXHAUSTED }

@export var agent_name: String = "New Agent"
@export var role: AgentRole = AgentRole.DEV
@export var state: AgentState = AgentState.IDLE
@export var energy: int = 100

func _init(p_name: String = "New Agent", p_role: AgentRole = AgentRole.DEV):
    agent_name = p_name
    role = p_role
    state = AgentState.IDLE
    energy = 100
