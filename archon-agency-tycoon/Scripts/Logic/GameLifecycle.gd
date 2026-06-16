extends Node
class_name GameLifecycle

var main_node: Control

func initialize(p_main_node: Control) -> void:
	main_node = p_main_node

func setup_loaded_game(agent_manager, task_manager) -> void:
	if not main_node: return
	
	# Apply scripts to DevRoom and SalesRoom drop zones
	var drop_script = preload("res://Scripts/UI/DevRoomDropZone.gd")
	if drop_script:
		main_node.dev_room.set_script(drop_script)
		main_node.sales_room.set_script(drop_script)
		# Initialize setups
		main_node.dev_room.setup_room("DevRoom", Color("#39ff14"), main_node.tycoon_manager)
		main_node.sales_room.setup_room("SalesRoom", Color("#fde910"), main_node.tycoon_manager)
	
	for agent_id in range(agent_manager.agents.size()):
		var agent = agent_manager.get_agent(agent_id)
		var target_room = main_node.dev_room
		if agent.role == 0: target_room = main_node.sales_room
		elif agent.role == 2: target_room = main_node.qa_room
		main_node._spawn_agent_view(agent_id, target_room)
	
	var card_scene = preload("res://Scenes/UI/TaskCard.tscn")
	for task_id in range(task_manager.tasks.size()):
		var task = task_manager.tasks[task_id]
		if not task.is_completed and task.assigned_agent_id == -1:
			if card_scene and main_node.task_container:
				var card = card_scene.instantiate()
				main_node.task_container.add_child(card)
				card.setup(task_id, task.task_name, task.required_ticks, task.reward_funds)

func setup_initial_game(agent_manager) -> void:
	if not main_node: return
	
	# Recruit three core employees
	var alice = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # DEV
	var bob = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 0)	 # SALES
	var charlie = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 2) # QA
	
	agent_manager.add_agent(alice)
	agent_manager.add_agent(bob)
	agent_manager.add_agent(charlie)
	
	# Instantiate ModularAgent views
	main_node._spawn_agent_view(0, main_node.dev_room)
	main_node._spawn_agent_view(1, main_node.sales_room)
	main_node._spawn_agent_view(2, main_node.qa_room)
		
	# Apply scripts to DevRoom and SalesRoom drop zones
	var drop_script = preload("res://Scripts/UI/DevRoomDropZone.gd")
	if drop_script:
		main_node.dev_room.set_script(drop_script)
		main_node.sales_room.set_script(drop_script)
		main_node.dev_room.setup_room("DevRoom", Color("#39ff14"), main_node.tycoon_manager)
		main_node.sales_room.setup_room("SalesRoom", Color("#fde910"), main_node.tycoon_manager)

	# Generate initial tasks
	main_node._spawn_task_in_backlog("Fix Login Bug", 3, 300, 1) # DEV
	main_node._spawn_task_in_backlog("Update DB Schema", 2, 200, 1) # DEV
	main_node._spawn_task_in_backlog("Start Outreach", 999, 0, 0) # SALES
