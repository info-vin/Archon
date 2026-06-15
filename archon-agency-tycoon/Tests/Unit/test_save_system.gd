extends MiniTest

func test_local_save_and_load() -> void:
    # 1. Setup the manager with a LOCAL adapter pointing to a test file
    var manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    var test_save_path = "user://test_savegame.json"
    var adapter = preload("res://Scripts/Logic/SaveSystems/LocalSaveAdapter.gd").new(test_save_path)
    manager.set_save_adapter(adapter)
    
    # 2. Modify game state
    manager.funds = 9999
    manager.reputation = 85
    manager.current_phase = 2
    
    # 3. Save the game
    var save_success = await manager.save_game()
    assert_true(save_success, "Game should save successfully to local disk")
    
    # 4. Create a BRAND NEW manager to simulate restarting the game
    var new_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    new_manager.set_save_adapter(adapter)
    
    # 5. Assert default state before loading
    assert_eq(new_manager.funds, 500, "New manager should start with default 500 funds")
    
    # 6. Load the game
    var load_success = await new_manager.load_game()
    assert_true(load_success, "Game should load successfully from local disk")
    
    # 7. Assert state was restored
    assert_eq(new_manager.funds, 9999, "Funds should be restored to 9999")
    assert_eq(new_manager.reputation, 85, "Reputation should be restored to 85")
    assert_eq(new_manager.current_phase, 2, "Phase should be restored to 2")
    
    # Cleanup test file
    DirAccess.remove_absolute(test_save_path)

func test_save_without_adapter_fails() -> void:
    var manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    # No adapter set
    var save_success = await manager.save_game()
    assert_false(save_success, "Save should fail if no adapter is set")
