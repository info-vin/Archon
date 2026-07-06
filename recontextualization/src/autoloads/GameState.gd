extends Node

signal ap_changed(new_ap: int)
signal hp_changed(new_hp: float)
signal player_hp_changed(new_hp: float)
signal player_died()
signal context_updated(purity: float)
signal game_over(is_victory: bool, rank: String)
signal sla_changed(new_sla: float)
signal poisoning_updated(ratio: float)
signal rate_limit_updated(compression: float)
signal search_triggered(match_type: int)
signal context_purified(remaining_card_instances: Array)
signal chaos_event_triggered(event_id: String)

var current_ap: int = 10
var crisis_hp: float = 10000.0
var max_crisis_hp: float = 10000.0

var player_hp: float = 100.0
var max_player_hp: float = 100.0

var sla_timer: float = GameBalanceConfig.MAX_SLA_TIME
var max_sla: float = GameBalanceConfig.MAX_SLA_TIME
var is_game_active: bool = false
var is_tutorial_active: bool = false
var rate_limit_compression: float = 1.0
var data_poisoning_ratio: float = 0.0
var base_poisoning_ratio: float = 0.0
var delivery_count: int = 0
var agent_planning_state: String = "idle"
var combo_multiplier: float = 1.0

var active_context = preload("res://src/models/DeckData.gd").new()
var hand_context = preload("res://src/models/HandData.gd").new()
var CardEffectResolver = preload("res://src/models/cards/CardEffectResolver.gd")
var backend_client_script = preload("res://src/network/BackendClient.gd")
var backend_client: Node
var t_mgr_scene = preload("res://src/managers/tutorial/TutorialManager.gd")
var CardData = preload("res://src/models/cards/CardData.gd")

func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null

func _ready() -> void:
	backend_client = backend_client_script.new()
	add_child(backend_client)
	backend_client.request_completed.connect(_on_search_completed)
	backend_client.request_failed.connect(_on_search_failed)
	
	hand_context.card_added.connect(func(card):
		var event_bus = _safe_get_node("EventBus")
		if event_bus != null and event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.emit(card)
	)

	var event_bus = _safe_get_node("EventBus")
	if event_bus != null:
		if event_bus.has_signal("request_play_card"):
			event_bus.request_play_card.connect(_on_request_play_card)

func _process(delta: float) -> void:
	if is_game_active and not is_tutorial_active and sla_timer > 0.0:
		sla_timer -= delta
		sla_changed.emit(sla_timer)
		
		var elapsed = max_sla - sla_timer
		var target_poison = min(GameBalanceConfig.MAX_POISON_RATIO_LIMIT, base_poisoning_ratio + (elapsed / max_sla * GameBalanceConfig.POISON_TIME_SCALE))
		if abs(target_poison - data_poisoning_ratio) > 0.01:
			data_poisoning_ratio = target_poison
			poisoning_updated.emit(data_poisoning_ratio)
			
		if sla_timer <= 0.0:
			sla_timer = 0.0
			is_game_active = false
			game_over.emit(false, "")

func start_game() -> void:
	_reset_stats()
	_setup_tutorial()
	_setup_difficulty()
	_emit_initial_signals()
	_draw_starting_hand()

func _reset_stats() -> void:
	is_game_active = true
	sla_timer = max_sla
	player_hp = max_player_hp
	crisis_hp = max_crisis_hp
	rate_limit_compression = 1.0
	data_poisoning_ratio = 0.0
	delivery_count = 0
	agent_planning_state = "idle"
	combo_multiplier = 1.0
	hand_context.clear()

func _setup_tutorial() -> void:
	var sm = _safe_get_node("SaveManager")
	var has_completed_tutorial = false
	if sm != null:
		has_completed_tutorial = sm.has_completed_tutorial
		
	if not has_completed_tutorial:
		is_tutorial_active = true
		var t_mgr = t_mgr_scene.new()
		add_child(t_mgr)
	else:
		is_tutorial_active = false

func _setup_difficulty() -> void:
	var sm = _safe_get_node("SaveManager")
	if sm != null:
		max_player_hp = sm.max_player_hp
		player_hp = max_player_hp
		var sec = ProgressionSystem.get_current_sector(sm)
		
		base_poisoning_ratio = GameBalanceConfig.get_sector_poison(sec)
		data_poisoning_ratio = base_poisoning_ratio
		
		max_crisis_hp = GameBalanceConfig.get_sector_base_hp(sec)
		crisis_hp = max_crisis_hp

func _emit_initial_signals() -> void:
	hp_changed.emit(crisis_hp)
	player_hp_changed.emit(player_hp)
	sla_changed.emit(sla_timer)
	poisoning_updated.emit(data_poisoning_ratio)
	rate_limit_updated.emit(rate_limit_compression)

