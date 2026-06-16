extends MiniTest

func test_tycoon_manager_config_injection() -> void:
	var tycoon = preload("res://Scripts/Logic/TycoonManager.gd").new()
	var config = preload("res://Scripts/Resources/TycoonConfig.gd").new()
	
	# Override default values in config
	config.initial_funds = 1234
	config.initial_reputation = 88
	config.rush_fail_rep_penalty = 5
	
	tycoon.set_config(config)
	
	assert_eq(tycoon.funds, 1234, "Tycoon funds should initialize from config initial_funds")
	assert_eq(tycoon.reputation, 88, "Tycoon reputation should initialize from config initial_reputation")
	
	# Test rush fail rep penalty
	tycoon._on_rush_failed(0, 0)
	assert_eq(tycoon.reputation, 83, "Reputation penalty on rush fail should read config.rush_fail_rep_penalty")

func test_task_manager_config_injection() -> void:
	var task_mgr = preload("res://Scripts/Logic/TaskManager.gd").new()
	var agent_mgr = preload("res://Scripts/Logic/AgentManager.gd").new()
	task_mgr.set_agent_manager(agent_mgr)
	
	var config = preload("res://Scripts/Resources/TycoonConfig.gd").new()
	config.min_assign_energy = 45
	config.rush_fail_energy_penalty = 22
	
	task_mgr.set_config(config)
	agent_mgr.set_config(config)
	
	var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 1) # DEV
	var task = preload("res://Scripts/Resources/TaskResource.gd").new("Client Project", 1, 3, 300) # DEV
	
	agent_mgr.add_agent(agent)
	var task_id = task_mgr.add_task(task)
	
	# Set agent energy below config min but above default 10
	agent.energy = 25
	
	var success = task_mgr.assign_task(task_id, 0)
	assert_false(success, "Task assignment should fail because agent energy 25 < min_assign_energy 45")
	
	# Give energy and assign
	agent.energy = 100
	success = task_mgr.assign_task(task_id, 0)
	assert_true(success, "Should succeed now")
	
	# Test rush failure penalty read from config
	# Force rush failure by mocking random to guaranteed failure (e.g. success_prob is at most 0.8, we can just call rush_task with low energy to increase failure chance)
	# Actually, since luck is 0, success_prob is config.rush_base_chance = 0.5.
	# We can just mock randf or run multiple times if needed, but we can also check the result of rush_task directly if it returns false.
	# Let's override rush_base_chance to 0.0 to force failure
	config.rush_base_chance = 0.0
	var rushed = task_mgr.rush_task(task_id)
	assert_false(rushed, "Rush should fail since base chance is 0.0")
	assert_eq(agent.energy, 78, "Agent energy should drop by config.rush_fail_energy_penalty (100 - 22 = 78)")

func test_agent_manager_config_injection() -> void:
	var agent_mgr = preload("res://Scripts/Logic/AgentManager.gd").new()
	var config = preload("res://Scripts/Resources/TycoonConfig.gd").new()
	
	config.rest_energy_recovery = 40
	agent_mgr.set_config(config)
	
	var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1)
	agent.energy = 50
	agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.RESTING
	agent_mgr.add_agent(agent)
	
	agent_mgr.process_tick()
	assert_eq(agent.energy, 90, "Energy should recover by config.rest_energy_recovery (50 + 40 = 90)")
