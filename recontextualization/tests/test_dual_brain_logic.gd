extends RefCounted

func run_tests(tree: SceneTree) -> bool:
	print("[test_dual_brain_logic] Running...")
	var passed = true
	
	var save_mgr = tree.root.get_node_or_null("SaveManager")
	var game_state = tree.root.get_node_or_null("GameState")
	
	if game_state:
		game_state.is_tutorial_active = false
		
	if save_mgr:
		save_mgr.teammates = [{
			"id": "charlie",
			"level": 3,
			"equipped_model": "gemini-1.5-pro",
			"allow_react": true
		}]
	
	var backend = preload("res://src/network/BackendClient.gd").new()
	tree.root.add_child(backend)
	
	backend.search("test dual brain logic", 0.5, 5)
	
	if backend._current_payload.get("allow_react", false) != true:
		print("[test_dual_brain_logic] FAILED: allow_react not set correctly in payload. Got: ", backend._current_payload.get("allow_react"))
		passed = false
		
	if backend._current_payload.get("equipped_model", "") != "gemini-1.5-pro":
		print("[test_dual_brain_logic] FAILED: equipped_model not set correctly in payload. Got: ", backend._current_payload.get("equipped_model"))
		passed = false
		
	backend.queue_free()
	
	if passed:
		print("[test_dual_brain_logic] PASSED")
	return passed
