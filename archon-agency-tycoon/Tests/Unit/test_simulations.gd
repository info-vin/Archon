extends SceneTree

# 🏢 Headless Play Simulator: Run 3 complete cycles of gameplay loops
# to verify stability, logic validation, and save/load accuracy.

func _initialize() -> void:
	print("=========================================================")
	print("🏢 STARTING HEADLESS PLAY SIMULATION (3 RUNS) 🏢")
	print("=========================================================")
	
	for run in range(1, 4):
		print("\n--- SIMULATION RUN #", run, " ---")
		var success = await run_game_simulation(run)
		if not success:
			print("🔴 RUN #", run, " FAILED!")
			quit(1)
			return
		print("🟢 RUN #", run, " COMPLETED SUCCESSFULLY")
		
	print("\n=========================================================")
	print("🎉 ALL 3 SIMULATION RUNS COMPLETED SUCCESSFULLY! 🎉")
	print("=========================================================")
	quit(0)

func run_game_simulation(run_id: int) -> bool:
	var agent_manager = preload("res://Scripts/Logic/AgentManager.gd").new()
	var task_manager = preload("res://Scripts/Logic/TaskManager.gd").new()
	var tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
	
	task_manager.set_agent_manager(agent_manager)
	tycoon_manager.setup_connections(task_manager)
	
	# Add mock save adapter to avoid disk clutter while verifying save mechanics
	var mock_adapter = MockSaveAdapter.new()
	tycoon_manager.set_save_adapter(mock_adapter)
	
	# 1. Recruit Alice (DEV), Bob (SALES), Charlie (QA)
	var alice = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1, 8, 5, 5, 2)
	var bob = preload("res://Scripts/Resources/AgentResource.gd").new("Bob", 0, 5, 8, 5, 3)
	var charlie = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 2, 5, 5, 8, 4)
	
	var alice_id = agent_manager.add_agent(alice)
	var bob_id = agent_manager.add_agent(bob)
	var charlie_id = agent_manager.add_agent(charlie)
	
	print("  Recruited: Alice (DEV, ID: ", alice_id, "), Bob (SALES, ID: ", bob_id, "), Charlie (QA, ID: ", charlie_id, ")")
	
	# 2. Simulate Sales Generating Task
	# Make Bob SALES agent work
	bob.state = AgentResource.AgentState.WORKING
	print("  Bob (SALES) is now working to generate leads...")
	
	# Tick Bob until task is generated
	var ticks_passed = 0
	while task_manager.tasks.is_empty() and ticks_passed < 5:
		task_manager.process_tick()
		tycoon_manager.process_crisis_tick(agent_manager)
		ticks_passed += 1
		print("    Tick ", ticks_passed, " | Bob Energy: ", bob.energy, " | Tasks Available: ", task_manager.tasks.size())
		
	if task_manager.tasks.is_empty():
		push_error("Sales Agent failed to generate task!")
		return false
		
	var generated_task_id = task_manager.tasks.size() - 1
	var generated_task = task_manager.tasks[generated_task_id]
	print("  🟢 Task Generated successfully! Reward: $", generated_task.reward_funds)
	
	# 3. Assign Task to Alice (DEV) and process ticks to complete it
	bob.state = AgentResource.AgentState.IDLE # Stop Bob
	var assign_success = task_manager.assign_task(generated_task_id, alice_id)
	if not assign_success:
		push_error("Failed to assign task to Alice!")
		return false
		
	print("  Assigned task to Alice. Alice state: WORKING")
	ticks_passed = 0
	var initial_funds = tycoon_manager.funds
	
	while not generated_task.is_completed and ticks_passed < 5:
		task_manager.process_tick()
		tycoon_manager.process_crisis_tick(agent_manager)
		ticks_passed += 1
		print("    Tick ", ticks_passed, " | Alice Energy: ", alice.energy, " | Task Progress: ", generated_task.current_progress, "/", generated_task.required_ticks)
		
	if not generated_task.is_completed:
		push_error("Alice failed to complete task within expected ticks!")
		return false
		
	print("  🟢 Alice completed task! Funds increased from ", initial_funds, " to ", tycoon_manager.funds)
	
	# 4. Simulate a RUSH attempt with Alice (with guaranteed failure using low luck to force crisis)
	var rush_task = preload("res://Scripts/Resources/TaskResource.gd").new("Rush Project", 1, 10, 800)
	var rush_task_id = task_manager.add_task(rush_task)
	task_manager.assign_task(rush_task_id, alice_id)
	
	# Set Alice's luck low to trigger crisis for testing crisis resolution by Charlie
	alice.luck = -50
	print("  Triggering RUSH on 'Rush Project' with extremely low luck to force crisis...")
	var rush_result = task_manager.rush_task(rush_task_id)
	
	if rush_result:
		print("    Unexpectedly Rushed successfully.")
	else:
		print("    🟢 Rush failed as expected. Crisis spawned in DevRoom. Active crises: ", tycoon_manager.active_crises.keys())
		if not tycoon_manager.active_crises.has("DevRoom"):
			push_error("Failed to spawn crisis on rush failure!")
			return false
			
		# Resolve crisis using QA Agent Charlie
		print("  Assigning QA Agent Charlie to resolve DevRoom crisis...")
		tycoon_manager.resolve_crisis("DevRoom", charlie)
		print("    Active crises after QA resolution: ", tycoon_manager.active_crises.keys())
		if tycoon_manager.active_crises.has("DevRoom"):
			push_error("Crisis in DevRoom was not resolved by QA Agent!")
			return false
		print("    🟢 DevRoom crisis resolved successfully!")

	# 5. Save the Game State and Verify
	print("  Saving current game state...")
	var save_success = await tycoon_manager.save_game()
	if not save_success:
		push_error("Save game operation failed!")
		return false
		
	print("    Saved values: Funds = ", mock_adapter.saved_data["funds"], ", Rep = ", mock_adapter.saved_data["reputation"])
	
	# Load into a fresh tycoon manager and verify equality
	var fresh_tycoon = preload("res://Scripts/Logic/TycoonManager.gd").new()
	fresh_tycoon.set_save_adapter(mock_adapter)
	var load_success = await fresh_tycoon.load_game()
	if not load_success:
		push_error("Load game operation failed!")
		return false
		
	if fresh_tycoon.funds != tycoon_manager.funds or fresh_tycoon.reputation != tycoon_manager.reputation:
		push_error("Loaded state mismatch! Expected Funds: %d, Loaded: %d" % [tycoon_manager.funds, fresh_tycoon.funds])
		return false
		
	print("    🟢 State verified after saving & loading. Load parity matched!")
	return true

# --- Mock Save Adapter ---
class MockSaveAdapter extends SaveAdapter:
	var saved_data: Dictionary = {}
	
	func save_data(data: Dictionary) -> bool:
		saved_data = data.duplicate(true)
		return true
		
	func load_data() -> Dictionary:
		return saved_data.duplicate(true)
