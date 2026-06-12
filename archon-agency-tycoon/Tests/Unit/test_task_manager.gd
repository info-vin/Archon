extends MiniTest

func test_successful_task_assignment() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Fix Bug", 1, 3, 200) # DEV, 3 ticks, $200
    var task_id = task_manager.add_task(task)
    
    var success = task_manager.assign_task(task_id, agent_id)
    
    assert_true(success, "Task assignment should succeed")
    assert_eq(agent.state, preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING, "Agent state should be WORKING")
    assert_eq(task.assigned_agent_id, agent_id, "Task should hold the assigned agent ID")

func test_failed_assignment_role_mismatch() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 0) # SALES
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Fix Bug", 1, 3, 200) # DEV
    var task_id = task_manager.add_task(task)
    
    var success = task_manager.assign_task(task_id, agent_id)
    
    assert_false(success, "Task assignment should fail due to role mismatch")
    assert_eq(agent.state, preload("res://Scripts/Resources/AgentResource.gd").AgentState.IDLE, "Agent state should remain IDLE")

func test_process_tick_and_task_completion() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Quick Fix", 1, 2, 150) # Requires 2 ticks
    var task_id = task_manager.add_task(task)
    
    task_manager.assign_task(task_id, agent_id)
    
    # Tick 1
    task_manager.process_tick()
    assert_eq(task.current_progress, 1, "Progress should be 1 after 1 tick")
    assert_false(task.is_completed, "Task should not be completed yet")
    assert_eq(agent.energy, 90, "Energy should drop by 10")
    
    # Tick 2
    task_manager.process_tick()
    assert_eq(task.current_progress, 2, "Progress should be 2 after 2 ticks")
    assert_true(task.is_completed, "Task should be completed now")
    assert_eq(agent.state, preload("res://Scripts/Resources/AgentResource.gd").AgentState.IDLE, "Agent should be IDLE again")
    assert_eq(agent.energy, 80, "Energy should drop by another 10")
