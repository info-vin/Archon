extends Node
class_name TaskManager

var tasks: Array[TaskResource] = []
var agent_manager: AgentManager = null

signal task_completed(task_id: int, reward: int)

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

func process_tick() -> void:
    if agent_manager == null:
        return
        
    for i in range(tasks.size()):
        var task = tasks[i]
        if not task.is_completed and task.assigned_agent_id != -1:
            var agent = agent_manager.get_agent(task.assigned_agent_id)
            if agent != null and agent.state == 1: # 1 is WORKING
                task.current_progress += 1
                agent_manager.drain_agent_energy(task.assigned_agent_id, 10)
                
                if task.current_progress >= task.required_ticks:
                    task.is_completed = true
                    agent.state = 0 # 0 is IDLE
                    task_completed.emit(i, task.reward_funds)
