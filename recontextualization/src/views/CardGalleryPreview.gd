@tool
extends ScrollContainer

@onready var grid: GridContainer = $MarginContainer/GridContainer

func _ready():
    # Only run in editor or when explicitly needed
    if Engine.is_editor_hint():
        _generate_gallery()

func _generate_gallery():
    # Fallback for headless tests where @onready might not resolve instantly
    if grid == null and has_node("MarginContainer/GridContainer"):
        grid = $MarginContainer/GridContainer
        
    # Clear existing children if any
    if grid:
        for child in grid.get_children():
            grid.remove_child(child)
            child.queue_free()
    
    var dir = DirAccess.open("res://assets/images/")
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        var card_scene = load("res://src/views/CardChip.tscn")
        while file_name != "":
            if !dir.current_is_dir() and file_name.ends_with(".png"):
                if file_name.begins_with("chip_") or file_name.begins_with("action_"):
                    var tex = load("res://assets/images/" + file_name)
                    var base_name = file_name.replace(".png", "")
                    
                    var card_name = tr("card_name_" + base_name)
                    
                    var stats = ""
                    if base_name.begins_with("action_"):
                        var cost_text = tr("card_stat_cost").replace("%d", "2")
                        var effect_text = tr("card_stat_effect").replace("%d", "15")
                        stats = "[center][color=#44ffcc]" + cost_text + "[/color]\n[color=#ffaa44]" + effect_text + "[/color][/center]"
                    else:
                        var state = tr("card_stat_status_pure") if "green" in base_name else tr("card_stat_status_corrupted")
                        var size_text = tr("card_stat_size").replace("%s", "256 MB")
                        stats = "[center][color=#44ccff]" + size_text + "[/color]\n[color=#ff4444]" + state + "[/color][/center]"
                    
                    var card_instance = card_scene.instantiate()
                    
                    if grid:
                        grid.add_child(card_instance)
                        if card_instance.has_method("setup"):
                            card_instance.setup(tex, card_name, stats)
                        else:
                            printerr("CardChip missing setup() method!")
            file_name = dir.get_next()
