@tool
extends SceneTree

func _init():
    print("Building Node2D Isometric World with backgrounds...")
    
    # 2. Create World2D Scene
    var world = Node2D.new()
    world.name = "World2D"
    world.y_sort_enabled = true 
    world.set_script(load("res://Scripts/World2D.gd"))
    
    # Camera
    var camera = Camera2D.new()
    camera.name = "Camera2D"
    world.add_child(camera)
    camera.owner = world
    
    # Background Group
    var bg_node = Node2D.new()
    bg_node.name = "Backgrounds"
    bg_node.z_index = -10
    world.add_child(bg_node)
    bg_node.owner = world
    
    var bgs = [
        {"name": "central_lobby", "file": "central_lobby_bg.png", "pos": Vector2(0, 0)},
        {"name": "dev_room", "file": "dev_room_bg.png", "pos": Vector2(-240, -255)}, # Top Left?
        {"name": "sales_room", "file": "sales_room_bg.png", "pos": Vector2(240, 255)}, # Bottom Right?
        {"name": "qa_room", "file": "qa_room_bg.png", "pos": Vector2(240, -255)}, # Top Right?
        {"name": "break_room", "file": "break_room_bg.png", "pos": Vector2(-240, 255)}, # Bottom Left?
    ]
    
    for b in bgs:
        var tex = load("res://Assets/Rooms/" + b["file"])
        var sprite = Sprite2D.new()
        sprite.texture = tex
        sprite.name = b["name"]
        # Center them or place them according to a grid
        sprite.position = b["pos"]
        bg_node.add_child(sprite)
        sprite.owner = world
        
    # Objects Container (Y-Sort)
    var objects = Node2D.new()
    objects.name = "Objects"
    objects.y_sort_enabled = true
    world.add_child(objects)
    objects.owner = world
    
    var path_line = Line2D.new()
    path_line.name = "PathLine"
    path_line.default_color = Color(0, 1, 0, 0.5)
    path_line.width = 4.0
    world.add_child(path_line)
    path_line.owner = world
    
    # Save Scene
    var packed = PackedScene.new()
    packed.pack(world)
    ResourceSaver.save(packed, "res://Scenes/Main/World2D_with_bg.tscn")
    
    print("Done! Pure 2D Isometric World generated with backgrounds.")
    quit()
