extends MiniTest

func test_task_completion_adds_funds() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    var tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    
    task_manager.set_agent_manager(agent_manager)
    
    # Needs to connect signal manually or via a setup function in TycoonManager
    # Let's assume TycoonManager has a setup_connections(task_manager) method
    if tycoon_manager.has_method("setup_connections"):
        tycoon_manager.setup_connections(task_manager)
    else:
        # Fallback manual connection if not implemented yet
        task_manager.task_completed.connect(tycoon_manager._on_task_completed)
        
    var initial_funds = tycoon_manager.funds # should be 500
    
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Quick Fix", 1, 1, 150) # 1 tick, 150 funds reward
    var task_id = task_manager.add_task(task)
    
    task_manager.assign_task(task_id, agent_id)
    
    # Tick 1: completes the task
    task_manager.process_tick()
    
    assert_eq(task.is_completed, true, "Task should be completed")
    assert_eq(tycoon_manager.funds, initial_funds + 150, "Funds should increase by 150")
