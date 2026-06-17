extends MiniTest

func test_help_menu_popup_and_close() -> void:
    var scene = load("res://Scenes/Main/Main.tscn")
    var view = scene.instantiate()
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    await tree.process_frame # Ensure Main.gd _ready() completed
    
    # 1. Initially HelpMenu should not exist
    assert_eq(view.hud_controller.main_node.help_menu_instance, null, "HelpMenu should start as null")
    
    # 2. Simulate pressing H
    var ev_h = InputEventKey.new()
    ev_h.keycode = KEY_H
    ev_h.pressed = true
    view._unhandled_input(ev_h)
    
    assert_not_null(view.hud_controller.main_node.help_menu_instance, "HelpMenu should open when H is pressed")
    assert_eq(view.hud_controller.main_node.help_menu_instance.get_parent(), view, "HelpMenu parent should be the Main view")
    
    # 3. Simulate pressing ESC on HelpMenu
    var ev_esc = InputEventKey.new()
    ev_esc.keycode = KEY_ESCAPE
    ev_esc.pressed = true
    
    var menu = view.hud_controller.main_node.help_menu_instance
    menu._unhandled_input(ev_esc)
    
    # Wait for the closed signal of the HelpMenu
    await menu.closed
    await tree.process_frame
    
    assert_eq(view.hud_controller.main_node.help_menu_instance, null, "HelpMenu reference should be cleared after close")
    
    view.queue_free()

func test_agent_energy_and_bubble_visuals() -> void:
    var scene = load("res://Scenes/Main/Main.tscn")
    var view = scene.instantiate()
    if view.get_script() == null: view.set_script(load('res://Scripts/Main.gd'))
    view.instant_positioning = true
    var root = tree.root
    root.add_child(view)
    
    # Wait until views are fully spawned to prevent async race conditions
    var timeout = 50
    while not view.agent_views.has(0) and timeout > 0:
        await tree.process_frame
        timeout -= 1
        
    assert_true(view.agent_views.has(0), "Alice view should be spawned")
    # Alice (DEV) is agent_id 0
    var alice_view = view.agent_views[0]
    var alice_agent = view.agent_manager.get_agent(0)
    
    # Initial status
    assert_eq(alice_view.energy_bar.value, 100.0, "Energy bar value should start at 100")
    assert_false(alice_view.status_bubble.visible, "Status bubble should start hidden for IDLE state")
    
    # Change energy and set WORKING
    alice_agent.energy = 40
    alice_agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING
    view._update_ui()
    
    assert_eq(alice_view.energy_bar.value, 40.0, "Energy bar value should update to 40")
    assert_eq(alice_view.energy_bar.modulate, Color(1, 1, 0.2), "Energy bar modulate should be Yellow for value 40")
    assert_true(alice_view.status_bubble.visible, "Status bubble should show when WORKING")
    assert_not_null(alice_view.status_bubble.texture, "Working status bubble should have a texture")
    
    # Set RESTING
    alice_agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.RESTING
    view._update_ui()
    assert_true(alice_view.status_bubble.visible, "Status bubble should show when RESTING")
    
    view.queue_free()
