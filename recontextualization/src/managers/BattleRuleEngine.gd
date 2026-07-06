class_name BattleRuleEngine

static func calculate_hallucination_damage(noise_count: int) -> float:
	return float(noise_count) * GameBalanceConfig.HALLUCINATION_DAMAGE_PER_NOISE

static func evaluate_battle_rank(sla_timer: float, player_hp: float, max_player_hp: float, delivery_count: int) -> String:
	var half_max_sla = GameBalanceConfig.MAX_SLA_TIME / 2.0
	var low_sla_threshold = GameBalanceConfig.MAX_SLA_TIME * 0.2
	
	if sla_timer > half_max_sla and player_hp >= max_player_hp and delivery_count <= 2:
		return "S"
	elif sla_timer > low_sla_threshold and player_hp >= max_player_hp * 0.5:
		return "A"
	else:
		return "B"

static func calculate_context_purity(cards: Array, safe_threshold: float = GameBalanceConfig.SAFE_PURITY_THRESHOLD) -> float:
	if cards.is_empty():
		return 0.0
		
	var data_cards_count := 0
	var valid_count := 0
	var CardData = preload("res://src/models/cards/CardData.gd")
	
	for card in cards:
		var type_val = card.get("type") if card.get("type") != null else 1
		if type_val == CardData.CardType.DATA_CHIP or type_val == CardData.CardType.NOISE_CHIP:
			data_cards_count += 1
			if not card.is_noise(safe_threshold):
				valid_count += 1
				
	if data_cards_count == 0:
		return 0.0
	return float(valid_count) / float(data_cards_count)

static func get_noise_chips(cards: Array, safe_threshold: float = GameBalanceConfig.SAFE_PURITY_THRESHOLD) -> int:
	var noise_count := 0
	var CardData = preload("res://src/models/cards/CardData.gd")
	
	for card in cards:
		var type_val = card.get("type") if card.get("type") != null else 1
		if type_val == CardData.CardType.DATA_CHIP or type_val == CardData.CardType.NOISE_CHIP:
			if card.is_noise(safe_threshold):
				noise_count += 1
	return noise_count

static func calculate_delivery_damage(cards: Array, base_firepower: float = GameBalanceConfig.BASE_FIREPOWER, safe_threshold: float = GameBalanceConfig.SAFE_PURITY_THRESHOLD, has_chain_multiplier: bool = false) -> float:
	var purity := calculate_context_purity(cards, safe_threshold)
	if purity < 1.0: # Model Hallucination Penalty
		return 0.0 
	var multiplier := 1.5 if has_chain_multiplier else 1.0
	return float(base_firepower) * purity * multiplier
