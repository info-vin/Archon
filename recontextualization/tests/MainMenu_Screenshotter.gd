extends SceneTree

var output_dir = "/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/"

func _init() -> void:
    call_deferred("run_screenshots")

func run_screenshots() -> void:
    var scene_name = "MainMenu"
    print("Capturing %s..." % scene_name)
    
    var packed = load("res://src/views/MainMenu.tscn")
    var instance = packed.instantiate()
    
    root.add_child(instance)
    
    if instance is Control:
        instance.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
        
    await process_frame
    await create_timer(6.5).timeout
    
    var img = root.get_texture().get_image()
    var path_out = output_dir + "screenshot_%s.png" % scene_name
    img.save_png(path_out)
    print("Saved to %s" % path_out)
    
    # Test Carousel Input
    print("Testing input: ui_right")
    var event = InputEventAction.new()
    event.action = "ui_right"
    event.pressed = true
    Input.parse_input_event(event)
    await process_frame
    await create_timer(0.5).timeout
    
    img = root.get_texture().get_image()
    path_out = output_dir + "screenshot_%s_Right.png" % scene_name
    img.save_png(path_out)
    print("Saved to %s" % path_out)
    
    print("ALL SCREENSHOTS CAPTURED.")
    quit(0)
