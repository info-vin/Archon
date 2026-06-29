extends RefCounted

func run_tests(scene_tree: SceneTree) -> bool:
	print("Running test_backend_client...")
	
	var client_script = preload("res://src/network/BackendClient.gd")
	var client = client_script.new()
	scene_tree.root.add_child(client)
	
	var state = [false]
	
	client.request_failed.connect(func(code, msg):
		state[0] = true
		print("Test captured expected failure: ", msg)
	)
	
	client.search("test query", 0.82, 10)
	
	# Wait for max retries (3 retries * 1.0s delay = ~3s)
	print("Waiting for retries to complete...")
	await scene_tree.create_timer(5.0).timeout
	
	client.queue_free()
	
	if state[0]:
		print("test_backend_client PASSED (Fallback mechanism works)")
		return true
	else:
		print("test_backend_client FAILED (Did not emit request_failed after retries)")
		return false
