extends SceneTree

const ASSET_DIR = "res://assets/images/"
const RESOURCE_DIR = "res://src/models/cards/resources/"

func _init() -> void:
	print("=== Starting Card Resource Generator ===")
	
	var dir := DirAccess.open(ASSET_DIR)
	if dir == null:
		printerr("[Fatal Error] Cannot open directory: ", ASSET_DIR)
		quit()
		return
		
	dir.list_dir_begin()
	var file_name := dir.get_next()
	var created_count := 0
	
	var CardDataScript = load("res://src/models/cards/CardData.gd")
	if not CardDataScript:
		printerr("[Error] Could not load CardData.gd")
		quit()
		return
	
	while file_name != "":
		if not dir.current_is_dir() and file_name.get_extension() == "png":
			if file_name.begins_with("action_") or file_name.begins_with("chip_"):
				var base_id = file_name.get_basename()
				var tres_path = RESOURCE_DIR + base_id + ".tres"
				
				# Only create if the resource doesn't already exist
				if not FileAccess.file_exists(tres_path):
					var card = CardDataScript.new()
					card.id = base_id
					
					# Convert "action_xray" to "Action Xray"
					var words = base_id.split("_")
					var formatted_title = ""
					for word in words:
						formatted_title += word.capitalize() + " "
					card.title = formatted_title.strip_edges()
					
					# Load the compressed texture
					card.icon = load(ASSET_DIR + file_name)
					
					# Assign proper enum based on prefix
					if base_id.begins_with("action_"):
						card.type = 1 # CardData.CardType.ACTION
					elif base_id == "chip_red_noise":
						card.type = 3 # CardData.CardType.NOISE_CHIP
					elif base_id.begins_with("chip_"):
						card.type = 2 # CardData.CardType.DATA_CHIP
						
					var err = ResourceSaver.save(card, tres_path)
					if err == OK:
						print("[Created] ", tres_path)
						created_count += 1
					else:
						printerr("[Error] Failed to save ", tres_path)
		file_name = dir.get_next()
		
	print("=== Generation Complete! Created ", created_count, " new .tres files ===")
	quit()
