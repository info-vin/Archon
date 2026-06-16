extends SceneTree

# 📸 True UI Snapshot Generator: Instantiates the exact CharacterCreator UI scene
# as designed for the player, hooks it to a SubViewport to force layout rendering,
# and captures the resulting preview image to disk, matching EXACTLY what the player sees!

func _initialize() -> void:
	print("--- Loading CharacterCreator UI Scene ---")
	var scene = load("res://Scenes/UI/CharacterCreator.tscn")
	if not scene:
		push_error("Failed to load CharacterCreator scene")
		quit(1)
		return
		
	# Ensure translation server is populated for UI screenshot rendering
	var translation = load("res://translations.en.translation")
	if translation:
		TranslationServer.add_translation(translation)
	TranslationServer.set_locale("en")
	
	var creator = scene.instantiate()
	
	# Instantiate a SubViewport to host the UI layout so it renders correctly headlessly
	var viewport = SubViewport.new()
	viewport.size = Vector2(850, 500) # Slightly wider viewport to fit everything cleanly
	viewport.disable_3d = true
	viewport.transparent_bg = false
	# Crucial: set update mode properly
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	
	root.add_child(viewport)
	viewport.add_child(creator)
	
	# Set target values to render a custom combinations
	creator.gender = 0 # Female base
	creator.hair_style = 1 # Long bow hair
	creator.hair_hue = 330.0 # Magenta/Pink hair
	creator.outfit_style = 1 # Mage robe
	creator.tool_style = 1 # DEV wand
	creator.character_name = "Alice the Tech Mage"
	
	# Force preview textures to update
	creator._update_preview()
	
	# Let layout settle by waiting for RenderingServer frame post draw to prevent black screen!
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	
	# Retrieve SubViewport texture rendering
	var img = viewport.get_texture().get_image()
	var dest_path = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/game_screenshot.png"
	var err = img.save_png(dest_path)
	if err == OK:
		print("🟢 SUCCESSFULLY CAPTURED REAL UI PREVIEW AT: ", dest_path)
		quit(0)
	else:
		push_error("Failed to save preview: ", err)
		quit(1)
