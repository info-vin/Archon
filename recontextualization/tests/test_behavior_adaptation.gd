extends RefCounted

func run_tests(tree: SceneTree) -> bool:
	print("[test_behavior_adaptation] Running...")
	var passed = true
	
	var game_state = tree.root.get_node_or_null("GameState")
	var save_mgr = tree.root.get_node_or_null("SaveManager")
	
	if save_mgr:
		save_mgr.has_completed_tutorial = true # Prevent tutorial lock
		
	if not game_state:
		game_state = preload("res://src/autoloads/GameState.gd").new()
		tree.root.add_child(game_state)
		
	game_state.start_game()
	
	# Initial ratio should be 0 for sector 1
	if game_state.data_poisoning_ratio != 0.0:
		print("[test_behavior_adaptation] FAILED: Initial poisoning ratio not 0.0, got: ", game_state.data_poisoning_ratio)
		passed = false
		
	# Reduce SLA to simulate time passing and adaptation
	game_state.sla_timer = game_state.max_sla / 2.0
	game_state._process(0.1) # Trigger process to update ratio
	
	if game_state.data_poisoning_ratio <= 0.0:
		print("[test_behavior_adaptation] FAILED: Poisoning ratio did not adapt to SLA drop.")
		passed = false
		
	if passed:
		print("[test_behavior_adaptation] PASSED")
	return passed
