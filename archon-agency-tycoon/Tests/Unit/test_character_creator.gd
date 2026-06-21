extends MiniTest

func test_character_creation_and_customization() -> void:
	var scene = load("res://Scenes/UI/CharacterCreator.tscn")
	assert_not_null(scene, "CharacterCreator scene should be loadable")
	
	var creator = scene.instantiate()
	assert_not_null(creator, "CharacterCreator should be instantiable")
	
	# 2. Connect character_created signal immediately before ready/frames
	var box = []
	creator.character_created.connect(func(agent_data):
		box.append(agent_data)
	)
	
	var root = tree.root
	root.add_child(creator)
	
	await tree.process_frame
	
	# Toggle spritesheet mode off for Classic creator tests
	creator._on_mode_toggle_pressed()
	
	# 1. Modify paperdoll variables inside the creator
	creator.gender = 1 # Male base skeleton
	creator.hair_style = 2 # Short Hair style
	creator.hair_hue = 180.0 # Cyan/Blue hair modulation
	creator.outfit_style = 2 # Formal vest
	creator.tool_style = 2 # Cards tool
	
	creator.character_name = "Bob the Wizard"
	
	# Update preview texture configurations
	creator._update_preview()
	
	assert_eq(creator.agent_view.body_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_010.png", "Should preview male base skeleton")
	assert_eq(creator.agent_view.hair_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_015.png", "Should preview short hair style")
	assert_eq(creator.agent_view.hair_sprite.modulate.h, 0.5, "Modulated color hue should match 180.0 degrees (0.5 normalized)")
	assert_eq(creator.agent_view.outfit_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_020.png", "Should preview formal vest")
	assert_eq(creator.agent_view.tool_sprite.texture.resource_path, "res://Assets/Characters/Alice_Parts/part_031.png", "Should preview cards tool")
	
	
	creator._on_recruit_pressed()
	
	assert_eq(box.size(), 1, "Should have emitted exactly one recruited agent resource")
	var recruited_agent = box[0]
	assert_not_null(recruited_agent, "Recruited agent resource should be emitted synchronously")
	assert_eq(recruited_agent.agent_name, "Bob the Wizard", "Name should carry over")
	assert_eq(recruited_agent.gender, 1, "Male skeleton flag should carry over")
	assert_eq(recruited_agent.hair_style, 2, "Hair style should carry over")
	assert_eq(recruited_agent.outfit_style, 2, "Outfit style should carry over")
	assert_eq(recruited_agent.tool_style, 2, "Tool style should carry over")
	assert_eq(recruited_agent.hair_color.h, 0.5, "Hair modulation color hue should match")
	
