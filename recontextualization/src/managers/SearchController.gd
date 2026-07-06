class_name SearchController
extends Node

signal search_triggered(match_type: int)

var game_state: Node
var backend_client: Node

func _ready() -> void:
	game_state = get_parent()
	backend_client = BackendClient.new()
	add_child(backend_client)
	backend_client.request_completed.connect(_on_search_completed)
	backend_client.request_failed.connect(_on_search_failed)

func trigger_search(match_type: int, query_text: String = "default query") -> void:
	if not game_state.is_game_active:
		return
	if game_state.current_ap >= GameBalanceConfig.SEARCH_AP_COST:
		game_state.current_ap -= GameBalanceConfig.SEARCH_AP_COST
		game_state.ap_changed.emit(game_state.current_ap)
		search_triggered.emit(match_type)
		backend_client.search(query_text, GameBalanceConfig.SEARCH_SIMILARITY_THRESHOLD, GameBalanceConfig.SEARCH_TOP_K)
	else:
		print("Not enough AP to search!")

func _on_search_completed(response: Dictionary) -> void:
	if not response.has("results"):
		return
	var results = response.get("results")
	for chunk in results:
		var card = CardData.new()
		card.type = CardData.CardType.DATA_CHIP
		card.similarity = chunk.get("similarity", 0.0)
		card.title = chunk.get("content", "Data Chunk").left(20) + "..."
		
		var mt = chunk.get("match_type", "keyword")
		if mt == "keyword":
			card.match_type = CardData.MatchType.KEYWORD
		elif mt == "vector":
			card.match_type = CardData.MatchType.VECTOR
		else:
			card.match_type = CardData.MatchType.HYBRID
			
		_apply_data_poisoning(card)
		game_state.hand_context.add_card(card)

func _on_search_failed(error_code: int, message: String) -> void:
	print("Search failed (Code: %d, Message: %s). Activating Standalone Fallback!" % [error_code, message])
	var mock_cards = MockDataGenerator.generate_mock_rag_chunks()
	for card in mock_cards:
		_apply_data_poisoning(card)
		game_state.hand_context.add_card(card)

func _apply_data_poisoning(card: Resource) -> void:
	if randf() < game_state.data_poisoning_ratio:
		var type_val = card.get("type") if card.get("type") != null else CardData.CardType.ACTION
		if type_val == CardData.CardType.DATA_CHIP:
			card.set("type", CardData.CardType.NOISE_CHIP)
			var current_title = card.get("title")
			if current_title != null and not current_title.begins_with("[CORRUPTED]"):
				card.set("title", "[CORRUPTED] " + current_title)
