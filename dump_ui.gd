
extends SceneTree

func _init():
    var Teammates = load("res://src/views/TeammateDashboard.tscn")
    var t = Teammates.instantiate()
    root.add_child(t)
    
    # Force process
    await get_tree().process_frame
    await get_tree().process_frame
    
    # We want to capture the exact layout of the config vbox to see what went wrong.
    var vbox = t.get_node("MarginContainer/VBoxContainer/HBoxContainer/ConfigVBox")
    
    var f = FileAccess.open("user://ui_dump.txt", FileAccess.WRITE)
    f.store_line("ConfigVBox children:")
    for child in vbox.get_children():
        if child is Label:
            f.store_line("Label: " + child.text + " | Visible: " + str(child.visible))
        elif child is HBoxContainer:
            f.store_line("HBox: " + child.name)
            for sub in child.get_children():
                if sub is Label:
                    f.store_line("  - Label: " + sub.text)
                else:
                    f.store_line("  - Node: " + sub.name + " (" + sub.get_class() + ")")
    f.close()
    
    print("DUMP COMPLETE")
    quit()
