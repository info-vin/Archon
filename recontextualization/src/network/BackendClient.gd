extends Node

signal request_completed(result: Dictionary)
signal request_failed(error_code: int, message: String)

var _http_request: HTTPRequest
var _max_retries: int = 3
var _current_retries: int = 0
var _current_payload: Dictionary = {}
var _api_url: String = "http://127.0.0.1:8181/rag/hybrid-search"

func _ready():
	_http_request = HTTPRequest.new()
	_http_request.timeout = 5.0 # SLA limit
	add_child(_http_request)
	_http_request.request_completed.connect(_on_http_request_completed)

func search(query: String, similarity_threshold: float = 0.5, match_count: int = 10):
	_current_payload = {
		"query": query,
		"similarity_threshold": similarity_threshold,
		"match_count": match_count
	}
	_current_retries = 0
	_send_request()

func _send_request():
	var json_payload = JSON.stringify(_current_payload)
	var headers = ["Content-Type: application/json"]
	
	# Godot 4 HTTPRequest.request uses error enums
	var error = _http_request.request(_api_url, headers, HTTPClient.METHOD_POST, json_payload)
	if error != OK:
		_handle_failure(error, "Failed to initiate HTTP request.")

func _on_http_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
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

func _handle_failure(code: int, message: String):
	print("BackendClient ERROR: %d - %s" % [code, message])
	request_failed.emit(code, message)
