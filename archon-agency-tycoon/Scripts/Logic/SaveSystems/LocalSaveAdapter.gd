extends SaveAdapter
class_name LocalSaveAdapter

var save_path: String

func _init(path: String = "user://savegame.json"):
    save_path = path

func save_data(data: Dictionary) -> bool:
    var file = FileAccess.open(save_path, FileAccess.WRITE)
    if file == null:
        push_error("Failed to open file for writing at %s" % save_path)
        return false
        
    var json_string = JSON.stringify(data)
    file.store_string(json_string)
    file.close()
    return true

func load_data() -> Dictionary:
    if not FileAccess.file_exists(save_path):
        return {} # Return empty dictionary if no save exists
        
    var file = FileAccess.open(save_path, FileAccess.READ)
    if file == null:
        push_error("Failed to open file for reading at %s" % save_path)
        return {}
        
    var json_string = file.get_as_text()
    file.close()
    
    var json = JSON.new()
    var error = json.parse(json_string)
    if error == OK:
        if typeof(json.data) == TYPE_DICTIONARY:
            return json.data as Dictionary
        else:
            push_error("Saved data is not a dictionary.")
            return {}
    else:
        push_error("JSON Parse Error: %s at line %d" % [json.get_error_message(), json.get_error_line()])
        return {}
