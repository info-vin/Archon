extends SceneTree

func _init():
    print("Assembling Scaled World2D puzzle and capturing screenshot...")
    
    var root = get_root()
    var packed_scene = load("res://Scenes/Main/World2D.tscn")
    var scene = packed_scene.instantiate()
    root.add_child(scene)
    
    await create_timer(1.0).timeout
    
    if scene.has_method("place_object"):
        # Engineering / Dev (Top Left, -x, -y)
        # Place desks and chairs aligned
        scene.place_object(Vector2i(-4, -4), "desk_sw")
        scene.place_object(Vector2i(-3, -4), "chair_se") # Chair facing desk
        
        scene.place_object(Vector2i(-6, -6), "desk_se")
        scene.place_object(Vector2i(-6, -5), "chair_sw") # Chair facing desk
        
        # QA (Top Right, +x, -y)
        # Row of server racks
        scene.place_object(Vector2i(3, -3), "server_sw")
        scene.place_object(Vector2i(4, -4), "server_sw")
        scene.place_object(Vector2i(5, -5), "server_sw")
        scene.place_object(Vector2i(6, -6), "server_sw")
        
        # Break Room (Bottom Left, -x, +y)
        # 3 sofas, vending machine, coffee machine
        scene.place_object(Vector2i(-3, 3), "sofa_sw")
        scene.place_object(Vector2i(-4, 4), "sofa_se")
        scene.place_object(Vector2i(-5, 5), "sofa_sw")
        
        scene.place_object(Vector2i(-2, 6), "vending_machine")
        scene.place_object(Vector2i(-6, 2), "coffee_machine")
        
        # Sales (Bottom Right, +x, +y)
        # Marketing/Sales desks
        scene.place_object(Vector2i(3, 3), "desk_se")
        scene.place_object(Vector2i(3, 4), "chair_sw")
        
        scene.place_object(Vector2i(5, 3), "desk_sw")
        scene.place_object(Vector2i(6, 3), "chair_se")
        
        # Room Corners
        scene.place_object(Vector2i(-8, -8), "wall") # Dev corner
        scene.place_object(Vector2i(8, -8), "wall")  # QA corner
        scene.place_object(Vector2i(-8, 8), "wall")  # Break corner
        scene.place_object(Vector2i(8, 8), "wall")   # Sales corner
        
    if scene.has_method("spawn_agent"):
        scene.spawn_agent(Vector2i(1, 1))
        
    if scene.has_method("move_agent_to"):
        scene.move_agent_to(Vector2i(2, -2))
        
    await create_timer(0.5).timeout
    
    var img = root.get_viewport().get_texture().get_image()
    var err = img.save_png("res://screenshot_puzzle.png")
    
    if err == OK:
        print("Screenshot saved to res://screenshot_puzzle.png")
    else:
        print("Failed to save screenshot: ", err)
        
    quit()
