extends Node

var tests_passed = 0
var tests_failed = 0

var _game_board = null
var _signal_emitted = false
var _emitted_card_data = null

func _on_card_played(card: Resource):
	_signal_emitted = true
	_emitted_card_data = card

func run_tests(runner) -> bool:
	print("Running test_drag_and_drop...")
	
	# Setup Scene
	_game_board = preload("res://src/views/GameBoard.tscn").instantiate()
	runner.root.add_child(_game_board)
	
	# Connect to EventBus
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		if event_bus.has_signal("card_played"):
			event_bus.card_played.connect(_on_card_played)
	else:
		print("Manually instantiating EventBus for headless test")
		var event_bus = preload("res://src/autoloads/EventBus.gd").new()
		Engine.register_singleton("EventBus", event_bus)
		event_bus.card_played.connect(_on_card_played)
	
	var card_script = preload("res://src/models/cards/CardData.gd")
	var card = card_script.new()
	card.set("title", "Test Drag Card")
	card.set("type", 1)
	
	var card_chip = preload("res://src/views/CardChip.tscn").instantiate()
	var hand = _game_board.get_node("MarginContainer/VBoxContainer/HandContainer")
	var play_area = _game_board.get_node("MarginContainer/VBoxContainer/PlayArea")
	
	hand.add_child(card_chip)
	card_chip.set_card_data(card)
	
	# Test 1: _get_drag_data
	var drag_data = card_chip._get_drag_data(Vector2(0, 0))
	if drag_data == card_chip:
		print("Test captured expected drag data.")
	else:
		print("FAIL: _get_drag_data did not return self.")
		tests_failed += 1
		
	# Test 2: _can_drop_data
	var can_drop = play_area._can_drop_data(Vector2(50, 50), drag_data)
	if can_drop:
		print("Test confirmed can drop.")
	else:
		print("FAIL: _can_drop_data returned false for valid card.")
		tests_failed += 1
		
	# Test 3: _drop_data
	if Engine.has_singleton("EventBus"):
		var eb = Engine.get_singleton("EventBus")
		if eb.has_signal("request_play_card"):
			eb.request_play_card.connect(_on_card_played)
			
	play_area._drop_data(Vector2(50, 50), drag_data)
	
	# Wait for Tween to finish (0.4s) before checking signal
	await runner.create_timer(1.5).timeout
	
	if _signal_emitted and _emitted_card_data == card:
		print("Test confirmed request_play_card signal emitted with correct data.")
	else:
		print("FAIL: request_play_card signal was not emitted or data was wrong.")
		tests_failed += 1
		
	# Cleanup
	_game_board.queue_free()
	
	if Engine.has_singleton("EventBus"):
		var event_bus = Engine.get_singleton("EventBus")
		Engine.unregister_singleton("EventBus")
		event_bus.free()
	
	if tests_failed == 0:
		print("test_drag_and_drop PASSED")
		return true
	else:
		return false
