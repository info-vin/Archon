extends Node

var agent_manager
var task_manager
var tycoon_manager
var lifecycle

var tick_count: int = 0
var config: Resource
var game_tick_timer: Timer

func _ready() -> void:
	config = load("res://GameConfig.tres")
	
	agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
	task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
	tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
	lifecycle = preload("res://Scripts/Logic/GameLifecycle.gd").new()
	
	var local_save_adapter = preload("res://Scripts/Logic/SaveSystems/LocalSaveAdapter.gd").new("user://savegame.save")
	tycoon_manager.set_save_adapter(local_save_adapter)
	
	task_manager.task_generated.connect(_on_task_generated)
	
	game_tick_timer = Timer.new()
	game_tick_timer.wait_time = 1.0
	game_tick_timer.autostart = true
	add_child(game_tick_timer)
	game_tick_timer.timeout.connect(_on_tick_timer_timeout)
	
	if not FileAccess.file_exists("user://savegame.save"):
		_setup_initial_game()
	else:
		_load_game()

func _load_game() -> void:
	var loaded = await tycoon_manager.load_game(agent_manager, task_manager)
	if loaded:
		lifecycle.setup_loaded_game(agent_manager, task_manager)
		for agent_id in range(agent_manager.agents.size()):
			var agent = agent_manager.get_agent(agent_id)
			var target_room = "dev"
			if agent.role == 0: target_room = "sales"
			elif agent.role == 2: target_room = "qa"
			get_node("/root/EventBus").agent_spawned.emit(agent_id, target_room)
	else:
		_setup_initial_game()

func _setup_initial_game() -> void:
	var AgentResource = preload("res://Scripts/Resources/AgentResource.gd")
	var alice = AgentResource.new("Alice", AgentResource.AgentRole.DEV, 10, 5, 5, 5, "", "", "", 0, 1, Color("#39ff14"), 1, 1)
	var bob = AgentResource.new("Bob", AgentResource.AgentRole.SALES, 5, 10, 5, 5, "", "", "", 1, 2, Color("#fde910"), 2, 2)
	var charlie = AgentResource.new("Charlie", AgentResource.AgentRole.QA, 5, 5, 10, 5, "", "", "", 1, 2, Color("#ff003c"), 2, 3)
	
	for agent in [alice, bob, charlie]:
		var id = agent_manager.add_agent(agent)
		var target_room = "dev"
		if agent.role == AgentResource.AgentRole.SALES: target_room = "sales"
		elif agent.role == AgentResource.AgentRole.QA: target_room = "qa"
		get_node("/root/EventBus").agent_spawned.emit(id, target_room)
		
	var TaskResource = preload("res://Scripts/Resources/TaskResource.gd")
	var task1 = TaskResource.new("Fix Login Bug", AgentResource.AgentRole.DEV, 3, 300)
	var task2 = TaskResource.new("Update DB Schema", AgentResource.AgentRole.DEV, 2, 200)
	var task3 = TaskResource.new("Start Outreach", AgentResource.AgentRole.SALES, 999, 0)
	task_manager.add_task(task1)
	task_manager.add_task(task2)
	task_manager.add_task(task3)

func recruit_agent(agent_data: Resource) -> void:
	var recruit_cost = config.recruit_cost if config else 500
	if tycoon_manager.funds >= recruit_cost:
		tycoon_manager.funds -= recruit_cost
		var id = agent_manager.add_agent(agent_data)
		var target_room = "dev"
		if agent_data.role == 0: target_room = "sales"
		elif agent_data.role == 2: target_room = "qa"
		get_node("/root/EventBus").agent_spawned.emit(id, target_room)
		get_node("/root/EventBus").tick_updated.emit(tick_count, tycoon_manager.funds, tycoon_manager.reputation)

func expand_room() -> bool:
	var expand_cost = config.expand_cost if config else 500
	if tycoon_manager.funds >= expand_cost:
		tycoon_manager.funds -= expand_cost
		get_node("/root/EventBus").tick_updated.emit(tick_count, tycoon_manager.funds, tycoon_manager.reputation)
		return true
	return false

func save_game() -> void:
	tycoon_manager.save_game(agent_manager, task_manager)

func _on_task_generated(task_id: int) -> void:
	var task = task_manager.tasks[task_id]
	get_node("/root/EventBus").task_generated.emit(task_id, task.task_name, task.required_ticks, task.reward_funds)

func _on_tick_timer_timeout() -> void:
	tick_count += 1
	tycoon_manager.process_tick(agent_manager, task_manager)
	get_node("/root/EventBus").tick_updated.emit(tick_count, tycoon_manager.funds, tycoon_manager.reputation)
