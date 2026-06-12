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
