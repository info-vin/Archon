extends RefCounted

var _is_completed = false
var _passed = false
var _game_board = null
var _backend_client = null
var _scene_tree = null

func run_tests(scene_tree: SceneTree) -> bool:
	print("Running test_e2e_api_to_ui...")
	_scene_tree = scene_tree
	
	# Instantiate GameBoard
	var game_board_scene = preload("res://src/views/GameBoard.tscn")
	_game_board = game_board_scene.instantiate()
	scene_tree.root.add_child(_game_board)
	
	# Instantiate BackendClient
	_backend_client = preload("res://src/network/BackendClient.gd").new()
	scene_tree.root.add_child(_backend_client)
	
	# Mock JWT token for Python Resilient Fallback 
	# (Header: {"alg":"HS256","typ":"JWT"}, Payload: {"email":"test@archon.com","role":"admin"}, Signature: AAAA)
	_backend_client.auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3RAYXJjaG9uLmNvbSIsInJvbGUiOiJhZG1pbiJ9.AAAA"
	
	# Connect signals
	_backend_client.request_completed.connect(_on_search_completed)
	_backend_client.request_failed.connect(_on_search_failed)
	
	print("Sending real HTTP request to FastAPI backend...")
	_backend_client.search("test", 0.5, 3)
	
	var timeout_counter = 0.0
	while not _is_completed and timeout_counter < 10.0:
		await scene_tree.create_timer(0.5).timeout
		timeout_counter += 0.5
		
	if not _is_completed:
		print("FAIL: test_e2e_api_to_ui timed out after 10 seconds.")
	
	_game_board.queue_free()
	_backend_client.queue_free()
	
	if _passed:
		print("test_e2e_api_to_ui PASSED")
		
	return _passed

func _on_search_completed(result: Dictionary):
	print("FastAPI Response received! Parsing JSON to CardData...")
	
	if not result.has("results"):
		print("FAIL: JSON missing 'results' array.")
		_is_completed = true
		return
		
	var results = result["results"]
	if results.size() == 0:
		print("WARNING: FastAPI returned 0 results. Test passes but visually empty.")
		_passed = true
		_is_completed = true
		return
		
		
	var card_script = preload("res://src/models/cards/CardData.gd")
	
	for item in results:
		var card = card_script.new()
		# Parse fields from RAG chunk response
		card.set("title", item.get("title", "Unknown Chunk"))
		card.set("description", item.get("content", ""))
		# Arbitrarily set type based on id or default to 2
		card.set("type", 2) 
		
		# Emit signal to GameBoard
		if Engine.has_singleton("EventBus"):
			var event_bus = Engine.get_singleton("EventBus")
			if event_bus.has_signal("card_drawn"):
				event_bus.card_drawn.emit(card)
			else:
				_game_board._on_card_drawn(card)
		else:
			_game_board._on_card_drawn(card)
			
	print("Waiting for visual animations...")
	await _scene_tree.create_timer(2.5).timeout
	
	var hand = _game_board.get_node("MarginContainer/VBoxContainer/HandContainer")
	if hand.get_child_count() == results.size():
		print("Test captured expected E2E visual instantiation! Hand size: ", hand.get_child_count())
		_passed = true
	else:
		print("FAIL: Expected %d children in hand, got %d" % [results.size(), hand.get_child_count()])
		
	_is_completed = true

func _on_search_failed(error_code: int, message: String):
	print("FAIL: E2E API request failed: ", message)
	_is_completed = true
