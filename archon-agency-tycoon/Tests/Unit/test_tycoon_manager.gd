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

func test_agent_attributes_boost_work_speed() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    # Alice (DEV) has code_speed 10 -> work increment is 1 + 10/5 = 3 per tick
    var alice = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1, 10)
    var alice_id = agent_manager.add_agent(alice)
    
    # Bob (DEV) has code_speed 1 -> work increment is 1 + 1/5 = 1 per tick
    var bob = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 1, 1)
    var bob_id = agent_manager.add_agent(bob)
    
    var task1 = preload("res://Scripts/Resources/TaskResource.gd").new("Task 1", 1, 3, 100)
    var task2 = preload("res://Scripts/Resources/TaskResource.gd").new("Task 2", 1, 3, 100)
    
    var t1_id = task_manager.add_task(task1)
    var t2_id = task_manager.add_task(task2)
    
    task_manager.assign_task(t1_id, alice_id)
    task_manager.assign_task(t2_id, bob_id)
    
    # Process 1 Tick
    task_manager.process_tick()
    
    assert_true(task1.is_completed, "Alice should complete the 3-tick task in 1 tick due to code_speed 10")
    assert_eq(task2.current_progress, 1, "Bob should only have progress 1 after 1 tick")

func test_rush_success_completes_task_instantly() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    # Set high luck to guarantee success (success_prob > 1.0)
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1, 5, 5, 5, 20)
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Long Task", 1, 10, 500)
    var task_id = task_manager.add_task(task)
    task_manager.assign_task(task_id, agent_id)
    
    var success = task_manager.rush_task(task_id)
    assert_true(success, "Rush should succeed with high luck")
    assert_true(task.is_completed, "Task should be marked as completed instantly")
    assert_eq(agent.state, 0, "Agent should return to IDLE")

func test_rush_failure_triggers_crisis_and_drains_energy() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    var tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    
    task_manager.set_agent_manager(agent_manager)
    tycoon_manager.setup_connections(task_manager)
    
    # Set negative luck to guarantee failure (success_prob < 0)
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1, 5, 5, 5, -20)
    var agent_id = agent_manager.add_agent(agent)
    
    var task = preload("res://Scripts/Resources/TaskResource.gd").new("Long Task", 1, 10, 500)
    var task_id = task_manager.add_task(task)
    task_manager.assign_task(task_id, agent_id)
    
    var success = task_manager.rush_task(task_id)
    assert_false(success, "Rush should fail with extremely low/negative luck")
    assert_eq(agent.energy, 70, "Agent energy should drop by 30 on failure (100 - 30)")
    assert_eq(task.assigned_agent_id, -1, "Task should be unassigned and returned to backlog")
    assert_true(tycoon_manager.active_crises.has("DevRoom"), "DevRoom should have a spawned crisis")
    assert_eq(tycoon_manager.reputation, 90, "Reputation should drop by 10 (100 - 10)")

func test_crisis_drains_energy_and_spreads() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    
    var charlie = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 2) # QA
    agent_manager.add_agent(charlie) # Charlie gets agent_id 2 (mapped to QARoom)
    
    tycoon_manager.spawn_crisis("QARoom")
    
    # Tick 1
    tycoon_manager.process_crisis_tick(agent_manager)
    assert_eq(charlie.energy, 95, "Charlie energy should drop by 5 due to crisis in QARoom")
    assert_eq(tycoon_manager.active_crises["QARoom"], 1, "Crisis duration should be 1 tick")

