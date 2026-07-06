extends Node

signal request_completed(result: Dictionary)
signal request_failed(error_code: int, message: String)

@export var api_url: String = "http://127.0.0.1:8181/api/rag/hybrid-search"
@export var tutorial_dataset_path: String = "res://assets/data/tutorial_dataset.json"

var _http_request: HTTPRequest
var _max_retries: int = 3
var _current_retries: int = 0
var _current_payload: Dictionary = {}
var auth_token: String = ""
var _is_web: bool = false

func _ready() -> void:
	if OS.has_feature("web"):
		_is_web = true
		if JavaScriptBridge.get_interface("window"):
			var origin = JavaScriptBridge.eval("window.location.origin")
			if origin:
				api_url = str(origin) + "/api/rag/hybrid-search"
			else:
				api_url = "/api/rag/hybrid-search"
				
	_http_request = HTTPRequest.new()
	_http_request.timeout = 5.0 # SLA limit
	add_child(_http_request)
	_http_request.request_completed.connect(_on_http_request_completed)

func search(query: String, similarity_threshold: float = 0.5, match_count: int = 10) -> void:
	var game_state: Node = (Engine.get_singleton("GameState") if Engine.has_singleton("GameState") else get_node_or_null("/root/GameState"))
	if game_state != null and game_state.is_tutorial_active:
		var file = FileAccess.open(tutorial_dataset_path, FileAccess.READ)
		if file:
			var text = file.get_as_text()
			var json = JSON.new()
			if json.parse(text) == OK:
				var data = json.data
				if typeof(data) == TYPE_ARRAY:
					# Mock random selection from array
					data.shuffle()
					var results = data.slice(0, min(match_count, data.size()))
					call_deferred("emit_signal", "request_completed", {"results": results})
					return
		
		# Fallback if json fails
		call_deferred("emit_signal", "request_failed", 404, "Tutorial dataset missing")
		return

	var eq_model = ""
	var env_config = _safe_get_node("EnvConfig")
	if env_config:
		eq_model = env_config.default_model
		
	var al_react = false
	
	var save_manager = _safe_get_node("SaveManager")
	if save_manager and save_manager.teammates.size() > 0:
		# Use the first selected teammate for now or active logic
		var active_t = save_manager.teammates[0]
		if active_t.get("equipped_model") != null and active_t.get("equipped_model") != "":
			eq_model = active_t.get("equipped_model")
		al_react = active_t.get("allow_react", al_react)

	_current_payload = {
		"query": query,
		"similarity_threshold": similarity_threshold,
		"match_count": match_count,
		"equipped_model": eq_model,
		"allow_react": al_react
	}
	_current_retries = 0
	_send_request()

func _send_request() -> void:
	var json_payload = JSON.stringify(_current_payload)
	var headers = ["Content-Type: application/json"]
	if auth_token != "":
		headers.append("Authorization: Bearer " + auth_token)	
	# Godot 4 HTTPRequest.request uses error enums
	var error = _http_request.request(api_url, headers, HTTPClient.METHOD_POST, json_payload)
	if error != OK:
		_handle_failure(error, "Failed to initiate HTTP request.")

func _on_http_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or response_code >= 400:
		if _current_retries < _max_retries:
			_current_retries += 1
			print("BackendClient: Request failed (Result: %d, Code: %d). Retrying %d/%d..." % [result, response_code, _current_retries, _max_retries])
			# Need a slight delay before retry. 
			await get_tree().create_timer(1.0).timeout
			_send_request()
		else:
			var error_msg = "Request failed after max retries."
			if body.size() > 0:
				error_msg += " Body: " + body.get_string_from_utf8()
			_handle_failure(response_code, error_msg)
		return
	
	var json = JSON.new()
	var err = json.parse(body.get_string_from_utf8())
	if err == OK:
		var response_data = json.get_data()
		request_completed.emit(response_data)
	else:
		_handle_failure(err, "Failed to parse JSON response.")

func _handle_failure(code: int, message: String) -> void:
	print("BackendClient ERROR: %d - %s" % [code, message])
	request_failed.emit(code, message)

func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null
