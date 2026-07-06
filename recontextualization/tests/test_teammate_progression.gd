extends RefCounted

func run_tests(tree: SceneTree) -> bool:
	print("[test_teammate_progression] Running...")
	var passed = true
	
	var save_mgr = tree.root.get_node_or_null("SaveManager")
	if not save_mgr:
		save_mgr = preload("res://src/autoloads/SaveManager.gd").new()
		tree.root.add_child(save_mgr)
	
	# Mock data
	save_mgr.teammates = [{
		"id": "bob",
		"level": 2,
		"ingested_docs": ["med_db_v1", "legal_db_v2"],
		"equipped_model": "gemini-1.5-pro",
		"allow_react": true
	}]
	
	save_mgr.save_progress()
	
	# Wipe and reload
	save_mgr.teammates = []
	save_mgr.load_progress()
	
	if save_mgr.teammates.size() != 1:
		print("[test_teammate_progression] FAILED: teammates array size incorrect after load.")
		passed = false
	else:
		var loaded_tm = save_mgr.teammates[0]
		if loaded_tm.get("id") != "bob" or loaded_tm.get("level") != 2 or loaded_tm.get("equipped_model") != "gemini-1.5-pro":
			print("[test_teammate_progression] FAILED: teammate data mismatch.")
			passed = false
			
		var docs = loaded_tm.get("ingested_docs", [])
		if docs.size() != 2 or docs[0] != "med_db_v1":
			print("[test_teammate_progression] FAILED: ingested_docs mismatch.")
			passed = false
			
	if passed:
		print("[test_teammate_progression] PASSED")
	return passed
