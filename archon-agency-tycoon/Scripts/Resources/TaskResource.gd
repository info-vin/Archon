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

func to_dict() -> Dictionary:
	return {
		"task_name": task_name,
		"required_role": required_role,
		"required_ticks": required_ticks,
		"reward_funds": reward_funds,
		"current_progress": current_progress,
		"is_completed": is_completed,
		"assigned_agent_id": assigned_agent_id
	}

static func from_dict(data: Dictionary) -> TaskResource:
	var t = TaskResource.new()
	if data.has("task_name"): t.task_name = data["task_name"]
	if data.has("required_role"): t.required_role = data["required_role"]
	if data.has("required_ticks"): t.required_ticks = data["required_ticks"]
	if data.has("reward_funds"): t.reward_funds = data["reward_funds"]
	if data.has("current_progress"): t.current_progress = data["current_progress"]
	if data.has("is_completed"): t.is_completed = data["is_completed"]
	if data.has("assigned_agent_id"): t.assigned_agent_id = data["assigned_agent_id"]
	return t
