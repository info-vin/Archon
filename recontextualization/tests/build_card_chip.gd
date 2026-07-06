@tool
extends SceneTree

func _init():
    print("Building CardChip.tscn...")
    var root = MarginContainer.new()
    root.name = "CardChip"
    root.set_anchors_preset(Control.PRESET_FULL_RECT)

    var frame = TextureRect.new()
    frame.name = "BackgroundFrame"
    frame.texture = load("res://assets/images/card_frame_blank.png")
    frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    frame.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    root.add_child(frame)
    frame.owner = root

    var slot = Control.new()
    slot.name = "ChipSlot"
    slot.set_anchors_preset(Control.PRESET_FULL_RECT)
    root.add_child(slot)
    slot.owner = root

    var chip = TextureRect.new()
    chip.name = "ChipIcon"
    chip.texture = load("res://assets/images/chip_green_target.png")
    chip.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    chip.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    
    var mat = ShaderMaterial.new()
    mat.shader = load("res://src/shaders/OctagonMask.gdshader")
    mat.set_shader_parameter("chamfer_ratio", 0.18)
    chip.material = mat
    
    # Anchor to 38.5% height and 50% width
    chip.set_anchor(SIDE_LEFT, 0.29)
    chip.set_anchor(SIDE_RIGHT, 0.71)
    chip.set_anchor(SIDE_TOP, 0.17)
    chip.set_anchor(SIDE_BOTTOM, 0.59)
    chip.set_anchors_preset(Control.PRESET_FULL_RECT, true)
    
    slot.add_child(chip)
    chip.owner = root

    var packed = PackedScene.new()
    var err = packed.pack(root)
    if err == OK:
        var dir = DirAccess.open("res://")
        if not dir.dir_exists("src/views"):
            dir.make_dir_recursive("src/views")
        ResourceSaver.save(packed, "res://src/views/CardChip.tscn")
        print("[Success] Saved CardChip.tscn")
    else:
        printerr("[Error] Failed to pack scene: ", err)

    quit()