func _draw_starting_hand() -> void:
	var card_reg = _safe_get_node("CardRegistry")
	var event_bus = _safe_get_node("EventBus")
	var sm = _safe_get_node("SaveManager")
	
	if card_reg != null and event_bus != null:
		var equipped = ["keyword_search", "dense_search", "reranker"]
		if sm != null:
			equipped = sm.equipped_action_cards
			
		for card_id in equipped:
			var card = card_reg.get_card(card_id)
			if card:
				event_bus.card_drawn.emit(card)

func deduct_sla(amount: float) -> void:
	if is_game_active and not is_tutorial_active:
		sla_timer -= amount
		if sla_timer <= 0.0:
			sla_timer = 0.0
			is_game_active = false
			game_over.emit(false, "")
		sla_changed.emit(sla_timer)

func _on_request_play_card(card: Resource) -> void:
	if not is_game_active:
		return
		
	var cost = card.get("ap_cost") if card.get("ap_cost") != null else 1
	if current_ap < cost:
		print("Not enough AP to play card!")
		return
		
	if not hand_context.remove_card(card):
		print("Card not in hand!")
		return
		
	current_ap -= cost
	ap_changed.emit(current_ap)
	
	var type_val = card.get("type") if card.get("type") != null else CardData.CardType.ACTION_CARD
	
	if type_val == CardData.CardType.DATA_CHIP or type_val == CardData.CardType.NOISE_CHIP:
		active_context.add_card(card)
		var purity = BattleRuleEngine.calculate_context_purity(active_context.cards)
		context_updated.emit(purity)
		
	elif type_val == CardData.CardType.ACTION_CARD:
		CardEffectResolver.resolve_action_card(self, card)
		
	var event_bus = _safe_get_node("EventBus")
	if event_bus != null and event_bus.has_signal("card_played"):
		event_bus.card_played.emit(card)

func deliver_context() -> void:
	if not is_game_active:
		return
		
	current_ap -= GameBalanceConfig.DELIVERY_AP_COST
	ap_changed.emit(current_ap)
	deduct_sla(GameBalanceConfig.SLA_PENALTY_PER_DELIVERY)
	
	delivery_count += 1
	rate_limit_compression = max(GameBalanceConfig.RATE_LIMIT_COMPRESSION_MIN, GameBalanceConfig.RATE_LIMIT_COMPRESSION_BASE - (delivery_count * GameBalanceConfig.RATE_LIMIT_COMPRESSION_STEP))
	rate_limit_updated.emit(rate_limit_compression)
	
	var purity = BattleRuleEngine.calculate_context_purity(active_context.cards)
	var damage = 0.0
	
	if purity < 1.0:
		var noise_count = BattleRuleEngine.get_noise_chips(active_context.cards)
		var damage_taken = BattleRuleEngine.calculate_hallucination_damage(noise_count)
		player_hp -= damage_taken
		if player_hp <= 0:
			player_hp = 0
			is_game_active = false
			player_died.emit()
			game_over.emit(false, "")
		player_hp_changed.emit(player_hp)
	else:
		var has_chain = false
		for card in active_context.cards:
			if card.get("id") == GameBalanceConfig.CARD_GRAPH_RAG:
				has_chain = true
				break
		damage = BattleRuleEngine.calculate_delivery_damage(active_context.cards, GameBalanceConfig.BASE_FIREPOWER, GameBalanceConfig.SAFE_PURITY_THRESHOLD, has_chain)
		damage = damage * rate_limit_compression
		crisis_hp -= damage
		if crisis_hp <= 0:
			crisis_hp = 0
			is_game_active = false
			var rank = BattleRuleEngine.evaluate_battle_rank(sla_timer, player_hp, max_player_hp, delivery_count)
			print("Battle Won with Rank: ", rank)
			game_over.emit(true, rank)
		hp_changed.emit(crisis_hp)
		
	active_context.clear()
	context_updated.emit(0.0)
	context_purified.emit([])

func trigger_search(match_type: int, query_text: String = "default query") -> void:
	if not is_game_active:
		return
	if current_ap >= GameBalanceConfig.SEARCH_AP_COST:
		current_ap -= GameBalanceConfig.SEARCH_AP_COST
		ap_changed.emit(current_ap)
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
		hand_context.add_card(card)

func _apply_data_poisoning(card: Resource) -> void:
	if randf() < data_poisoning_ratio:
		var type_val = card.get("type") if card.get("type") != null else CardData.CardType.ACTION_CARD
		if type_val == CardData.CardType.DATA_CHIP:
			card.set("type", CardData.CardType.NOISE_CHIP)
			var current_title = card.get("title")
			if current_title != null and not current_title.begins_with("[CORRUPTED]"):
				card.set("title", "[CORRUPTED] " + current_title)

func _on_search_failed(error_code: int, message: String) -> void:
	print("Search failed (Code: %d, Message: %s). Activating Standalone Fallback!" % [error_code, message])
	var mock_cards = MockDataGenerator.generate_mock_rag_chunks()
	for card in mock_cards:
		_apply_data_poisoning(card)
		hand_context.add_card(card)
