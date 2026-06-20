extends MiniTest

func test_agent_visual_room_relocation() -> void:
    var scene = load("res://Scenes/Main/Main.tscn")
    assert_not_null(scene, "Main scene should be loadable")

    var view = scene.instantiate()
    view.set_script(load("res://Scripts/Main.gd"))
    
    var dev_room_node = view.get_node("VBox/HBoxMain/GameArea/Building/OfficeGrid/DevRoom")
    dev_room_node.set_script(load("res://Scripts/UI/OfficeRoom.gd"))
    var break_room_node = view.get_node("VBox/HBoxMain/GameArea/Building/OfficeGrid/BreakRoom")
    break_room_node.set_script(load("res://Scripts/UI/OfficeRoom.gd"))

    view.instant_positioning = true
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    await tree.process_frame 

    # Now that the node is inside the tree, `@onready` variables are resolved
    view.tycoon_manager = preload("res://Scripts/Logic/TycoonManager.gd").new()
    view.dev_room.setup_room("DevRoom", Color("#39ff14"), view.tycoon_manager)

    # Wait until views are fully spawned
    var timeout = 50
    while not view.agent_views.has(0) and timeout > 0:
        await tree.process_frame
        timeout -= 1

    assert_true(view.agent_views.has(0), "Alice view should be spawned")
    var alice_view = view.agent_views[0]
    assert_eq(alice_view.get_parent(), view.dev_room, "Alice should start in DevRoom")

    # Change Alice state to WORKING
    var alice_agent = view.agent_manager.get_agent(0)
    alice_agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING
    view._update_ui()

    # Assert Position - DeskPoint_1 is (65, 230)
    assert_eq(alice_view.position, Vector2(65, 230), "Alice position should be at DEV desk")

    # Change Alice state to RESTING
    alice_agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.RESTING
    view._update_ui()

    # Should be in BreakRoom - DeskPoint_1 is (152, 112)
    assert_eq(alice_view.get_parent(), view.break_room, "Alice should be in BreakRoom when RESTING")
    assert_eq(alice_view.position, Vector2(152, 112), "Alice position should be at DeskPoint_1")

    view.queue_free()
    
    view.queue_free()

func test_crisis_visual_pulse_active() -> void:
    var scene = load("res://Scenes/Main/Main.tscn")
    var view = scene.instantiate()
    view.instant_positioning = true
    # Ensure router is set (it should be set by _ready)
    assert_not_null(view.agent_router, 'AgentRouter should be initialized')
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
