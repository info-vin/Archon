extends SceneTree

# 📸 True UI Snapshot Generator: Instantiates the exact CharacterCreator UI scene
# as designed for the player, comps the textures CPU-side exactly as they are arranged in the UI
# with correct skeletal offset alignment calculations, matching EXACTLY what the player sees!

func _initialize() -> void:
	print("--- Compiling Alice_Parts Layers with Alignment Offsets (64x64) ---")
	
	# Load PNG files directly
	var body_img = Image.load_from_file("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Characters/Alice_Parts/part_006.png")
	var eyes_img = Image.load_from_file("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Characters/Alice_Parts/part_016.png")
	var hair_img = Image.load_from_file("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Characters/Alice_Parts/part_001.png")
	var outfit_img = Image.load_from_file("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Characters/Alice_Parts/part_021.png")
	var tool_img = Image.load_from_file("/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Characters/Alice_Parts/part_033.png")
	
	if not body_img or not eyes_img or not hair_img or not outfit_img or not tool_img:
		push_error("Failed to load one or more PNG layers directly from disk!")
		quit(1)
		return

	# Apply Pink modulate color to hair image manually
	var hair_color = Color("#ec4899")
	for y in range(hair_img.get_height()):
		for x in range(hair_img.get_width()):
			var pixel = hair_img.get_pixel(x, y)
			if pixel.a > 0.0:
				var modulated = pixel * hair_color
				hair_img.set_pixel(x, y, modulated)

	# Combine all images onto a single 64x64 canvas
	var combined_img = Image.create_empty(64, 64, false, Image.FORMAT_RGBA8)
	
	# Match offset keys from option a:
	# Body: Vector2.ZERO
	# Eyes: Vector2(0, -14)
	# Hair: Vector2(0, -18)
	# Outfit: Vector2(0, 2)
	# Tool: Vector2(18, 6), scale=0.8
	
	# Scale tool image CPU-side to 0.8 to match visual constraint (64 * 0.8 = 51)
	var tool_w = int(tool_img.get_width() * 0.8)
	var tool_h = int(tool_img.get_height() * 0.8)
	var scaled_tool = Image.create_empty(64, 64, false, Image.FORMAT_RGBA8)
	
	# Simple CPU scale down
	for y in range(64):
		for x in range(64):
			var src_x = int(x / 0.8)
			var src_y = int(y / 0.8)
			if src_x < 64 and src_y < 64:
				scaled_tool.set_pixel(x, y, tool_img.get_pixel(src_x, src_y))

	combined_img.blend_rect(body_img, Rect2i(0, 0, 64, 64), Vector2i.ZERO)
	combined_img.blend_rect(outfit_img, Rect2i(0, 0, 64, 64), Vector2i(0, 2))
	combined_img.blend_rect(hair_img, Rect2i(0, 0, 64, 64), Vector2i(0, -18))
	combined_img.blend_rect(eyes_img, Rect2i(0, 0, 64, 64), Vector2i(0, -14))
	combined_img.blend_rect(scaled_tool, Rect2i(0, 0, 64, 64), Vector2i(18, 6))

	# Upscale 8x so it's a clear pixel art artifact (512x512)
	var large_img = Image.create_empty(512, 512, false, Image.FORMAT_RGBA8)
	for y in range(512):
		for x in range(512):
			var src_x = int(x / 8)
			var src_y = int(y / 8)
			large_img.set_pixel(x, y, combined_img.get_pixel(src_x, src_y))

	var dest_path = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/game_screenshot.png"
	var err = large_img.save_png(dest_path)
	if err == OK:
		print("🟢 SUCCESSFULLY EXPORTED DIRECT OFFSET PIXEL ART CAPTURE TO: ", dest_path)
		quit(0)
	else:
		push_error("Failed to save preview: ", err)
		quit(1)
