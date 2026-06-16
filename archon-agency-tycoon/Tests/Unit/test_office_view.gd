extends MiniTest

func test_agent_visual_room_relocation() -> void:
    var scene = load("res://Scenes/Main/Main.tscn")
    assert_not_null(scene, "Main scene should be loadable")
    
    var view = scene.instantiate()
    assert_not_null(view, "Main view should be instantiable")
    
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    
    # Alice (DEV) has agent_id 0.
    # Initial state should be DEV room
    var alice_view = view.agent_views[0]
    assert_eq(alice_view.get_parent(), view.dev_room, "Alice should start in DevRoom")
    
    # Change Alice state to WORKING
    var alice_agent = view.agent_manager.get_agent(0)
    alice_agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING
    view._update_ui()
    
    # Should still be in DevRoom but position shifted to desk
    assert_eq(alice_view.get_parent(), view.dev_room, "Alice should remain in DevRoom when WORKING")
    assert_eq(alice_view.position, Vector2(30 + 32, 80 + 32), "Alice position should be at DEV desk")
    
    # Change Alice state to RESTING
    alice_agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.RESTING
    view._update_ui()
    
    # Should be in BreakRoom
    assert_eq(alice_view.get_parent(), view.break_room, "Alice should be in BreakRoom when RESTING")
    assert_eq(alice_view.position, Vector2(120 + 32, 80 + 32), "Alice position should be at Sofa")
    
    view.queue_free()

func test_crisis_visual_pulse_active() -> void:
    var scene = load("res://Scenes/Main/Main.tscn")
    var view = scene.instantiate()
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    
    # Trigger crisis spawned on DevRoom
    view.tycoon_manager.crisis_spawned.emit("DevRoom")
    assert_not_null(view.dev_room.crisis_tween, "Crisis tween should be active on DevRoom")
    
    # Trigger crisis resolved
    view.tycoon_manager.crisis_resolved.emit("DevRoom")
    assert_eq(view.dev_room.crisis_tween, null, "Crisis tween should be cleared after resolution")
    assert_eq(view.dev_room.modulate, Color.WHITE, "DevRoom modulate should be reset to white")
    
    view.queue_free()
