extends SceneTree

func _init():
    var board = preload("res://src/views/GameBoard.tscn").instantiate()
    root.add_child(board)
    print("Hand container children before start: ", board.hand_container.get_child_count())
    
    var game_state = preload("res://src/autoloads/GameState.gd").new()
    root.add_child(game_state)
    Engine.register_singleton("GameState", game_state)
    
    var event_bus = preload("res://src/autoloads/EventBus.gd").new()
    root.add_child(event_bus)
    Engine.register_singleton("EventBus", event_bus)
    
    var card_registry = preload("res://src/managers/CardRegistry.gd").new()
    root.add_child(card_registry)
    Engine.register_singleton("CardRegistry", card_registry)
    card_registry._ready()
    
    board._ready()
    
    # Simulate pressing start
    board._on_start_pressed()
    
    print("Hand container children after start: ", board.hand_container.get_child_count())
    quit()
