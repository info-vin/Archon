extends MiniTest

func test_option_a_positioning() -> void:
    var scene = load("res://Scenes/Main/ModularAgent.tscn")
    assert_not_null(scene, "ModularAgent scene should be loadable")
    
    var view = scene.instantiate()
    assert_not_null(view, "ModularAgent view should be instantiable")
    
    # Add to tree so onready variables are initialized
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    
    view.reset_layout_for_option_a()
    
    assert_eq(view.body_sprite.position, Vector2.ZERO, "Body position should be zero")
    assert_eq(view.eyes_sprite.position, Vector2(0, -27), "Eyes position should be aligned")
    assert_eq(view.hair_sprite.position, Vector2(0, -18), "Hair position should be aligned")
    assert_eq(view.outfit_sprite.position, Vector2(0, 2), "Outfit position should be aligned")
    assert_eq(view.tool_sprite.position, Vector2(18, 6), "Tool position should be aligned")
    
    view.queue_free()

func test_default_role_outfits() -> void:
    var scene = load("res://Scenes/Main/ModularAgent.tscn")
    var view = scene.instantiate()
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Alice", 1) # 1 = DEV
    view.apply_agent_data(agent)
    assert_not_null(view.body_sprite.texture, "Should load body sprite")
    assert_eq(view.tool_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_033.png", "DEV should hold DEV wand")
    
    agent.role = 0 # SALES
    agent.tool_style = 2
    view.apply_agent_data(agent)
    assert_eq(view.tool_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_031.png", "SALES should hold SALES Cards")
    
    agent.role = 2 # QA
    agent.tool_style = 3
    view.apply_agent_data(agent)
    assert_eq(view.tool_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_026.png", "QA should hold QA Spell")
    
    view.queue_free()

func test_custom_outfit_loading() -> void:
    var scene = load("res://Scenes/Main/ModularAgent.tscn")
    var view = scene.instantiate()
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    
    # Define an agent with custom paths (pointing to existing placeholder svgs)
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new(
        "Bob", 1, 0, 0, 0, 0,
        "res://Assets/Characters/char_dev.svg",
        "res://Assets/Characters/char_sales.svg",
        "res://Assets/Characters/char_qa.svg"
    )
    
    view.apply_agent_data(agent)
    
    assert_not_null(view.hair_sprite.texture, "Custom hair should be loaded")
    assert_not_null(view.outfit_sprite.texture, "Custom outfit should be loaded")
    assert_not_null(view.tool_sprite.texture, "Custom tool should be loaded")
    
    view.queue_free()

func test_state_animation_triggers() -> void:
    var scene = load("res://Scenes/Main/ModularAgent.tscn")
    var view = scene.instantiate()
    var root = tree.root
    root.add_child(view)
    await tree.process_frame
    
    var agent = preload("res://Scripts/Resources/AgentResource.gd").new("Charlie", 2) # QA
    
    # Test Working state triggers work animation
    agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.WORKING
    view.apply_agent_data(agent)
    assert_eq(view.get_node("AnimationPlayer").current_animation, "work", "Animation should be work for WORKING state")
    assert_true(view.tool_sprite.visible, "Tool should be visible during working")
    
    # Test Resting state triggers rest animation
    agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.RESTING
    view.apply_agent_data(agent)
    assert_eq(view.get_node("AnimationPlayer").current_animation, "rest", "Animation should be rest for RESTING state")
    assert_false(view.tool_sprite.visible, "Tool should be hidden during resting")
    
    # Test Idle state stops animation
    agent.state = preload("res://Scripts/Resources/AgentResource.gd").AgentState.IDLE
    view.apply_agent_data(agent)
    assert_eq(view.get_node("AnimationPlayer").current_animation, "idle", "Animation should be idle for IDLE state")
    
    view.queue_free()
