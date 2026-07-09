extends RefCounted

func run_tests(tree = null) -> bool:
    print("Running test_meta_progression...")
    
    # Pre-setup
    var sm = preload("res://src/autoloads/SaveManager.gd").new()
    Engine.register_singleton("SaveManager", sm)
    
    var cr = preload("res://src/managers/CardRegistry.gd").new()
    Engine.register_singleton("CardRegistry", cr)
    cr._ready() # Load resources
    
    var eb = preload("res://src/autoloads/EventBus.gd").new()
    Engine.register_singleton("EventBus", eb)
    
    var game_state = preload("res://src/autoloads/GameState.gd").new()
    Engine.register_singleton("GameState", game_state)
    
    # Run _ready to ensure signal hookups
    game_state._ready()
    
    # Mock some basic progression data
    sm.career_level = 4
    sm.max_player_hp = 110.0
    sm.equipped_action_cards = ["action_keyword", "action_reranker"] # only equip 2
    
    var drawn_cards = []
    eb.card_drawn.connect(func(c): drawn_cards.append(c))
    
    # Test GameState Start
    var gs = game_state
    gs.start_game()
    
    if gs.max_player_hp != 110.0:
        print("FAIL: GameState should sync max_player_hp from SaveManager")
        return false
    if gs.player_hp != 110.0:
        print("FAIL: GameState should start with max_player_hp")
        return false
    
    if drawn_cards.size() != 2:
        print("FAIL: Should only draw the 2 equipped cards")
        return false
    if drawn_cards[0].get("id") != "action_keyword":
        print("FAIL: First card should be action_keyword")
        return false
    if drawn_cards[1].get("id") != "action_reranker":
        print("FAIL: Second card should be action_reranker")
        return false
    
    # Cleanup
    Engine.unregister_singleton("SaveManager")
    Engine.unregister_singleton("CardRegistry")
    Engine.unregister_singleton("EventBus")
    Engine.unregister_singleton("GameState")
    sm.free()
    cr.free()
    eb.free()
    game_state.free()
    
    print("test_meta_progression PASSED")
    return true
