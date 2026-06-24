@tool
extends SceneTree

func _init():
    print("Populating HD-2D World3D GridMap for Editor...")
    
    var packed = load("res://Scenes/Main/World3D.tscn")
    if not packed:
        print("Error loading World3D.tscn")
        quit()
        return
        
    var world = packed.instantiate()
    var grid_map = world.get_node("GridMap")
    
    # 0 = floor_tile, 1 = wall_corner_SW
    grid_map.clear()
    
    # Build a 10x10 floor
    var width = 10
    var depth = 10
    for x in range(-width/2, width/2):
        for z in range(-depth/2, depth/2):
            grid_map.set_cell_item(Vector3i(x, 0, z), 0)
            
    # Add walls
    for x in range(-width/2, width/2):
        grid_map.set_cell_item(Vector3i(x, 1, -depth/2), 1)
    for z in range(-depth/2, depth/2):
        grid_map.set_cell_item(Vector3i(-width/2, 1, z), 1)
        
    # Place a desk (id=2) and chair (id=3) and server (id=4)
    grid_map.set_cell_item(Vector3i(0, 1, 0), 2) # desk
    grid_map.set_cell_item(Vector3i(0, 1, 1), 3) # chair
    grid_map.set_cell_item(Vector3i(2, 1, -2), 4) # server
    
    # Save it back
    var new_packed = PackedScene.new()
    new_packed.pack(world)
    var err = ResourceSaver.save(new_packed, "res://Scenes/Main/World3D.tscn")
    
    if err == OK:
        print("Successfully populated and saved World3D.tscn")
    else:
        print("Failed to save populated scene")
        
    quit()
