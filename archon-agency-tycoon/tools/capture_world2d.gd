extends SceneTree

func _init():
    print("Assembling Refactored Scaled World2D puzzle and capturing screenshot...")
    
    var root = get_root()
    var packed_scene = load("res://Scenes/Main/World2D.tscn")
    var scene = packed_scene.instantiate()
    root.add_child(scene)
    
    # 給予足夠的運算等待時間，確保 Y-Sort 與 AStar 繪製完畢
    await create_timer(1.0).timeout
    
    var img = root.get_viewport().get_texture().get_image()
    var err = img.save_png("res://screenshot_puzzle.png")
    
    if err == OK:
        print("Screenshot saved to res://screenshot_puzzle.png")
    else:
        print("Failed to save screenshot: ", err)
        
    quit()
