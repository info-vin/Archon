extends SceneTree

## Phase 5.8.12 Art Asset Optimizer
## Replaces the external Python script with a native Godot tool.
## Scans `res://assets/images/` and applies downscaling and cropping rules based on filename prefixes.

const ASSET_DIR = "res://assets/images/"

enum CropMode {
	NONE,
	SQUARE_CENTER
}

class AssetRule:
	var prefix: String
	var max_size: int
	var crop_mode: int

	func _init(p_prefix: String, p_max: int, p_crop: int) -> void:
		prefix = p_prefix
		max_size = p_max
		crop_mode = p_crop

var rules: Array[AssetRule] = []

func _init() -> void:
	# 類別 1: 背景 (保留比例，最大 1920)
	rules.append(AssetRule.new("bg_", 1920, CropMode.NONE))
	# 類別 2: 底框 (保留比例，最大 1024)
	rules.append(AssetRule.new("card_frame_", 1024, CropMode.NONE))
	# 類別 2 & 3 & 5 & 6: 晶片、行動卡、徽章、預設頭像 (強制正方，最大 512)
	rules.append(AssetRule.new("chip_", 512, CropMode.SQUARE_CENTER))
	rules.append(AssetRule.new("action_", 512, CropMode.SQUARE_CENTER))
	rules.append(AssetRule.new("badge_", 512, CropMode.SQUARE_CENTER))
	rules.append(AssetRule.new("avatar_default", 512, CropMode.SQUARE_CENTER))
	# 類別 7: 團隊頭像、裝備槽 (強制正方，最大 256)
	rules.append(AssetRule.new("avatar_", 256, CropMode.SQUARE_CENTER))
	rules.append(AssetRule.new("icon_", 256, CropMode.SQUARE_CENTER))

	print("=== Starting Asset Optimizer ===")
	
	var dir := DirAccess.open(ASSET_DIR)
	if dir == null:
		printerr("[Fatal Error] Cannot open directory: ", ASSET_DIR, ". Directory may not exist.")
		quit()
		return
	
	dir.list_dir_begin()
	var file_name := dir.get_next()
	var processed_count := 0
	
	while file_name != "":
		if not dir.current_is_dir() and file_name.get_extension() == "png":
			# .import 檔案由引擎自動處理，我們只處理實體 PNG
			_process_file(file_name)
			processed_count += 1
		file_name = dir.get_next()
		
	print("=== Optimization Complete! Processed ", processed_count, " PNGs ===")
	quit()

func _process_file(file_name: String) -> void:
	# 尋找第一條符合的規則 (規則順序影響優先權，例如 avatar_default 必須在 avatar_ 之前)
	var active_rule: AssetRule = null
	for rule in rules:
		if file_name.begins_with(rule.prefix):
			active_rule = rule
			break
			
	if active_rule == null:
		# 沒有匹配到規則的圖檔跳過
		return
		
	var file_path := ASSET_DIR + file_name
	var img := Image.new()
	var err := img.load(file_path)
	
	if err != OK:
		printerr("[Error] Failed to load image: ", file_path, " Error code: ", err)
		return
		
	var original_size := img.get_size()
	var needs_save := false
	
	# 1. 置中裁切 (如果規則要求，且原本不是正方形)
	if active_rule.crop_mode == CropMode.SQUARE_CENTER and original_size.x != original_size.y:
		var new_dim := mini(original_size.x, original_size.y)
		var x_offset := (original_size.x - new_dim) / 2
		var y_offset := (original_size.y - new_dim) / 2
		var rect := Rect2i(x_offset, y_offset, new_dim, new_dim)
		img = img.get_region(rect)
		needs_save = true
		
	# 2. 降階縮放
	var current_size := img.get_size()
	if current_size.x > active_rule.max_size or current_size.y > active_rule.max_size:
		var ratio := minf(float(active_rule.max_size) / float(current_size.x), float(active_rule.max_size) / float(current_size.y))
		var new_w := clampi(int(current_size.x * ratio), 1, active_rule.max_size)
		var new_h := clampi(int(current_size.y * ratio), 1, active_rule.max_size)
		img.resize(new_w, new_h, Image.INTERPOLATE_LANCZOS)
		needs_save = true
		
	# 3. 儲存覆寫
	if needs_save:
		var save_err := img.save_png(file_path)
		if save_err != OK:
			printerr("[Error] Failed to save optimized image: ", file_path, " Error code: ", save_err)
		else:
			print("[Done] Optimized ", file_name, " -> ", img.get_size())
