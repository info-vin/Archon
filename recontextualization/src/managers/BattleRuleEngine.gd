class_name BattleRuleEngine

static func calculate_hallucination_damage(noise_count: int) -> float:
	return float(noise_count) * GameBalanceConfig.HALLUCINATION_DAMAGE_PER_NOISE

static func evaluate_battle_rank(sla_timer: float, player_hp: float, max_player_hp: float, delivery_count: int) -> String:
	var half_max_sla = GameBalanceConfig.MAX_SLA_TIME * GameBalanceConfig.RANK_S_SLA_RATIO
	var low_sla_threshold = GameBalanceConfig.MAX_SLA_TIME * GameBalanceConfig.RANK_A_SLA_RATIO
	
	if sla_timer > half_max_sla and player_hp >= max_player_hp and delivery_count <= GameBalanceConfig.RANK_S_DELIVERY_LIMIT:
		return "S"
	elif sla_timer > low_sla_threshold and player_hp >= max_player_hp * GameBalanceConfig.RANK_A_HP_RATIO:
		return "A"
	else:
		return "B"

static func calculate_context_purity(cards: Array, safe_threshold: float = GameBalanceConfig.SAFE_PURITY_THRESHOLD) -> float:
	if cards.is_empty():
		return 0.0
		
	var data_cards_count := 0
	var valid_count := 0

	
	for card in cards:
		var type_val = card.get("type") if "type" in card else CardData.CardType.DATA_CHIP
		if type_val == CardData.CardType.DATA_CHIP or type_val == CardData.CardType.NOISE_CHIP:
			data_cards_count += 1
			if not card.is_noise(safe_threshold):
				valid_count += 1
				
	if data_cards_count == 0:
		return 0.0
	return float(valid_count) / float(data_cards_count)

static func get_noise_chips(cards: Array, safe_threshold: float = GameBalanceConfig.SAFE_PURITY_THRESHOLD) -> int:
	var noise_count := 0

	
	for card in cards:
		var type_val = card.get("type") if "type" in card else CardData.CardType.DATA_CHIP
		if type_val == CardData.CardType.DATA_CHIP or type_val == CardData.CardType.NOISE_CHIP:
			if card.is_noise(safe_threshold):
				noise_count += 1
	return noise_count

static func calculate_delivery_damage(cards: Array, base_firepower: float = GameBalanceConfig.BASE_FIREPOWER, safe_threshold: float = GameBalanceConfig.SAFE_PURITY_THRESHOLD, has_chain_multiplier: bool = false) -> float:
	var purity := calculate_context_purity(cards, safe_threshold)
	if purity < 1.0: # Model Hallucination Penalty
		return 0.0 
	var multiplier := GameBalanceConfig.MULTIPLIER_CHAIN if has_chain_multiplier else GameBalanceConfig.MULTIPLIER_BASE
	return float(base_firepower) * purity * multiplier
