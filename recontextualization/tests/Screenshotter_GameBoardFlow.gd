extends SceneTree

var output_dir = "/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/"

func _init() -> void:
	call_deferred("run_flow")

func run_flow() -> void:
	print("Capturing GameBoard Flow...")
	TranslationServer.set_locale("zh_TW")
	
	# We need GameState and EventBus for proper testing
	var event_bus = load("res://src/autoloads/EventBus.gd").new()
	var game_state = load("res://src/autoloads/GameState.gd").new()
	var save_manager = load("res://src/autoloads/SaveManager.gd").new()
	root.add_child(event_bus)
	root.add_child(game_state)
	root.add_child(save_manager)
	
	game_state.name = "GameState"
	event_bus.name = "EventBus"
	save_manager.name = "SaveManager"
	
	game_state.start_game()
	
	var board_packed = load("res://src/views/GameBoard.tscn")
	var board = board_packed.instantiate()
	root.add_child(board)
	
	if board is Control:
		board.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		
	board.setup_tutorial(false)
	
	# Step 1: New Player Flow (Level 1)
	board.initialize_career(1, 100.0)
	await process_frame
	await create_timer(1.0).timeout
	var img1 = root.get_texture().get_image()
	if img1: img1.save_png(output_dir + "flow_01_NewPlayer_Level1.png")
	
	# Step 2: Advanced Player Flow (Level 5)
	if board.has_node("TutorialPanel"): board.get_node("TutorialPanel").hide()
	board.initialize_career(5, 100.0)
	await process_frame
	await create_timer(1.0).timeout
	var img2 = root.get_texture().get_image()
	if img2: img2.save_png(output_dir + "flow_02_AdvancedPlayer_Level5.png")
	
	# Step 3: Simulate dropping an Action Card
	var query_input = board.get_node("QueryBar/QueryInput")
	if query_input:
		query_input.text = "How to automate testing?"
		query_input.grab_focus() # Triggers the dynamic Z-Swap
		
	var game_hud = board.get_node("MarginContainer/RootHBox/MainColumn/GameHUD")
	if game_hud and game_hud.has_method("set_mode"):
		game_hud.set_mode("search_active")
		
	var card_script = preload("res://src/models/cards/CardData.gd")
	var action_card = card_script.new()
	action_card.set("type", 1) # ACTION
	action_card.set("id", "action_keyword")
	action_card.set("match_type", 3)
	action_card.set("ap_cost", 1)
	action_card.set("title", "Basic Override")
	action_card.set("art_texture", load("res://assets/images/action_keyword.png"))
	
	game_state.hand_context.add_card(action_card)
	event_bus.request_play_card.emit(action_card)
	
	# Try to render the visual
	if board.has_method("anim_play_card"):
		board.anim_play_card(action_card)
		
	await process_frame
	await create_timer(0.5).timeout
	
	var img3 = root.get_texture().get_image()
	if img3: img3.save_png(output_dir + "flow_03_CardPlayed_Search.png")
	
	print("ALL SCREENSHOTS CAPTURED.")
	quit(0)
