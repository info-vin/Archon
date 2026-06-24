@tool
extends SceneTree

func _init():
    print("Creating HD-2D World3D scene...")
    
    var world = Node3D.new()
    world.name = "World3D"
    
    # GridMap
    var grid_map = GridMap.new()
    grid_map.name = "GridMap"
    grid_map.cell_size = Vector3(2, 2, 2)
    var mesh_lib = load("res://Assets/Rooms/isometric/HD2D_MeshLibrary.tres")
    if mesh_lib:
        grid_map.mesh_library = mesh_lib
    else:
        print("Warning: HD2D_MeshLibrary.tres not found!")
    
    world.add_child(grid_map)
    grid_map.owner = world
    
    # Lighting
    var light = DirectionalLight3D.new()
    light.name = "DirectionalLight3D"
    light.shadow_enabled = true
    light.rotation_degrees = Vector3(-45, 45, 0) # Top-down angle
    light.light_color = Color(0.8, 0.9, 1.0) # Cyberpunk moon light
    light.light_energy = 0.8
    world.add_child(light)
    light.owner = world
    
    # Attach Script
    var script = load("res://Scripts/World3D.gd")
    if script:
        world.set_script(script)
    else:
        print("Warning: World3D.gd not found!")
    
    # Save scene
    var packed = PackedScene.new()
    packed.pack(world)
    var err = ResourceSaver.save(packed, "res://Scenes/Main/World3D.tscn")
    if err == OK:
        print("Successfully saved res://Scenes/Main/World3D.tscn")
    else:
        print("Failed to save scene, error code: ", err)
        
    quit()
