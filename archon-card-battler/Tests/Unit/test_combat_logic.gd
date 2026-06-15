extends MiniTest

func test_play_card_reduces_mana_and_deals_damage() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var EnemyAgent = preload("res://Scripts/Logic/EnemyAgent.gd")
	var CardStats = preload("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameStateClass.new(10)
	var enemy = EnemyAgent.new(100)
	var card = CardStats.new()
	card.cost = 3
	card.damage = 45
	
	var success = game_state.play_card(card, enemy)
	
	assert_eq(success, true, "Card should be playable")
	assert_eq(game_state.current_mana, 7, "Mana should be correctly deducted (10 - 3)")
	assert_eq(enemy.current_hp, 55, "Enemy should take correct damage (100 - 45)")

func test_cannot_play_card_without_enough_mana() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var EnemyAgent = preload("res://Scripts/Logic/EnemyAgent.gd")
	var CardStats = preload("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameStateClass.new(2)
	var enemy = EnemyAgent.new(100)
	var card = CardStats.new()
	card.cost = 3
	card.damage = 45
	
	var success = game_state.play_card(card, enemy)
	
	assert_eq(success, false, "Card should NOT be playable")
	assert_eq(game_state.current_mana, 2, "Mana should not be deducted")
	assert_eq(enemy.current_hp, 100, "Enemy should not take damage")

func test_play_card_adds_block() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	var EnemyAgent = preload("res://Scripts/Logic/EnemyAgent.gd")
	var CardStats = preload("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameStateClass.new(10)
	var enemy = EnemyAgent.new(100)
	var card = CardStats.new()
	card.cost = 1
	card.block = 15
	
	var success = game_state.play_card(card, enemy)
	
	assert_eq(success, true, "Defensive card should be playable")
	assert_eq(game_state.player_block, 15, "Player block should increase by 15")

func test_block_absorbs_damage_completely() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	
	var game_state = GameStateClass.new(5, 100)
	game_state.player_block = 20
	
	var actual_damage = game_state.enemy_attack(15)
	
	assert_eq(actual_damage, 0, "Actual damage taken should be 0 (fully blocked)")
	assert_eq(game_state.player_block, 5, "Remaining block should be 5 (20 - 15)")
	assert_eq(game_state.player_hp, 100, "Player HP should remain 100")

func test_block_absorbs_damage_partially() -> void:
	var GameStateClass = load("res://Scripts/Logic/GameState.gd")
	
	var game_state = GameStateClass.new(5, 100)
	game_state.player_block = 10
	
	var actual_damage = game_state.enemy_attack(25)
	
	assert_eq(actual_damage, 15, "Actual damage taken should be 15 (25 - 10)")
	assert_eq(game_state.player_block, 0, "Remaining block should be 0")
	assert_eq(game_state.player_hp, 85, "Player HP should drop to 85 (100 - 15)")
