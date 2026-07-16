extends SceneTree

var output_dir = "/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/"

func _init() -> void:
    call_deferred("run_screenshots")

func run_screenshots() -> void:
    var path = "res://src/views/GameBoard.tscn"
    print("Capturing %s..." % path)
    var packed = load(path)
    var instance = packed.instantiate()
    root.add_child(instance)
    if instance is Control:
        instance.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    await process_frame
    await create_timer(1.0).timeout
    var img = root.get_texture().get_image()
    var path_out = output_dir + "screenshot_GameBoard_CurrentHUD.png"
    img.save_png(path_out)
    print("Saved to %s" % path_out)
    instance.queue_free()
    await process_frame
    quit(0)
