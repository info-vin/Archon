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
