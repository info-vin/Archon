@tool
extends MiniTest

func _run() -> void:
	run_test_suite()

func test_play_card_reduces_mana_and_deals_damage() -> void:
	var GameState = preload("res://Scripts/Logic/GameState.gd")
	var EnemyAgent = preload("res://Scripts/Logic/EnemyAgent.gd")
	var CardStats = preload("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameState.new(10)
	var enemy = EnemyAgent.new(100)
	var card = CardStats.new()
	card.cost = 3
	card.damage = 45
	
	var success = game_state.play_card(card, enemy)
	
	assert_eq(success, true, "Card should be playable")
	assert_eq(game_state.current_mana, 7, "Mana should be correctly deducted (10 - 3)")
	assert_eq(enemy.current_hp, 55, "Enemy should take correct damage (100 - 45)")

func test_cannot_play_card_without_enough_mana() -> void:
	var GameState = preload("res://Scripts/Logic/GameState.gd")
	var EnemyAgent = preload("res://Scripts/Logic/EnemyAgent.gd")
	var CardStats = preload("res://Scripts/Resources/CardStats.gd")
	
	var game_state = GameState.new(2)
	var enemy = EnemyAgent.new(100)
	var card = CardStats.new()
	card.cost = 3
	card.damage = 45
	
	var success = game_state.play_card(card, enemy)
	
	assert_eq(success, false, "Card should NOT be playable")
	assert_eq(game_state.current_mana, 2, "Mana should not be deducted")
	assert_eq(enemy.current_hp, 100, "Enemy should not take damage")
