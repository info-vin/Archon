extends MiniTest

func test_add_and_retrieve_agent() -> void:
    var manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # 1 = DEV
    
    var id = manager.add_agent(agent)
    assert_eq(id, 0, "First agent should have ID 0")
    
    var retrieved = manager.get_agent(0)
    assert_not_null(retrieved, "Agent should be retrievable")
    assert_eq(retrieved.agent_name, "Alice", "Name should match")

func test_find_available_agent() -> void:
    var manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var agent1 = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
    var agent2 = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 0)   # SALES
    var agent3 = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 1) # DEV
    
    manager.add_agent(agent1)
    manager.add_agent(agent2)
    manager.add_agent(agent3)
    
    # Make Charlie busy
    agent3.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING
    
    # We want a DEV
    var available_devs = manager.get_available_agents_by_role(1)
    
    assert_eq(available_devs.size(), 1, "Should only find 1 available DEV")
    assert_eq(available_devs[0], 0, "The available DEV should be Alice (ID 0)")

func test_agent_energy_recovery() -> void:
    var manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
    
    # 模擬員工工作很累，體力剩下 70
    agent.energy = 70
    
    # 將員工狀態設為休息
    agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.RESTING
    manager.add_agent(agent)
    
    # 呼叫 manager 的 process_tick()，預期員工體力應該恢復
    manager.process_tick()
    assert_eq(agent.energy, 90, "Energy should recover by 20 during RESTING state")
    
    # 再過一回合，確保體力不會超過上限 100
    manager.process_tick()
    assert_eq(agent.energy, 100, "Energy should not exceed 100")

func test_agent_exhaustion() -> void:
    var manager = preload("res://Scripts/Logic/AgentManager.gd").new()
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 1)
    
    agent.energy = 5
    agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING
    manager.add_agent(agent)
    
    # Simulate a process tick where the task manager would typically drain 10 energy,
    # but the agent manager's process_tick will clamp it to 0 and set state to EXHAUSTED if it drops <= 0
    # Let's just deduct energy and then call process_tick to see if AgentManager handles the limit
    agent.energy -= 10
    manager.process_tick()
    
    assert_eq(agent.energy, 0, "Energy should not drop below 0")
    assert_eq(agent.state, preload("res://Scripts/Resources/AgentResource.gd").AgentState.EXHAUSTED, "Agent should be EXHAUSTED")
