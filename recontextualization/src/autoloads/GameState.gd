extends Node

signal ap_changed(new_ap: int)
signal hp_changed(new_hp: float)
signal player_hp_changed(new_hp: float)
signal player_died()
signal context_updated(purity: float)
signal game_over(is_victory: bool)
signal sla_changed(new_sla: float)
signal poisoning_updated(ratio: float)
signal rate_limit_updated(compression: float)
signal search_triggered(match_type: int)
signal context_purified(remaining_card_instances: Array)

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

var active_context = preload("res://src/models/DeckData.gd").new()


func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null

func _ready() -> void:
	var event_bus = _safe_get_node("EventBus")
	if event_bus != null:
		if event_bus.has_signal("card_played"):
			event_bus.card_played.connect(_on_card_played)

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
			var sm = _safe_get_node("SaveManager")
			if sm != null:
				sm.penalize_battle_loss()
			game_over.emit(false)

func start_game() -> void:
	is_game_active = true
	sla_timer = max_sla
	player_hp = max_player_hp
	crisis_hp = max_crisis_hp
	rate_limit_compression = 1.0
	data_poisoning_ratio = 0.0
	delivery_count = 0
	
	var sm = _safe_get_node("SaveManager")
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
			var sm = _safe_get_node("SaveManager")
			if sm != null:
				sm.penalize_battle_loss()
			game_over.emit(false)
		sla_changed.emit(sla_timer)

func _on_card_played(card: Resource) -> void:
	if not is_game_active:
		return
		
	var cost = card.get("ap_cost") if card.get("ap_cost") != null else 1
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
		var card_id = card.get("id") if card.get("id") != null else ""
		deduct_sla(cost * 2.0) # Cost * 2.0 seconds penalty for playing action card
		
		if card_id == "reranker":
			# Reranker filter logic: remove similarity < 0.5 cards from active_context
			var remaining_cards = []
			for c in active_context.cards:
				var sim = c.get("similarity") if c.get("similarity") != null else 0.0
				if sim >= 0.5:
					remaining_cards.append(c)
			active_context.cards = remaining_cards
			var purity = active_context.calculate_context_purity(0.5)
			context_updated.emit(purity)
			context_purified.emit(remaining_cards)
			
		elif card_id == "keyword_search":
			search_triggered.emit(3) # KEYWORD
			# Draw back so it's reusable
			var event_bus = _safe_get_node("EventBus")
			if event_bus != null:
				event_bus.card_drawn.emit(card.duplicate())
				
		elif card_id == "dense_search":
			search_triggered.emit(2) # VECTOR
			var event_bus = _safe_get_node("EventBus")
			if event_bus != null:
				event_bus.card_drawn.emit(card.duplicate())

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
			var sm = _safe_get_node("SaveManager")
			if sm != null:
				sm.penalize_battle_loss()
			player_died.emit()
			game_over.emit(false)
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
			var sm = _safe_get_node("SaveManager")
			if sm != null:
				sm.award_battle_loot(rank)
			game_over.emit(true)
		hp_changed.emit(crisis_hp)
		
	# Reset context
	active_context.clear()
	context_updated.emit(0.0)
	context_purified.emit([])

func trigger_search(match_type: int) -> void:
	if not is_game_active:
		return
	if current_ap >= 2:
		current_ap -= 2
		ap_changed.emit(current_ap)
		search_triggered.emit(match_type)
	else:
		print("Not enough AP to search!")

func calculate_battle_rank() -> String:
	if sla_timer > 150.0 and player_hp >= max_player_hp and delivery_count <= 2:
		return "S"
	elif sla_timer > 60.0 and player_hp >= max_player_hp * 0.5:
		return "A"
	else:
		return "B"
