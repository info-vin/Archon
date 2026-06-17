extends SceneTree

var root_node
var state = 0

func _init():
	var main_scene = load("res://Scenes/Main/Main.tscn")
	if not main_scene:
		print("Error: Could not load Main.tscn")
		quit(1)
		return
		
	root_node = main_scene.instantiate()
	root.add_child(root_node)
	
	process_frame.connect(_on_frame)

var frames = 0
func _on_frame():
	frames += 1
	
	if frames == 5:
		root_node.tycoon_manager.funds = 1000
		
	if frames == 10:
		print("--- Step 1: Clicking Recruit Button ---")
		root_node._on_recruit_btn_pressed()
	
	# Wait for popup animation (0.3s)
	if frames == 40:
		print("--- Step 2: Capturing Popup State ---")
		var img = root.get_viewport().get_texture().get_image()
		img.save_png("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/flow_1_popup.png")
		
		# Find the CharacterCreator instance and click recruit
		for child in root_node.get_children():
			if child.name == "CharacterCreator":
				print("--- Step 3: Confirming Recruitment ---")
				child._on_recruit_pressed()
				break
				
	if frames == 50:
		print("--- Step 4: Capturing Final State ---")
		var img = root.get_viewport().get_texture().get_image()
		img.save_png("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/flow_2_result.png")
		print("🟢 UI FLOW TEST COMPLETED SUCCESSFULLY!")
		quit(0)
