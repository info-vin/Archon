extends SceneTree

var output_dir = "/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/"

func _init() -> void:
    # Schedule screenshot process
    call_deferred("run_screenshots")

func run_screenshots() -> void:
    var scenes = [
        "res://src/views/TeammateDashboard.tscn",
        "res://src/views/CardManagementMenu.tscn",
        "res://src/views/CardWorkshop.tscn",
        "res://src/views/CharacterDashboard.tscn"
    ]
    
    for path in scenes:
        var scene_name = path.get_file().replace(".tscn", "")
        print("Capturing %s..." % scene_name)
        
        var packed = load(path)
        var instance = packed.instantiate()
        
        # Add to root viewport
        root.add_child(instance)
        
        # Ensure it takes full screen if it's a Control
        if instance is Control:
            instance.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
            
        # Wait for Godot to render the frame
        await process_frame
        await process_frame
        await create_timer(0.2).timeout
        
        if scene_name == "CharacterDashboard" and instance.has_method("debug_trigger_node"):
            instance.debug_trigger_node(0)
            await create_timer(1.5).timeout
        
        var img = root.get_texture().get_image()
        var out_path = output_dir + "screenshot_" + scene_name + ".png"
        img.save_png(out_path)
        print("Saved to %s" % out_path)
        
        instance.queue_free()
        await process_frame
        
    print("ALL SCREENSHOTS CAPTURED.")
    quit(0)
