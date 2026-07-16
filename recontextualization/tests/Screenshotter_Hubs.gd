extends SceneTree

var output_dir = "/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/"

func _init() -> void:
	call_deferred("run_flow")

func run_flow() -> void:
	print("Capturing Hubs Flow...")
	TranslationServer.set_locale("zh_TW")
	
	var event_bus = load("res://src/autoloads/EventBus.gd").new()
	var game_state = load("res://src/autoloads/GameState.gd").new()
	var save_manager = load("res://src/autoloads/SaveManager.gd").new()
	root.add_child(event_bus)
	root.add_child(game_state)
	root.add_child(save_manager)
	
	game_state.name = "GameState"
	event_bus.name = "EventBus"
	save_manager.name = "SaveManager"
	
	game_state._ready()
	game_state.start_game()
	
	var hubs = [
		{"name": "CharacterDashboard", "path": "res://src/views/CharacterDashboard.tscn"},
		{"name": "CardManagementMenu", "path": "res://src/views/CardManagementMenu.tscn"},
		{"name": "CardWorkshop", "path": "res://src/views/CardWorkshop.tscn"},
		{"name": "TeammateDashboard", "path": "res://src/views/TeammateDashboard.tscn"}
	]
	
	var index = 1
	for hub_data in hubs:
		var scene_packed = load(hub_data["path"])
		if not scene_packed:
			print("Error: Could not load " + hub_data["path"])
			continue
			
		var scene = scene_packed.instantiate()
		root.add_child(scene)
		
		if scene is Control:
			scene.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		
		await process_frame
		await create_timer(1.0).timeout
		
		var img = root.get_texture().get_image()
		var file_path = output_dir + "hub_" + str(index) + "_" + hub_data["name"] + ".png"
		img.save_png(file_path)
		print("Saved screenshot: " + file_path)
		
		root.remove_child(scene)
		scene.queue_free()
		index += 1
		
	print("ALL HUB SCREENSHOTS CAPTURED.")
	quit()
