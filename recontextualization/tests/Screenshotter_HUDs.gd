extends SceneTree

var output_dir = "/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/"

func _init() -> void:
    call_deferred("run_screenshots")

func run_screenshots() -> void:
    print("Capturing HUDs...")
    
    # Create a SubViewport to guarantee rendering in headless
    var vp = SubViewport.new()
    vp.size = Vector2(1280, 200)
    vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    vp.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
    vp.transparent_bg = true
    root.add_child(vp)
    
    var bg = ColorRect.new()
    bg.color = Color(0.05, 0.05, 0.05, 1.0) # Dark gray/black
    bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    vp.add_child(bg)
    
    var packed = load("res://src/views/components/GameHUD.tscn")
    var instance = packed.instantiate()
    vp.add_child(instance)
    
    if instance is Control:
        instance.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
        
    await process_frame
    await process_frame
    await create_timer(1.0).timeout
    
    var img = vp.get_texture().get_image()
    if img:
        var path_out = output_dir + "screenshot_Phase_5_8_22_HUDs.png"
        img.save_png(path_out)
        print("Saved to %s" % path_out)
    else:
        print("ERROR: Could not get image from viewport.")
        
    print("ALL SCREENSHOTS CAPTURED.")
    quit(0)
