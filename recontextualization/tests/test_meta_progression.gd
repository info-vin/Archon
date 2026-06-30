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
    
    var drawn_cards = []
    eb.card_drawn.connect(func(c): drawn_cards.append(c))
    
    # Mock Save Data
    sm.career_level = 4
    sm.max_player_hp = 110.0
    sm.equipped_action_cards = ["keyword_search", "reranker"] # only equip 2
    
    # Test GameState Start
    var gs = preload("res://src/autoloads/GameState.gd").new()
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
    if drawn_cards[0].get("id") != "keyword_search":
        print("FAIL: First card should be keyword_search")
        return false
    if drawn_cards[1].get("id") != "reranker":
        print("FAIL: Second card should be reranker")
        return false
    
    # Cleanup
    Engine.unregister_singleton("SaveManager")
    Engine.unregister_singleton("CardRegistry")
    Engine.unregister_singleton("EventBus")
    
    print("test_meta_progression PASSED")
    return true
