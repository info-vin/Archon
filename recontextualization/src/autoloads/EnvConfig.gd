extends Node

const ENV_PATH = "res://env.json"

var models: Array = []
var default_model: String = "gemini-1.5-flash"

func _ready() -> void:
    _load_env()

func _load_env() -> void:
    if not FileAccess.file_exists(ENV_PATH):
        print("EnvConfig: env.json not found, using fallback defaults.")
        _setup_fallbacks()
        return
        
    var file = FileAccess.open(ENV_PATH, FileAccess.READ)
    if not file:
        _setup_fallbacks()
        return
        
    var json_string = file.get_as_text()
    file.close()
    
    var json = JSON.new()
    var error = json.parse(json_string)
    if error == OK:
        var data = json.data
        if typeof(data) == TYPE_DICTIONARY:
            models = data.get("models", [])
            default_model = data.get("default_model", "gemini-1.5-flash")
            return
            
    _setup_fallbacks()

func _setup_fallbacks() -> void:
    models = [
        {"id": "gemini-1.5-flash", "display_name": "Gemini Flash (Fallback)", "ap_cost": 1},
        {"id": "gemini-1.5-pro", "display_name": "Gemini Pro (Fallback)", "ap_cost": 3}
    ]
    default_model = "gemini-1.5-flash"

func get_model_display_name(model_id: String) -> String:
    for m in models:
        if m.get("id") == model_id:
            return m.get("display_name", model_id)
    return model_id

func get_model_id_by_index(idx: int) -> String:
    if idx >= 0 and idx < models.size():
        return models[idx].get("id", default_model)
    return default_model

func get_model_index_by_id(model_id: String) -> int:
    for i in range(models.size()):
        if models[i].get("id") == model_id:
            return i
    return 0
