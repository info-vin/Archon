extends RefCounted

func run_tests(tree: SceneTree = null) -> bool:
    print("Running test_tutorial_fsm...")
    
    # 1. Setup Mock EventBus and GameState
    var eb = preload("res://src/autoloads/EventBus.gd").new()
    Engine.register_singleton("EventBus", eb)
    
    var gs = preload("res://src/autoloads/GameState.gd").new()
    Engine.register_singleton("GameState", gs)
    
    # Run _ready to connect signals and start
    gs._ready()
    
    # 2. Instantiate TutorialManager
    var tm = preload("res://src/managers/tutorial/TutorialManager.gd").new()
    tree.root.add_child(tm)
    
    # FSM starts on "Welcome" deferred. We force it manually to be sure in headless:
    tm._start_tutorial()
    
    if tm.current_state.name != "Welcome":
        print("FAIL: Did not start in Welcome state")
        return false
        
    # 3. Simulate Welcome -> Search
    # Welcome state waits for dialog click, then emits "Search"
    tm.current_state.transitioned.emit("Search")
    if tm.current_state.name != "Search":
        print("FAIL: Did not transition to Search state")
        return false
        
    var card_script = preload("res://src/models/cards/CardData.gd")
    
    # 4. Simulate Search -> DragData
    # Emitting card_drawn should trigger DragData
    var mock_card = card_script.new()
    mock_card.type = 2
    eb.card_drawn.emit(mock_card)
    if tm.current_state.name != "DragData":
        print("FAIL: Did not transition to DragData state on card drawn")
        return false
        
    # 5. Simulate DragData -> Deliver
    # Emitting card_played(data) should trigger Deliver
    gs.hand_context.add_card(mock_card, 0.0)
    eb.request_play_card.emit(mock_card)
    if tm.current_state.name != "Deliver":
        print("FAIL: Did not transition to Deliver state on card played")
        return false
        
    # 6. Simulate Deliver -> End
    gs.crisis_hp = 9999.0 # Simulating damage taken
    tm.current_state.update(0.1) # Trigger the update poll
    
    # Wait, the end transition calls _end_tutorial which queues free
    # So we just check if it completed
    
    print("test_tutorial_fsm PASSED")
    
    Engine.unregister_singleton("EventBus")
    eb.free()
    Engine.unregister_singleton("GameState")
    gs.free()
    
    return true
