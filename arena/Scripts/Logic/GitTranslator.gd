extends RefCounted
class_name GitTranslator

var dictionary: Dictionary = {}

func _init():
	load_dictionary()

func load_dictionary() -> void:
	var file_path = "res://Scripts/Resources/git_dict.json"
	if FileAccess.file_exists(file_path):
		var file = FileAccess.open(file_path, FileAccess.READ)
		if file:
			var content = file.get_as_text()
			file.close()
			var parsed = JSON.parse_string(content)
			if parsed is Dictionary:
				dictionary = parsed
				return
				
	# Fallback if file load/parse fails
	dictionary = {
		"feat": "新增功能",
		"fix": "修復錯誤",
		"docs": "更新文件",
		"refactor": "重構程式碼",
		"perf": "優化效能",
		"test": "新增測試",
		"style": "調整樣式",
		"chore": "例行工作",
		"merge": "分支合併"
	}

func translate_message(msg: String) -> String:
	var translated = msg
	var keys = dictionary.keys()
	# Sort keys by length descending to match longer phrases first
	keys.sort_custom(func(a, b): return a.length() > b.length())
	
	for key in keys:
		var val = dictionary[key]
		translated = translated.replacen(key, val)
	return translated
