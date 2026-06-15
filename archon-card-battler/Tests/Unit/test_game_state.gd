extends MiniTest

func test_difficulty_settings() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var game_state = GameStateClass.new(5, 100)
	
	# Test Expert Difficulty Setup
	game_state.select_difficulty(3) # Difficulty.EXPERT = 3
	assert_eq(game_state.difficulty, 3, "Difficulty should be EXPERT")
	assert_eq(game_state.player_max_mana, 4, "EXPERT player max mana should be 4")
	assert_eq(game_state.enemy_max_hp, 600, "EXPERT enemy max HP should be 600")
	assert_eq(game_state.enemy_damage, 15, "EXPERT enemy damage should be 15")
	assert_eq(game_state.enemy_hp, 600, "EXPERT enemy current HP should be 600")
	
	# Test Easy Difficulty Setup
	game_state.select_difficulty(0) # Difficulty.EASY = 0
	assert_eq(game_state.difficulty, 0, "Difficulty should be EASY")
	assert_eq(game_state.player_max_mana, 5, "EASY player max mana should be 5")
	assert_eq(game_state.enemy_max_hp, 60, "EASY enemy max HP should be 60")
	assert_eq(game_state.enemy_damage, 5, "EASY enemy damage should be 5")

func test_card_effects_and_combos() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var CardStatsClass = load("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameStateClass.new(5, 100)
	game_state.select_difficulty(1) # Difficulty.NORMAL (HP=200, mana=5)
	
	# Define a basic Feature card (damage only)
	var card_feat = CardStatsClass.new()
	card_feat.category = "Feature"
	card_feat.cost = 2
	card_feat.damage = 20
	card_feat.block = 0
	
	# Play first card (Combo = 1, multiplier = 1.0)
	var success = game_state.play_card(card_feat)
	assert_eq(success, true, "Card play should succeed")
	assert_eq(game_state.player_mana, 3, "Mana should decrease from 5 to 3")
	assert_eq(game_state.enemy_hp, 180, "Enemy HP should decrease by 20 (200 - 20)")
	assert_eq(game_state.combo_count, 1, "Combo count should be 1")
	
	# Play second card (Combo = 2, multiplier = 1.5x)
	# Category matches (Feature), so Combo count increments to 2
	# Damage should be 20 * 1.5 = 30
	var success2 = game_state.play_card(card_feat)
	assert_eq(success2, true, "Second card play should succeed")
	assert_eq(game_state.player_mana, 1, "Mana should decrease from 3 to 1")
	assert_eq(game_state.enemy_hp, 150, "Enemy HP should decrease by 30 (180 - 30)")
	assert_eq(game_state.combo_count, 2, "Combo count should be 2")

func test_special_card_categories() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var CardStatsClass = load("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameStateClass.new(5, 100)
	game_state.select_difficulty(1) # HP=200, player HP=100
	
	# 1. Test Merge healing card
	var card_merge = CardStatsClass.new()
	card_merge.category = "Merge"
	card_merge.cost = 1
	card_merge.damage = 10
	card_merge.block = 5
	game_state.player_hp = 50 # Damaged player
	
	game_state.play_card(card_merge)
	assert_eq(game_state.player_hp, 60, "Merge card should heal player by 10 HP (50 -> 60)")
	assert_eq(game_state.player_block, 5, "Merge card should give 5 Block")
	
	# 2. Test Performance mana restoration
	var card_perf = CardStatsClass.new()
	card_perf.category = "Performance"
	card_perf.cost = 1
	card_perf.damage = 0
	card_perf.block = 0
	game_state.player_mana = 2
	
	game_state.play_card(card_perf)
	assert_eq(game_state.player_mana, 3, "Performance card should restore 2 mana (clamped to max mana: 2 - 1 cost + 2 = 3)")

func test_smart_end_turn_trigger() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var CardStatsClass = load("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameStateClass.new(5, 100)
	game_state.select_difficulty(1) # player_max_mana = 5
	
	var card1 = CardStatsClass.new()
	card1.cost = 2
	var card2 = CardStatsClass.new()
	card2.cost = 3
	
	game_state.hand = [card1, card2]
	game_state.player_mana = 4
	assert_eq(game_state.check_smart_end_turn(), false, "Should not end turn if mana (4) >= min cost (2)")
	
	game_state.player_mana = 1
	assert_eq(game_state.check_smart_end_turn(), true, "Should end turn if mana (1) < min cost (2)")
