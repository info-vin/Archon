extends Resource
class_name TaskResource

@export var task_name: String = "New Task"
@export var required_role: int = 1 # Matches AgentResource.AgentRole.DEV (enum is 0-indexed: SALES=0, DEV=1, QA=2)
@export var required_ticks: int = 5
@export var reward_funds: int = 100
@export var current_progress: int = 0
@export var is_completed: bool = false
@export var assigned_agent_id: int = -1

func _init(p_name: String = "New Task", p_role: int = 1, p_ticks: int = 5, p_reward: int = 100):
    task_name = p_name
    required_role = p_role
    required_ticks = p_ticks
    reward_funds = p_reward
    current_progress = 0
    is_completed = false
    assigned_agent_id = -1
