extends Node

const ENV_PATH = "res://env.json"

var models: Array = []
var default_model: String = ""

func _ready() -> void:
    _load_env()

func _load_env() -> void:
    var loaded_from_json = false
    if FileAccess.file_exists(ENV_PATH):
        var file = FileAccess.open(ENV_PATH, FileAccess.READ)
        if file:
            var json_string = file.get_as_text()
            file.close()
            
            var json = JSON.new()
            if json.parse(json_string) == OK:
                var data = json.data
                if typeof(data) == TYPE_DICTIONARY:
                    models = data.get("models", [])
                    default_model = data.get("default_model", "")
                    if default_model != "":
                        loaded_from_json = true

    if not loaded_from_json:
        # Fallback to Environment Variables (SSOT)
        var env_model = OS.get_environment("DEFAULT_MODEL")
        if env_model != "":
            default_model = env_model
            models = [{"id": env_model, "display_name": env_model + " (Env)", "ap_cost": 1}]
        else:
            # Fail-Fast! No hardcoded fallbacks allowed.
            push_error("CRITICAL ERROR: No model configuration found in env.json or DEFAULT_MODEL env var. FAILING FAST.")
            assert(false, "Model Configuration Missing - SSOT Violation")

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
