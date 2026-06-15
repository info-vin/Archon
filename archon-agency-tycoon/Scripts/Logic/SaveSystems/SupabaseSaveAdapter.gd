extends SaveAdapter
class_name SupabaseSaveAdapter

# Cloud Save Adapter for Supabase syncing via FastAPI backend

const BASE_API_URL = "http://localhost:8181/api/game" # Default local, can be overridden by Web environment

func get_auth_token() -> String:
	if OS.has_feature("web"):
		var token = JavaScriptBridge.eval("window.getArchonToken ? window.getArchonToken() : ''")
		if token:
			return str(token)
	return ""

func save_data(data: Dictionary) -> bool:
	var token = get_auth_token()
	if token.is_empty():
		push_warning("No authentication token found. Falling back to local save.")
		return false
		
	var http = HTTPRequest.new()
	var root = Engine.get_main_loop().root
	root.add_child(http)
	
	var url = BASE_API_URL + "/save"
	# If on web, use current host as base URL
	if OS.has_feature("web"):
		var host = str(JavaScriptBridge.eval("window.location.origin"))
		url = host + "/api/game/save"
		
	var headers = [
		"Content-Type: application/json",
		"Authorization: Bearer " + token
	]
	
	var payload = JSON.stringify({"save_data": data})
	
	http.request(url, headers, HTTPClient.METHOD_POST, payload)
	var result = await http.request_completed
	http.queue_free()
	
	var response_code = result[1]
	if response_code == 200:
		return true
	else:
		push_error("Cloud save failed with response code: %d" % response_code)
		return false

func load_data() -> Dictionary:
	var token = get_auth_token()
	if token.is_empty():
		push_warning("No authentication token found. Cannot load from cloud.")
		return {}
		
	var http = HTTPRequest.new()
	var root = Engine.get_main_loop().root
	root.add_child(http)
	
	var url = BASE_API_URL + "/load"
	if OS.has_feature("web"):
		var host = str(JavaScriptBridge.eval("window.location.origin"))
		url = host + "/api/game/load"
		
	var headers = [
		"Authorization: Bearer " + token
	]
	
	http.request(url, headers, HTTPClient.METHOD_GET)
	var result = await http.request_completed
	http.queue_free()
	
	var response_code = result[1]
	var body = result[3].get_string_from_utf8()
	
	if response_code == 200:
		var json = JSON.new()
		if json.parse(body) == OK:
			var res_dict = json.data as Dictionary
			if res_dict.get("status") == "success" and res_dict.has("save_data") and res_dict["save_data"] != null:
				return res_dict["save_data"] as Dictionary
		return {}
	else:
		push_error("Cloud load failed with response code: %d" % response_code)
		return {}
