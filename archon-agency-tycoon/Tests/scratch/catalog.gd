extends SceneTree

func _init():
	var atlas = Image.create_empty(64 * 6, 64 * 6, false, Image.FORMAT_RGBA8)
	var index = 0
	
	for y in range(6):
		for x in range(6):
			if index > 33:
				break
				
			var filename = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Characters/Alice_Parts/part_%03d.png" % index
			var img = Image.load_from_file(filename)
			if img:
				atlas.blend_rect(img, Rect2i(0, 0, 64, 64), Vector2i(x * 64, y * 64))
			
			index += 1
			
	var dest_path = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/parts_catalog.png"
	atlas.save_png(dest_path)
	print("🟢 CATALOG EXPORTED TO: ", dest_path)
	quit(0)
