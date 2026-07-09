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
        await create_timer(0.2).timeout
        
        var img = root.get_texture().get_image()
        var path_out = output_dir + "screenshot_%s.png" % scene_name
        
        if scene_name == "TeammateDashboard":
            var ctrl = instance.get_node("TeammateDashboardController")
            if ctrl:
                var mock_teammates = [
                    {"name": "Alice", "level": 5},
                    {"name": "Bob", "level": 4},
                    {"name": "Charlie", "level": 3},
                    {"name": "Default", "level": 1}
                ]
                instance.populate_teammates(mock_teammates)
                instance.set_max_token_budget(15)
                
            if instance.has_method("_on_teammate_item_selected") and instance.has_method("_on_toggle_deploy_clicked"):
                instance._on_teammate_item_selected(1) # Focus Bob
                instance._on_toggle_deploy_clicked()   # Deploy Bob (Cost 8)
                instance._on_teammate_item_selected(0) # Focus Alice
                instance._on_toggle_deploy_clicked()   # Deploy Alice (Cost 10) -> Warning!
            await create_timer(0.4).timeout
            img = root.get_texture().get_image()
            
        if scene_name == "CardWorkshop":
            instance.get_node("CardWorkshopController").current_cards_in_furnace = [{"base_id": "action_keyword", "level": 1}, {"base_id": "action_keyword", "level": 1}, {"base_id": "action_keyword", "level": 1}]
            instance.update_furnace_slots([{"base_id": "action_keyword", "level": 1}, {"base_id": "action_keyword", "level": 1}, {"base_id": "action_keyword", "level": 1}])
            await process_frame
            await create_timer(0.2).timeout
            # Save Before Screenshot
            var img_before = root.get_texture().get_image()
            img_before.save_png(output_dir + "screenshot_CardWorkshop_Before.png")
            
            instance.play_success_anim()
            await create_timer(0.6).timeout
            # Save After Screenshot
            path_out = output_dir + "screenshot_CardWorkshop_After.png"
            img = root.get_texture().get_image()
            
        if scene_name == "CharacterDashboard" and instance.has_method("debug_trigger_node"):
            instance.debug_trigger_node(0)
            await create_timer(1.5).timeout
            img = root.get_texture().get_image()
            
        img.save_png(path_out)
        print("Saved to %s" % path_out)
        
        instance.queue_free()
        await process_frame
        
    print("ALL SCREENSHOTS CAPTURED.")
    quit(0)
