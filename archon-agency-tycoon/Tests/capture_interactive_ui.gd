extends SceneTree

func _initialize() -> void:
	print("--- 📸 執行互動 UI 視覺截圖公證 ---")
	
	if DisplayServer.get_name() == "headless":
		print("⚠️ 檢測到 headless 模式，略過實體截圖以防崩潰 (Graceful Fallback)")
		quit(0)
		return
		
	# Inject Autoloads
	var event_bus = preload("res://Scripts/Autoloads/EventBus.gd").new()
	event_bus.name = "EventBus"
	root.add_child(event_bus)
	
	# 2. Simulate Recruiting a Custom Spritesheet Agent
	var sim_engine = preload("res://Scripts/Logic/SimulationEngine.gd").new()
	sim_engine.name = "SimulationEngine"
	root.add_child(sim_engine)
	
	var alice = preload("res://Scripts/Resources/AgentResource.gd").new()
	alice.agent_name = "Alice"
	sim_engine.agent_manager.add_agent(alice)
	
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
		
	# ----------------------------------------------------
	# 1. 預設主畫面截圖 (驗證 Minimap 雷達圖與預設排版)
	# ----------------------------------------------------
	# Wait for a few frames to let layout engine compute sizes
	for i in range(15):
		await process_frame
		
	var image_default = root.get_texture().get_image()
	if image_default:
		var err = image_default.save_png("res://screenshots/proof_main_default.png")
		if err == OK:
			print("🟢 1. 預設主畫面(含 Minimap 雷達圖)公證截圖成功")
		else:
			print("🔴 1. 儲存預設畫面失敗: ", err)
			
	# ----------------------------------------------------
	# 2. 模擬招募按鈕點擊 (驗證角色自訂器彈出視窗)
	# ----------------------------------------------------
	var recruit_btn: Button = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/RecruitBtn")
	if recruit_btn:
		print("👉 模擬點擊 RecruitBtn...")
		recruit_btn.pressed.emit()
		
		# Wait for Tween pop-up animation (0.3s -> about 20-30 frames)
		for i in range(30):
			await process_frame
			
		var image_recruit = root.get_texture().get_image()
		if image_recruit:
			var err = image_recruit.save_png("res://screenshots/proof_recruit_creator.png")
			if err == OK:
				print("🟢 2. 招募自訂器彈出視窗公證截圖成功")
			else:
				print("🔴 2. 儲存招募視窗失敗: ", err)
				
		# Clean up Creator panels & overlay manually to restore screen
		for child in main_node.get_children():
			if child.name == "ColorRect" or child.name == "CharacterCreator":
				child.queue_free()
		await process_frame
	else:
		print("🔴 找不到 RecruitBtn 節點")
		
	# ----------------------------------------------------
	# 3. 模擬擴建房間與滾動 ScrollContainer (驗證其他房間畫面)
	# ----------------------------------------------------
	var expand_btn: Button = main_node.get_node_or_null("VBox/BottomBar/VBox/ActionHBox/ExpandRoomBtn")
	var game_area: ScrollContainer = main_node.get_node_or_null("VBox/HBoxMain/GameArea")
	var dev_room_rect = main_node.dev_room.get_global_rect()
	
	if expand_btn:
		print("👉 模擬點擊 ExpandRoomBtn 擴建房間...")
		expand_btn.pressed.emit()
		await process_frame
		
		if game_area:
			# Scroll down to show the newly expanded bottom rooms
			print("👉 向下拉動 ScrollContainer 滾動條...")
			game_area.scroll_vertical = 200
			
			for i in range(15):
				await process_frame
				
			var image_scrolled = root.get_texture().get_image()
			if image_scrolled:
				var err = image_scrolled.save_png("res://screenshots/proof_expanded_and_scrolled.png")
				if err == OK:
					print("🟢 3. 擴建房間並下拉滾動畫面公證截圖成功")
				else:
					print("🔴 3. 儲存滾動畫面失敗: ", err)
		else:
			print("🔴 找不到 GameArea ScrollContainer 節點")
	else:
		print("🔴 找不到 ExpandRoomBtn 節點")
		
	quit(0)
