class_name ProgressionSystem

static func get_current_sector(save_manager: Node) -> int:
	if save_manager.clearance_rating >= GameBalanceConfig.SECTOR_3_CR_THRESHOLD:
		return 3
	elif save_manager.clearance_rating >= GameBalanceConfig.SECTOR_2_CR_THRESHOLD:
		return 2
	else:
		return 1

static func check_level_up(save_manager: Node) -> void:
	var xp_needed = GameBalanceConfig.BASE_XP_PER_LEVEL * save_manager.cognitive_level
	while save_manager.current_xp >= xp_needed:
		save_manager.current_xp -= xp_needed
		save_manager.cognitive_level += 1
		save_manager.topology_points += 1
		xp_needed = GameBalanceConfig.BASE_XP_PER_LEVEL * save_manager.cognitive_level

static func award_battle_loot(save_manager: Node, rank: String) -> void:
	var xp_gain = 0.0
	var cr_gain = 0
	if rank == "S":
		save_manager.material_inventory["data_core_s"] = save_manager.material_inventory.get("data_core_s", 0) + 1
		xp_gain = GameBalanceConfig.REWARD_S_XP
		cr_gain = GameBalanceConfig.REWARD_S_CR
	elif rank == "A":
		save_manager.material_inventory["data_core_a"] = save_manager.material_inventory.get("data_core_a", 0) + 1
		xp_gain = GameBalanceConfig.REWARD_A_XP
		cr_gain = GameBalanceConfig.REWARD_A_CR
	elif rank == "B":
		save_manager.material_inventory["data_core_b"] = save_manager.material_inventory.get("data_core_b", 0) + 1
		xp_gain = GameBalanceConfig.REWARD_B_XP
		cr_gain = GameBalanceConfig.REWARD_B_CR
		
	save_manager.clearance_rating += cr_gain
	save_manager.highest_sector = max(save_manager.highest_sector, get_current_sector(save_manager))
	
	save_manager.current_xp += xp_gain
	check_level_up(save_manager)
		
	var drop_pool = [GameBalanceConfig.CARD_KEYWORD]
	var sec = get_current_sector(save_manager)
	if sec >= 2:
		drop_pool.append(GameBalanceConfig.CARD_DENSE)
	if sec >= 3:
		drop_pool.append(GameBalanceConfig.CARD_RERANKER)
		
	var drop_card = drop_pool.pick_random()
	save_manager.player_inventory.append({"base_id": drop_card, "level": 1})
	save_manager.save_progress()

static func penalize_battle_loss(save_manager: Node) -> void:
	save_manager.clearance_rating = max(0, save_manager.clearance_rating - GameBalanceConfig.LOSS_CR_PENALTY)
	save_manager.save_progress()
