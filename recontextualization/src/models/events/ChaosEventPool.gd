extends Node

class_name ChaosEventPool

const EVENTS_DATA_PATH = "res://assets/data/chaos_events.json"
static var _events_cache: Array = []

static func _load_events() -> void:
    if _events_cache.size() > 0:
        return
        
    if FileAccess.file_exists(EVENTS_DATA_PATH):
        var file = FileAccess.open(EVENTS_DATA_PATH, FileAccess.READ)
        if file:
            var json_string = file.get_as_text()
            file.close()
            var json = JSON.new()
            if json.parse(json_string) == OK and typeof(json.data) == TYPE_ARRAY:
                _events_cache = json.data
                return
    
    # Fallback to prevent crash if JSON is missing, but should ideally be flagged
    push_error("Failed to load chaos events from " + EVENTS_DATA_PATH)
    _events_cache = [{"id": "fallback", "title": "Unknown Error", "description": "Error loading events.", "effect_type": "none", "duration": 0.0, "dialogue": "..."}]

static func get_random_event() -> Dictionary:
    _load_events()
    var e = _events_cache[randi() % _events_cache.size()]
    return e

static func get_event(event_id: String) -> Dictionary:
    _load_events()
    for e in _events_cache:
        if e.get("id") == event_id:
            return e
    return _events_cache[0]
