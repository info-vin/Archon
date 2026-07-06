extends RefCounted

func run_tests(tree: SceneTree) -> bool:
	print("[test_token_capping] Running...")
	var passed = true
	
	var save_mgr = tree.root.get_node_or_null("SaveManager")
	var game_state = tree.root.get_node_or_null("GameState")
	
	if game_state:
		game_state.is_tutorial_active = false # Prevent early return
		
	if save_mgr:
		save_mgr.teammates = [{
			"id": "alice",
			"level": 1,
			"equipped_model": "gemini-1.5-flash",
			"allow_react": false
		}]
	
	var backend = preload("res://src/network/BackendClient.gd").new()
	tree.root.add_child(backend)
	
	backend.search("test token capping", 0.5, 5)
	
	if backend._current_payload.get("equipped_model", "") != "gemini-1.5-flash":
		print("[test_token_capping] FAILED: equipped_model not set correctly in payload. Got: ", backend._current_payload.get("equipped_model"))
		passed = false
		
	backend.queue_free()
	
	if passed:
		print("[test_token_capping] PASSED")
	return passed
