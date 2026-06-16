extends MiniTest

func test_l2_modules_initialization() -> void:
	var scene = load("res://Scenes/Main/Main.tscn")
	assert_not_null(scene, "Main scene should load")
	
	var view = scene.instantiate()
	assert_not_null(view, "Main view should instantiate")
	
	var root = tree.root
	root.add_child(view)
	await tree.process_frame
	
	# Assert L2 controller modules and configuration
	assert_not_null(view.config, "Config resource should be loaded")
	assert_not_null(view.hud_controller, "HUDController should be instantiated and attached")
	assert_not_null(view.lifecycle, "GameLifecycle should be instantiated and attached")
	
	# Assert script attachments on dynamic nodes
	assert_not_null(view.minimap_container, "MinimapContainer should exist")
	assert_true(view.minimap_container.has_method("update_minimap"), "MinimapContainer should have update_minimap method")
	
	assert_true(view.dev_room.has_method("setup_room"), "DevRoom drop script should inherit setup_room")
	assert_true(view.qa_room.has_method("setup_room"), "QARoom script should inherit setup_room")
	
	view.queue_free()
