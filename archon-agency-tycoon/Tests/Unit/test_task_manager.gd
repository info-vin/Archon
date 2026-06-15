extends MiniTest

const AgentResource = preload("res://Scripts/Resources/AgentResource.gd")
const TaskResource = preload("res://Scripts/Resources/TaskResource.gd")

func test_successful_task_assignment() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = AgentResource.new("Alice", AgentResource.AgentRole.DEV)
    var agent_id = agent_manager.add_agent(agent)
    
    var task = TaskResource.new("Fix Bug", AgentResource.AgentRole.DEV, 3, 200)
    var task_id = task_manager.add_task(task)
    
    var success = task_manager.assign_task(task_id, agent_id)
    
    assert_true(success, "Task assignment should succeed")
    assert_eq(agent.state, AgentResource.AgentState.WORKING, "Agent state should be WORKING")
    assert_eq(task.assigned_agent_id, agent_id, "Task should hold the assigned agent ID")

func test_failed_assignment_role_mismatch() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = AgentResource.new("Bob", AgentResource.AgentRole.SALES)
    var agent_id = agent_manager.add_agent(agent)
    
    var task = TaskResource.new("Fix Bug", AgentResource.AgentRole.DEV, 3, 200)
    var task_id = task_manager.add_task(task)
    
    var success = task_manager.assign_task(task_id, agent_id)
    
    assert_false(success, "Task assignment should fail due to role mismatch")
    assert_eq(agent.state, AgentResource.AgentState.IDLE, "Agent state should remain IDLE")

func test_process_tick_and_task_completion() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = AgentResource.new("Alice", AgentResource.AgentRole.DEV)
    var agent_id = agent_manager.add_agent(agent)
    
    var task = TaskResource.new("Quick Fix", AgentResource.AgentRole.DEV, 2, 150)
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
    assert_eq(agent.state, AgentResource.AgentState.IDLE, "Agent should be IDLE again")
    assert_eq(agent.energy, 80, "Energy should drop by another 10")

func test_failed_assignment_exhausted_agent() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = AgentResource.new("Dave", AgentResource.AgentRole.DEV)
    agent.energy = 0
    agent.state = AgentResource.AgentState.EXHAUSTED
    var agent_id = agent_manager.add_agent(agent)
    
    var task = TaskResource.new("Crunch Time", AgentResource.AgentRole.DEV, 3, 200)
    var task_id = task_manager.add_task(task)
    
    var success = task_manager.assign_task(task_id, agent_id)
    
    assert_false(success, "Task assignment should fail for EXHAUSTED agents")
    assert_eq(agent.state, AgentResource.AgentState.EXHAUSTED, "Agent state should remain EXHAUSTED")

func test_task_interrupted_by_exhaustion() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var agent = AgentResource.new("ExhaustedWorker", AgentResource.AgentRole.DEV)
    agent.energy = 10 # Start with 10 to pass assignment check, will be 0 after 1 tick
    var agent_id = agent_manager.add_agent(agent)
    
    var task = TaskResource.new("Big Feature", AgentResource.AgentRole.DEV, 5, 500)
    var task_id = task_manager.add_task(task)
    
    task_manager.assign_task(task_id, agent_id)
    
    # Tick 1: Agent works, but AgentManager process_tick will set them to EXHAUSTED
    task_manager.process_tick() # This deducts 10 energy, energy becomes -5
    agent_manager.process_tick() # This clamps energy to 0, state EXHAUSTED
    
    assert_eq(task.current_progress, 1, "Progress should be 1")
    assert_eq(agent.state, AgentResource.AgentState.EXHAUSTED, "Agent should be exhausted")
    
    # Tick 2: Agent is exhausted, should not work on task
    task_manager.process_tick()
    
    assert_eq(task.current_progress, 1, "Progress should NOT increase because agent is exhausted")
    assert_eq(agent.energy, 0, "Energy should remain 0")

func test_sales_loop_no_output_when_idle() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var bob = AgentResource.new("Bob", AgentResource.AgentRole.SALES)
    bob.state = AgentResource.AgentState.IDLE
    agent_manager.add_agent(bob)
    
    var initial_task_count = task_manager.tasks.size()
    
    # Process 5 ticks
    for i in range(5):
        task_manager.process_tick()
        agent_manager.process_tick()
        
    assert_eq(task_manager.tasks.size(), initial_task_count, "No tasks should be generated when SALES is IDLE")

func test_sales_loop_generates_task() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var bob = AgentResource.new("Bob", AgentResource.AgentRole.SALES)
    # Simulate assigning Bob to a "Client Outreach" internal task
    bob.state = AgentResource.AgentState.WORKING
    agent_manager.add_agent(bob)
    
    var initial_task_count = task_manager.tasks.size()
    
    # Process ticks. Let's assume a design where a SALES agent generates 1 task every 3 ticks
    for i in range(3):
        task_manager.process_tick()
        agent_manager.process_tick()
        
    assert_eq(task_manager.tasks.size(), initial_task_count + 1, "One new task should be generated by SALES after working")
    assert_eq(bob.energy, 70, "Bob should have consumed 30 energy")
    
func test_sales_loop_interrupted_by_exhaustion() -> void:
    var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
    task_manager.set_agent_manager(agent_manager)
    
    var bob = AgentResource.new("Bob", AgentResource.AgentRole.SALES)
    bob.energy = 20 # Only enough energy for 2 ticks
    bob.state = AgentResource.AgentState.WORKING
    agent_manager.add_agent(bob)
    
    var initial_task_count = task_manager.tasks.size()
    
    # Process 4 ticks. Bob should faint at tick 2, failing to generate a task at tick 3.
    for i in range(4):
        task_manager.process_tick()
        agent_manager.process_tick()
        
    assert_eq(bob.state, AgentResource.AgentState.EXHAUSTED, "Bob should be exhausted")
    assert_eq(task_manager.tasks.size(), initial_task_count, "No task should be generated because Bob fainted before finishing the pitch")
