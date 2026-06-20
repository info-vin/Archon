extends Node
class_name TaskManager

var tasks: Array[TaskResource] = []
var agent_manager: AgentManager = null
var sales_progress: Dictionary = {}
var config: Resource

signal task_completed(task_id: int, reward: int)
signal rush_failed(task_id: int, agent_id: int)

func _init() -> void:
    var res = load("res://GameConfig.tres")
    if res:
        set_config(res)

func set_agent_manager(manager: AgentManager) -> void:
    agent_manager = manager

func set_config(p_config: Resource) -> void:
    config = p_config

func add_task(task: TaskResource) -> int:
    tasks.append(task)
    return tasks.size() - 1

func assign_task(task_id: int, agent_id: int) -> bool:
    if task_id < 0 or task_id >= tasks.size():
        push_error("Invalid task_id: %d" % task_id)
        return false
    if agent_manager == null:
        push_error("AgentManager not set in TaskManager")
        return false
        
    var agent = agent_manager.get_agent(agent_id)
    if agent == null:
        push_error("Invalid agent_id: %d" % agent_id)
        return false
        
    var task = tasks[task_id]
    
    if task.is_completed or task.assigned_agent_id != -1:
        # push_warning("Task already assigned or completed.")
        return false
        
    if agent.state != 0: # 0 is IDLE
        # push_warning("Agent is not IDLE.")
        return false
        
    if agent.role != task.required_role:
        # push_warning("Role mismatch.")
        return false
        
    var min_energy = config.min_assign_energy if config else 10
    if agent.energy < min_energy:
        # push_warning("Agent too tired.")
        return false
        
    # Apply assignment
    task.assigned_agent_id = agent_id
    agent.state = 1 # 1 is WORKING
    return true

func rush_task(task_id: int) -> bool:
    if task_id < 0 or task_id >= tasks.size():
        return false
    var task = tasks[task_id]
    if task.is_completed or task.assigned_agent_id == -1:
        return false
        
    if task.is_hell_client:
        return false
        
    var agent = agent_manager.get_agent(task.assigned_agent_id)
    if agent == null or agent.state != 1:
        return false
        
    var base_chance = config.rush_base_chance if config else 0.5
    var luck_mod = config.rush_luck_modifier if config else 0.03
    var energy_penalty = config.rush_fail_energy_penalty if config else 30
    
    # Probability formula: base + up to luck*luck_mod adjusted by Energy
    var success_prob = base_chance + (agent.luck * luck_mod) * (float(agent.energy) / 100.0)
    
    if randf() <= success_prob:
        # Success: Instant completion
        task.current_progress = task.required_ticks
        task.is_completed = true
        agent.state = 0 # IDLE
        task_completed.emit(task_id, task.reward_funds)
        return true
    else:
        # Failure: Energy drain, task reset, spawn crisis
        var agent_id = task.assigned_agent_id
        agent_manager.drain_agent_energy(agent_id, energy_penalty)
        task.assigned_agent_id = -1
        task.current_progress = 0
        rush_failed.emit(task_id, agent_id)
        return false

func process_tick() -> void:
    if agent_manager == null:
        return
        
    var work_drain = config.work_energy_drain if config else 10
    var sales_ticks_needed = config.sales_task_ticks_needed if config else 3
    var gen_ticks = config.generated_task_ticks if config else 3
    var gen_reward = config.generated_task_reward if config else 300
    
    # Process Sales Agents
    for i in range(agent_manager.agents.size()):
        var agent = agent_manager.agents[i]
        if agent.role == AgentResource.AgentRole.SALES and agent.state == AgentResource.AgentState.WORKING:
            if not sales_progress.has(i):
                sales_progress[i] = 0
            
            # Charisma scales task generation speed
            var divisor = config.stat_divisor if config else 5
            var scale = 1 + int(agent.charisma / divisor)
            sales_progress[i] += scale
            agent_manager.drain_agent_energy(i, work_drain)
            
            if sales_progress[i] >= sales_ticks_needed:
                sales_progress[i] = 0
                var new_task = preload("res://Scripts/Resources/TaskResource.gd").new("Client Project", AgentResource.AgentRole.DEV, gen_ticks, gen_reward)
                add_task(new_task)
                # Sales agent stays WORKING to generate more tasks until exhausted or manually stopped
        
    for i in range(tasks.size()):
        var task = tasks[i]
        if not task.is_completed and task.assigned_agent_id != -1:
            var agent = agent_manager.get_agent(task.assigned_agent_id)
            if agent != null and agent.state == 1: # 1 is WORKING
                # code_speed scales dev work speed
                var divisor = config.stat_divisor if config else 5
                var work_increment = 1 + int(agent.code_speed / divisor)
                task.current_progress += work_increment
                var actual_drain = work_drain
                if task.is_hell_client:
                    actual_drain *= 2
                    agent.happiness = clamp(agent.happiness - 10.0, 0.0, 100.0)
                agent_manager.drain_agent_energy(task.assigned_agent_id, actual_drain)
                
                if task.current_progress >= task.required_ticks:
                    task.is_completed = true
                    agent.state = 0 # 0 is IDLE
                    task_completed.emit(i, task.reward_funds)

func to_dict() -> Dictionary:
    var arr = []
    for t in tasks:
        arr.append(t.to_dict())
    return {
        "tasks": arr,
        "sales_progress": sales_progress
    }

func from_dict(data: Dictionary) -> void:
    tasks.clear()
    sales_progress.clear()
    if data.has("tasks") and data["tasks"] is Array:
        for t_data in data["tasks"]:
            var task = preload("res://Scripts/Resources/TaskResource.gd").from_dict(t_data)
            tasks.append(task)
    if data.has("sales_progress") and data["sales_progress"] is Dictionary:
        for key in data["sales_progress"].keys():
            sales_progress[int(key)] = data["sales_progress"][key]

