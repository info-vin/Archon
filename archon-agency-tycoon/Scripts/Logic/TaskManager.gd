extends Node
class_name TaskManager

var tasks: Array[TaskResource] = []
var agent_manager: AgentManager = null
var sales_progress: Dictionary = {}

signal task_completed(task_id: int, reward: int)
signal rush_failed(task_id: int, agent_id: int)

func set_agent_manager(manager: AgentManager) -> void:
    agent_manager = manager

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
        
    if agent.energy < 10:
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
        
    var agent = agent_manager.get_agent(task.assigned_agent_id)
    if agent == null or agent.state != 1:
        return false
        
    # Probability formula: 50% base + up to 30% from Luck adjusted by Energy
    var success_prob = 0.5 + (agent.luck * 0.03) * (float(agent.energy) / 100.0)
    
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
        agent_manager.drain_agent_energy(agent_id, 30)
        task.assigned_agent_id = -1
        task.current_progress = 0
        rush_failed.emit(task_id, agent_id)
        return false

func process_tick() -> void:
    if agent_manager == null:
        return
        
    # Process Sales Agents
    for i in range(agent_manager.agents.size()):
        var agent = agent_manager.agents[i]
        if agent.role == AgentResource.AgentRole.SALES and agent.state == AgentResource.AgentState.WORKING:
            if not sales_progress.has(i):
                sales_progress[i] = 0
            
            # Charisma scales task generation speed
            var scale = 1 + int(agent.charisma / 5)
            sales_progress[i] += scale
            agent_manager.drain_agent_energy(i, 10)
            
            if sales_progress[i] >= 3:
                sales_progress[i] = 0
                var new_task = preload("res://Scripts/Resources/TaskResource.gd").new("Client Project", AgentResource.AgentRole.DEV, 3, 300)
                add_task(new_task)
                # Sales agent stays WORKING to generate more tasks until exhausted or manually stopped
        
    for i in range(tasks.size()):
        var task = tasks[i]
        if not task.is_completed and task.assigned_agent_id != -1:
            var agent = agent_manager.get_agent(task.assigned_agent_id)
            if agent != null and agent.state == 1: # 1 is WORKING
                # code_speed scales dev work speed
                var work_increment = 1 + int(agent.code_speed / 5)
                task.current_progress += work_increment
                agent_manager.drain_agent_energy(task.assigned_agent_id, 10)
                
                if task.current_progress >= task.required_ticks:
                    task.is_completed = true
                    agent.state = 0 # 0 is IDLE
                    task_completed.emit(i, task.reward_funds)
