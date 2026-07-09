extends RefCounted

func run_tests(tree = null) -> bool:
    print("Running test_save_manager...")
    
    # 1. Test Default Initialization
    var sm = preload("res://src/autoloads/SaveManager.gd").new()
    var dir = DirAccess.open("user://")
    if dir and dir.file_exists("archon_progress.json"):
        dir.remove("archon_progress.json")
        
    sm.load_progress()
    if sm.career_level != 3: return false
    if sm.max_player_hp != 100.0: return false
    if sm.equipped_action_cards.size() != 3: return false
    
    # 2. Test Max Equipped Cards Logic
    sm.career_level = 5
    if sm.get_max_equipped_cards() != 5: return false
    
    # 3. Test Save and Load
    sm.career_level = 6
    sm.max_player_hp = 120.0
    sm.unlocked_action_cards = ["action_keyword", "action_dense", "action_reranker", "action_graphrag"]
    sm.equipped_action_cards = ["action_keyword", "action_dense", "action_reranker", "action_graphrag"]
    sm.save_progress()
    
    var sm2 = preload("res://src/autoloads/SaveManager.gd").new()
    sm2.load_progress()
    if sm2.career_level != 6: return false
    if sm2.max_player_hp != 120.0: return false
    if sm2.equipped_action_cards.size() != 4: return false
    
    print("test_save_manager PASSED")
    return true
