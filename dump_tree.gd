extends SceneTree

func _init():
    var Teammates = load("res://src/views/TeammateDashboard.tscn")
    var t = Teammates.instantiate()
    root.add_child(t)
    
    print("\n--- EXACT NODE TEXTS IN TEAMMATE DASHBOARD ---")
    
    var vbox = t.get_node("MarginContainer/VBoxContainer/HBoxContainer/ConfigVBox")
    for child in vbox.get_children():
        if child is Label:
            print("Label: " + child.text)
        elif child is HBoxContainer:
            for sub in child.get_children():
                if sub is Label:
                    print("SubLabel: " + sub.text)
    
    print("--- DUMP COMPLETE ---")
    quit()
