extends SceneTree

func _init():
	print("--- Running Topology Talent Modifiers Test ---")
	
	# Mock SaveManager
	var sm = Node.new()
	sm.name = "SaveManager"
	sm.set_script(preload("res://src/autoloads/SaveManager.gd"))
	root.add_child(sm)
	
	var card = preload("res://src/models/cards/CardData.gd").new()
	card.level = 1
	card.id = "keyword_search"
	
	print("1. Baseline Parameters:")
	var params = card.get_rag_parameters(sm.unlocked_talents)
	print(params)
	assert(params["match_count"] == 1)
	assert(params["min_score"] == 0.0)
	assert(params["use_hybrid"] == false)
	
	print("2. Equipping 'wide_net' talent:")
	sm.unlocked_talents.append("wide_net")
	params = card.get_rag_parameters(sm.unlocked_talents)
	print(params)
	assert(params["match_count"] == 4, "Wide net should add 3 to match_count")
	
	print("3. Equipping 'strict_purity' talent:")
	sm.unlocked_talents.append("strict_purity")
	params = card.get_rag_parameters(sm.unlocked_talents)
	print(params)
	assert(params["min_score"] == 0.1, "Strict purity should add 0.1 to min_score")
	
	print("4. Equipping 'hybrid_mastery' at Lv.3:")
	sm.unlocked_talents.append("hybrid_mastery")
	card.level = 3
	params = card.get_rag_parameters(sm.unlocked_talents)
	print(params)
	assert(params["use_hybrid"] == true, "Hybrid mastery should unlock hybrid at Lv.3")
	
	print("✅ Talent Modifiers Test Passed!")
	quit()
