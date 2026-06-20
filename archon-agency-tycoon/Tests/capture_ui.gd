extends SceneTree

func _initialize() -> void:
	print("--- 📸 執行實體渲染 UI 視覺截圖公證 ---")
	
	# Load and instance the Main scene
	var scene = load("res://Scenes/Main/Main.tscn")
	if not scene:
		print("🔴 無法載入主場景 Main.tscn")
		quit(1)
		return
		
	var main_node = scene.instantiate()
	root.add_child(main_node)
	
	# Wait for a few frames to let UI build layout, load theme, and position elements
	for i in range(30):
		await process_frame
		
	# Grab viewport image
	var image = root.get_texture().get_image()
	if not image:
		print("🔴 無法獲取 Viewport Image")
		quit(1)
		return
		
	var dir = DirAccess.open("res://")
	if not dir.dir_exists("screenshots"):
		dir.make_dir("screenshots")
		
	var save_path = "res://screenshots/proof_phase5_7_2.png"
	var err = image.save_png(save_path)
	if err == OK:
		print("🟢 UI 視覺公證截圖成功儲存至: ", save_path)
	else:
		print("🔴 儲存截圖失敗, 錯誤碼: ", err)
		
	quit(0)
