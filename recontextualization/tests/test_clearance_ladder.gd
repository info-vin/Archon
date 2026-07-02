extends SceneTree

func _init():
	print("--- Running Clearance Ladder & Dynamic Difficulty Test ---")
	
	var sm = Node.new()
	sm.name = "SaveManager"
	sm.set_script(preload("res://src/autoloads/SaveManager.gd"))
	root.add_child(sm)
	
	var gs = Node.new()
	gs.name = "GameState"
	gs.set_script(preload("res://src/autoloads/GameState.gd"))
	root.add_child(gs)
	
	# Simulate Sector 1
	print("1. Testing Sector 1 (CR 0)")
	sm.clearance_rating = 0
	gs.start_game()
	print("Poison: ", gs.data_poisoning_ratio, " HP: ", gs.crisis_hp)
	assert(gs.data_poisoning_ratio == 0.0)
	assert(gs.crisis_hp == 10000.0)
	
	# Simulate Sector 2
	print("2. Testing Sector 2 (CR 500)")
	sm.clearance_rating = 500
	gs.start_game()
	print("Poison: ", gs.data_poisoning_ratio, " HP: ", gs.crisis_hp)
	assert(gs.data_poisoning_ratio == 0.2)
	assert(gs.crisis_hp == 15000.0)
	
	# Simulate Sector 3
	print("3. Testing Sector 3 (CR 1000)")
	sm.clearance_rating = 1000
	gs.start_game()
	print("Poison: ", gs.data_poisoning_ratio, " HP: ", gs.crisis_hp)
	assert(gs.data_poisoning_ratio == 0.4)
	assert(gs.crisis_hp == 20000.0)
	
	# Simulate Battle Win
	print("4. Testing Battle Rewards (A Rank)")
	sm.award_battle_loot("A")
	print("New CR: ", sm.clearance_rating)
	assert(sm.clearance_rating == 1030) # 1000 + 30
	assert(sm.current_xp == 50.0)
	
	# Simulate Level Up
	print("5. Testing Level Up via XP")
	sm.cognitive_level = 1
	sm.current_xp = 0.0
	sm.topology_points = 0
	
	# Give 150 XP (Should level up to 2, leave 50 XP)
	sm.award_battle_loot("S") # gives 100
	sm.award_battle_loot("A") # gives 50
	
	print("Level: ", sm.cognitive_level, " TP: ", sm.topology_points, " XP: ", sm.current_xp)
	assert(sm.cognitive_level == 2)
	assert(sm.topology_points == 1)
	assert(sm.current_xp == 50.0)
	
	print("✅ Clearance Ladder Test Passed!")
	quit()
