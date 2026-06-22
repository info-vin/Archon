extends SceneTree

func _initialize() -> void:
	print("--- 📸 執行 Spritesheet UI 視覺截圖公證 ---")
	
	if DisplayServer.get_name() == "headless":
		print("⚠️ 檢測到 headless 模式，略過實體截圖以防崩潰 (Graceful Fallback)")
		quit(0)
		return
		
	# Inject Autoloads
	var event_bus = preload("res://Scripts/Autoloads/EventBus.gd").new()
	event_bus.name = "EventBus"
	root.add_child(event_bus)
	
	var sim_engine = preload("res://Scripts/Logic/SimulationEngine.gd").new()
	sim_engine.name = "SimulationEngine"
	root.add_child(sim_engine)
	
	# Load and instance the Main scene
	var scene = load("res://Scenes/Main/Main.tscn")
	if not scene:
		print("🔴 無法載入主場景 Main.tscn")
		quit(1)
		return
		
	var main_node = scene.instantiate()
	root.add_child(main_node)
	
	# 確保 screenshots 資料夾存在
	var dir = DirAccess.open("res://")
	if not dir.dir_exists("screenshots"):
		dir.make_dir("screenshots")
		
	# Wait for a few frames to let layout engine compute sizes
	for i in range(15):
		await process_frame
		
	# 2. Add some test agent data using SimulationEngine
	var s_engine = root.get_node("SimulationEngine")
	s_engine.tycoon_manager.funds = 10000
	print("💰 已注入資金: 10000")
		
	# 1. Open Character Creator
	print("👉 直接呼叫 _on_recruit_btn_pressed() 開啟自訂器...")
	main_node._on_recruit_btn_pressed()
	
	# Wait for Tween pop-up animation
	for i in range(30):
		await process_frame
		
	print("Main children after direct call:")
	for child in main_node.get_children():
		print(" - ", child.name, " (", child.get_class(), ")")
		
	var creator = main_node.get_node_or_null("CharacterCreator")
	if not creator:
		print("🔴 找不到 CharacterCreator 節點")
		quit(1)
		return
		
	# AI Spritesheet Mode is now default. We wait for layout to settle.
	for i in range(10):
		await process_frame
		
	# Save the initial empty Spritesheet UI state screenshot
	var image_initial = root.get_texture().get_image()
	if image_initial:
		var save_path = "res://screenshots/proof_spritesheet_ui_initial.png"
		var err = image_initial.save_png(save_path)
		if err == OK:
			print("🟢 1. 初始 AI Spritesheet UI 狀態截圖成功: ", save_path)
		else:
			print("🔴 1. 儲存初始截圖失敗: ", err)
			
	# 3. Partially fill slots (e.g. Slot 1 and Slot 2)
	print("👉 模擬點擊 Slot 1 (Box Art) 並選擇路徑...")
	creator._on_browse_pressed_for_step(0)
	creator._on_file_selected("res://Assets/Characters/char_sheet_v2.png")
	
	print("👉 模擬點擊 Slot 2 (South) 並選擇路徑...")
	creator._on_browse_pressed_for_step(1)
	creator._on_file_selected("res://Assets/Characters/char_sheet_v2.png")
	
	# Select Step 3 to display its status
	creator._on_browse_pressed_for_step(2)
	
	for i in range(10):
		await process_frame
		
	# Save the partially filled Spritesheet UI state screenshot
	var image_partial = root.get_texture().get_image()
	if image_partial:
		var save_path = "res://screenshots/proof_spritesheet_ui_partially_filled.png"
		var err = image_partial.save_png(save_path)
		if err == OK:
			print("🟢 2. 部分填滿且解鎖後續之 AI Spritesheet UI 狀態截圖成功: ", save_path)
		else:
			print("🔴 2. 儲存部分填滿截圖失敗: ", err)
			
	# Clean up
	quit(0)
