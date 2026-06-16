extends SceneTree

func _init():
    var main_scene = load("res://Scenes/Main/Main.tscn")
    if not main_scene:
        print("Error: Could not load Main.tscn")
        quit(1)
        return
        
    var root_node = main_scene.instantiate()
    root.add_child(root_node)
    
    # Spawn a neon test label
    var label = Label.new()
    label.text = "GLOW TEST"
    label.add_theme_font_size_override("font_size", 100)
    
    # Add a custom font using the downloaded TTF
    var font = FontFile.new()
    font.load_dynamic_font("res://Assets/Fonts/VT323-Regular.ttf")
    label.add_theme_font_override("font", font)
    
    # HDR Color! Red>1.0, Green>1.0, Blue=0
    # This should glow bright yellow/green
    label.modulate = Color(3.0, 5.0, 0.0)
    
    label.position = Vector2(300, 200)
    root_node.add_child(label)
    
    process_frame.connect(_on_frame)

var frames = 0
func _on_frame():
    frames += 1
    if frames == 10:
        var img = root.get_viewport().get_texture().get_image()
        var dest_path = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/glow_test.png"
        img.save_png(dest_path)
        print("🟢 SUCCESS: Exported glow test to ", dest_path)
        quit(0)
