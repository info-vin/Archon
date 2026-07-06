extends Node

signal ap_changed(new_ap: int)
signal hp_changed(new_hp: float)
signal player_hp_changed(new_hp: float)
signal player_died()
signal context_updated(purity: float)
signal game_over(is_victory: bool, rank: String)
signal rate_limit_updated(compression: float)
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

var match_builder: Node
var search_ctrl: Node
var env_mgr: Node

func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null

func _ready() -> void:
	match_builder = preload("res://src/managers/MatchBuilder.gd").new()
	search_ctrl = preload("res://src/managers/SearchController.gd").new()
	env_mgr = preload("res://src/managers/EnvironmentManager.gd").new()
	
	env_mgr.game_state = self
	search_ctrl.game_state = self
	
	add_child(match_builder)
	add_child(search_ctrl)
	add_child(env_mgr)
	
	hand_context.card_added.connect(func(card):
		var event_bus = _safe_get_node("EventBus")
		if event_bus != null and event_bus.has_signal("card_drawn"):
			event_bus.card_drawn.emit(card)
	)

	var event_bus = _safe_get_node("EventBus")
	if event_bus != null:
		if event_bus.has_signal("request_play_card"):
			event_bus.request_play_card.connect(_on_request_play_card)

func start_game() -> void:
	_reset_stats()
	match_builder.build_match(self)
	_emit_initial_signals()

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

func _emit_initial_signals() -> void:
	hp_changed.emit(crisis_hp)
	player_hp_changed.emit(player_hp)
	env_mgr.sla_changed.emit(sla_timer)
	env_mgr.poisoning_updated.emit(data_poisoning_ratio)
	rate_limit_updated.emit(rate_limit_compression)

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
	
	var type_val = card.get("type") if card.get("type") != null else CardData.CardType.ACTION
	
	if type_val == CardData.CardType.DATA_CHIP or type_val == CardData.CardType.NOISE_CHIP:
		active_context.add_card(card)
		var purity = BattleRuleEngine.calculate_context_purity(active_context.cards)
		context_updated.emit(purity)
		
	elif type_val == CardData.CardType.ACTION:
		CardEffectResolver.resolve_action_card(self, card)
		
	var event_bus = _safe_get_node("EventBus")
	if event_bus != null and event_bus.has_signal("card_played"):
		event_bus.card_played.emit(card)

func deliver_context() -> void:
	if not is_game_active:
		return
		
	current_ap -= GameBalanceConfig.DELIVERY_AP_COST
	ap_changed.emit(current_ap)
	env_mgr.deduct_sla(GameBalanceConfig.SLA_PENALTY_PER_DELIVERY)
	
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
