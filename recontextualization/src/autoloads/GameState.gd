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

# --- Sector Difficulty Constants ---
const SECTOR_1_BASE_HP = 10000.0
const SECTOR_2_BASE_HP = 15000.0
const SECTOR_3_BASE_HP = 20000.0

const SECTOR_1_POISON = 0.0
const SECTOR_2_POISON = 0.2
const SECTOR_3_POISON = 0.4
# ---------------------------------

var current_ap: int = 10
var crisis_hp: float = 10000.0
var max_crisis_hp: float = 10000.0

var player_hp: float = 100.0
var max_player_hp: float = 100.0

# Composite Threat Mechanics
var sla_timer: float = 300.0
var max_sla: float = 300.0
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
	# Instantiate BackendClient
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
		
		# Data Poisoning increases as SLA decreases. 
		var elapsed = max_sla - sla_timer
		var target_poison = min(0.8, base_poisoning_ratio + (elapsed / max_sla * 0.5))
		if abs(target_poison - data_poisoning_ratio) > 0.01:
			data_poisoning_ratio = target_poison
			poisoning_updated.emit(data_poisoning_ratio)
			
		if sla_timer <= 0.0:
			sla_timer = 0.0
			is_game_active = false
			game_over.emit(false, "")

func start_game() -> void:
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
	
	if sm != null:
		max_player_hp = sm.max_player_hp
		player_hp = max_player_hp
		var sec = sm.get_current_sector()
		if sec == 2:
			base_poisoning_ratio = SECTOR_2_POISON
			data_poisoning_ratio = SECTOR_2_POISON
			max_crisis_hp = SECTOR_2_BASE_HP
			crisis_hp = SECTOR_2_BASE_HP
		elif sec == 3:
			base_poisoning_ratio = SECTOR_3_POISON
			data_poisoning_ratio = SECTOR_3_POISON
			max_crisis_hp = SECTOR_3_BASE_HP
			crisis_hp = SECTOR_3_BASE_HP
		else:
			base_poisoning_ratio = SECTOR_1_POISON
			data_poisoning_ratio = SECTOR_1_POISON
			max_crisis_hp = SECTOR_1_BASE_HP
			crisis_hp = SECTOR_1_BASE_HP

	hp_changed.emit(crisis_hp)
	player_hp_changed.emit(player_hp)
	sla_changed.emit(sla_timer)
	poisoning_updated.emit(data_poisoning_ratio)
	rate_limit_updated.emit(rate_limit_compression)
	
	# Draw starting action cards based on SaveManager
	var card_reg = _safe_get_node("CardRegistry")
	var event_bus = _safe_get_node("EventBus")
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
		
	# Verify and remove from hand
	if not hand_context.remove_card(card):
		print("Card not in hand!")
		return
		
	current_ap -= cost
	ap_changed.emit(current_ap)
	
	var type_val = card.get("type") if card.get("type") != null else 1
	
	if type_val == 2 or type_val == 3:
		# Context Chips (Data/Noise)
		active_context.add_card(card)
		var purity = active_context.calculate_context_purity(0.5)
		context_updated.emit(purity)
		
	elif type_val == 1:
		# ACTION CARD
		CardEffectResolver.resolve_action_card(self, card)
		
	# Emit confirmed card_played so View can animate
	var event_bus = _safe_get_node("EventBus")
	if event_bus != null and event_bus.has_signal("card_played"):
		event_bus.card_played.emit(card)

func deliver_context() -> void:
	if not is_game_active:
		return
		
	# Delivery cost 1 AP
	current_ap -= 1
	ap_changed.emit(current_ap)
	deduct_sla(2.0) # SLA penalty: 2.0s
	
	delivery_count += 1
	rate_limit_compression = max(0.5, 1.0 - (delivery_count * 0.1))
	rate_limit_updated.emit(rate_limit_compression)
	
	var purity = active_context.calculate_context_purity(0.5)
	
	var damage = 0.0
	if purity < 1.0:
		# Hallucination Penalty: D = 0, player HP damage based on noise chips
		var noise_count = active_context.get_noise_chips(0.5)
		# TDD alignment: noise_count * 20.0 (5 chips = 100 HP dead)
		player_hp -= noise_count * 20.0
		if player_hp <= 0:
			player_hp = 0
			is_game_active = false
			player_died.emit()
			game_over.emit(false, "")
		player_hp_changed.emit(player_hp)
	else:
		# Check for GraphRAG KG multiplier
		var has_chain = false
		for card in active_context.cards:
			if card.get("id") == "graph_rag":
				has_chain = true
				break
		damage = active_context.calculate_delivery_damage(1000.0, 0.5, has_chain)
		damage = damage * rate_limit_compression
		crisis_hp -= damage
		if crisis_hp <= 0:
			crisis_hp = 0
			is_game_active = false
			var rank = calculate_battle_rank()
			print("Battle Won with Rank: ", rank)
			game_over.emit(true, rank)
		hp_changed.emit(crisis_hp)
		
	# Reset context
	active_context.clear()
	context_updated.emit(0.0)
	context_purified.emit([])

func trigger_search(match_type: int, query_text: String = "default query") -> void:
	if not is_game_active:
		return
	if current_ap >= 2:
		current_ap -= 2
		ap_changed.emit(current_ap)
		search_triggered.emit(match_type)
		backend_client.search(query_text, 0.5, 5)
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
			
		hand_context.add_card(card, data_poisoning_ratio)

func _on_search_failed(error_code: int, message: String) -> void:
	print("Search failed (Code: %d, Message: %s). Activating Standalone Fallback!" % [error_code, message])
	var num_cards = randi_range(3, 4)
	
	for i in range(num_cards):
		var card = CardData.new()
		card.type = CardData.CardType.DATA_CHIP
		card.similarity = randf_range(0.3, 0.98)
		card.title = "[MOCK] RAG Chunk #%d" % [i + 1]
		card.match_type = randi_range(1, 3)
		
		hand_context.add_card(card, data_poisoning_ratio)

func calculate_battle_rank() -> String:
	if sla_timer > 150.0 and player_hp >= max_player_hp and delivery_count <= 2:
		return "S"
	elif sla_timer > 60.0 and player_hp >= max_player_hp * 0.5:
		return "A"
	else:
		return "B"
