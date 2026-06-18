extends RefCounted
class_name GameState

enum Difficulty { EASY, NORMAL, HARD, EXPERT }

signal player_hp_changed(current_hp, max_hp)
signal enemy_hp_changed(current_hp, max_hp)
signal player_block_changed(current_block)
signal enemy_block_changed(current_block)
signal mana_changed(current_mana, max_mana)
signal combo_changed(combo_count, combo_category)
signal log_event(message)
signal game_over_triggered(win)
signal smart_end_turn_triggered()
signal draw_finished()

# Juice signals
signal player_took_damage(amount)
signal enemy_took_damage(amount)
signal player_gained_block(amount)

var difficulty: int = Difficulty.NORMAL
var player_hp: int = 100
var player_max_hp: int = 100
var player_mana: int = 5
var player_max_mana: int = 5
var current_mana: int:
	get: return player_mana
	set(val): player_mana = val
var max_mana: int:
	get: return player_max_mana
	set(val): player_max_mana = val
var player_block: int = 0
var enemy_hp: int = 200
var enemy_max_hp: int = 200
var enemy_damage: int = 10
var enemy_block: int = 0
var enemy_strength: int = 0
var game_turn_counter: int = 0

# Combo System
var current_combo_category: String = ""
var combo_count: int = 0

var hand: Array = []
var deck_manager: RefCounted
var git_parser: RefCounted

var config: Resource

func _init(mana: int = 5, hp: int = 100):
	config = load("res://Scripts/Resources/GameConfig.tres")
	if not config: config = load("res://Scripts/Resources/GameConfig.gd").new() # Fallback
	self.player_max_mana = mana
	self.player_mana = mana
	self.player_max_hp = hp
	self.player_hp = hp
	self.player_block = 0

func select_difficulty(diff: int) -> void:
	difficulty = diff
	match difficulty:
		Difficulty.EASY:
			player_max_mana = config.easy_mana
			enemy_max_hp = config.easy_hp
			enemy_damage = config.easy_dmg
		Difficulty.NORMAL:
			player_max_mana = config.normal_mana
			enemy_max_hp = config.normal_hp
			enemy_damage = config.normal_dmg
		Difficulty.HARD:
			player_max_mana = config.hard_mana
			enemy_max_hp = config.hard_hp
			enemy_damage = config.hard_dmg
		Difficulty.EXPERT:
			player_max_mana = config.expert_mana
			enemy_max_hp = config.expert_hp
			enemy_damage = config.expert_dmg
			
	player_hp = player_max_hp
	enemy_hp = enemy_max_hp
	player_mana = player_max_mana
	player_block = 0
	enemy_block = 0
	enemy_strength = 0
	game_turn_counter = 0
	combo_count = 0
	current_combo_category = ""
	
	emit_signal("player_hp_changed", player_hp, player_max_hp)
	emit_signal("enemy_hp_changed", enemy_hp, enemy_max_hp)
	emit_signal("player_block_changed", player_block)
	emit_signal("enemy_block_changed", enemy_block)
	emit_signal("mana_changed", player_mana, player_max_mana)
	emit_signal("combo_changed", combo_count, current_combo_category)

func play_card(card: CardStats, _enemy: RefCounted = null) -> bool:
	if player_mana < card.cost:
		emit_signal("log_event", "Not enough mana!")
		return false
		
	player_mana -= card.cost
	emit_signal("mana_changed", player_mana, player_max_mana)
	
	# Combo system calculations
	var multiplier = 1.0
	if card.category == current_combo_category:
		combo_count += 1
		multiplier = 1.0 + (combo_count - 1) * 0.5
	else:
		current_combo_category = card.category
		combo_count = 1
	emit_signal("combo_changed", combo_count, current_combo_category)
		
	# Deal damage
	var final_damage = int(float(card.damage) * multiplier)
	var damage_to_deal = final_damage
	var absorbed_dmg = 0
	if enemy_block > 0:
		absorbed_dmg = min(damage_to_deal, enemy_block)
		enemy_block -= absorbed_dmg
		damage_to_deal -= absorbed_dmg
		emit_signal("enemy_block_changed", enemy_block)
		
	if damage_to_deal > 0:
		enemy_hp -= damage_to_deal
		if enemy_hp < 0:
			enemy_hp = 0
		emit_signal("enemy_hp_changed", enemy_hp, enemy_max_hp)
		emit_signal("enemy_took_damage", damage_to_deal)
		
	if _enemy != null and _enemy.has_method("take_damage"):
		_enemy.take_damage(final_damage)
		
	player_block += card.block
	emit_signal("player_block_changed", player_block)
	if card.block > 0:
		emit_signal("player_gained_block", card.block)
	
	var msg = "[color=#fde047]Played: " + card.card_name + "[/color]\n"
	if final_damage > 0:
		if combo_count > 1:
			msg += " dealt " + str(final_damage) + " DMG. (" + str(multiplier) + "x COMBO!)"
		else:
			msg += " dealt " + str(final_damage) + " DMG."
		if absorbed_dmg > 0:
			msg += " [color=#9ca3af](Block absorbed " + str(absorbed_dmg) + " DMG)[/color]"
			
	if card.block > 0:
		msg += " gained " + str(card.block) + " Block."
		
	# Play card effects based on category
	if card.category == "Performance":
		player_mana = min(player_max_mana, player_mana + 2)
		emit_signal("mana_changed", player_mana, player_max_mana)
		msg += " [color=#facc15][Str] Performance: Restored 2 Tokens![/color]"
	elif card.category == "Merge":
		player_hp = min(player_max_hp, player_hp + 10)
		emit_signal("player_hp_changed", player_hp, player_max_hp)
		msg += " [color=#fbbf24][Merge] Healed 10 HP![/color]"
	elif card.category == "Refactor":
		var bonus_block = int(float(final_damage) * 0.5)
		player_block += bonus_block
		emit_signal("player_block_changed", player_block)
		emit_signal("player_gained_block", bonus_block)
		msg += " [color=#60a5fa][Refactor] Gained %d Block from damage![/color]" % bonus_block
	elif card.category == "Test":
		player_block += card.block # Double block
		emit_signal("player_block_changed", player_block)
		emit_signal("player_gained_block", card.block)
		msg += " [color=#c084fc][Test] Doubled Block (+%d Block)![/color]" % card.block
	elif card.category == "Docs":
		if deck_manager != null and deck_manager.has_method("draw_card"):
			var drawn = deck_manager.draw_card()
			if drawn != null:
				hand.append(drawn)
				msg += " [color=#22d3ee][Docs] Drew 1 card (%s).[/color]" % drawn.card_name
				emit_signal("draw_finished")
	elif card.category == "Style":
		player_block += 10
		emit_signal("player_block_changed", player_block)
		emit_signal("player_gained_block", 10)
		msg += " [color=#f472b6][Style] Gained 10 Block![/color]"
	elif card.category == "Agent":
		enemy_hp -= 20
		if enemy_hp < 0:
			enemy_hp = 0
		emit_signal("enemy_hp_changed", enemy_hp, enemy_max_hp)
		emit_signal("enemy_took_damage", 20)
		msg += " [color=#a78bfa][Agent] Dealt 20 direct DMG (bypassed shields)![/color]"
	elif card.category == "Chore":
		var cards_to_discard = []
		for h_card in hand:
			if h_card != card:
				cards_to_discard.append(h_card)
		for h_card in cards_to_discard:
			if deck_manager != null and deck_manager.has_method("discard_card"):
				deck_manager.discard_card(h_card)
			hand.erase(h_card)
		msg += " [color=#9ca3af][Chore] Discarded hand and drew 2 cards.[/color]"
		for i in range(2):
			if deck_manager != null and deck_manager.has_method("draw_card"):
				var drawn = deck_manager.draw_card()
				if drawn != null:
					hand.append(drawn)
		emit_signal("draw_finished")
		
	emit_signal("log_event", msg)
	
	if deck_manager != null and deck_manager.has_method("discard_card"):
		deck_manager.discard_card(card)
	if hand.find(card) != -1:
		hand.remove_at(hand.find(card))
		
	if check_win_condition():
		return true
		
	check_smart_end_turn()
	return true

func enemy_attack(damage: int) -> int:
	var actual_damage = max(0, damage - player_block)
	player_block = max(0, player_block - damage)
	player_hp -= actual_damage
	if player_hp < 0:
		player_hp = 0
	emit_signal("player_hp_changed", player_hp, player_max_hp)
	emit_signal("player_block_changed", player_block)
	if actual_damage > 0:
		emit_signal("player_took_damage", actual_damage)
	return actual_damage

func enemy_turn() -> void:
	if player_hp <= 0 or enemy_hp <= 0:
		return
		
	# Gain Block based on difficulty
	var block_to_gain = 0
	if difficulty == Difficulty.HARD:
		block_to_gain = 5
	elif difficulty == Difficulty.EXPERT:
		block_to_gain = 10
		
	if block_to_gain > 0:
		enemy_block += block_to_gain
		emit_signal("enemy_block_changed", enemy_block)
		emit_signal("log_event", "[color=#a78bfa][Bug] Enemy gained " + str(block_to_gain) + " Block.[/color]")

	# Increase Strength
	game_turn_counter += 1
	var turn_interval = 3 if difficulty == Difficulty.HARD else 2
	if difficulty == Difficulty.HARD or difficulty == Difficulty.EXPERT:
		if game_turn_counter > 1 and (game_turn_counter - 1) % turn_interval == 0:
			var strength_gain = 3 if difficulty == Difficulty.HARD else 4
			enemy_strength += strength_gain
			emit_signal("log_event", "[color=#f87171][Str+] Enemy Strength increased! Attack permanently gains +" + str(strength_gain) + " DMG.[/color]")

	var final_enemy_damage = enemy_damage + enemy_strength
	emit_signal("log_event", "\n[b][color=#ef4444][Bug] Enemy attacks for " + str(final_enemy_damage) + " DMG![/color][/b]")
	
	var actual_damage = enemy_attack(final_enemy_damage)
	
	if player_block > 0:
		emit_signal("log_event", "[Block] absorbed " + str(min(final_enemy_damage, player_block)) + " DMG.")
		
	if actual_damage > 0:
		emit_signal("log_event", "Player took " + str(actual_damage) + " DMG.")
		
	emit_signal("draw_finished") # Update UI
	
	if !check_win_condition():
		start_player_turn()

func start_player_turn() -> void:
	player_mana = player_max_mana
	player_block = 0
	combo_count = 0
	current_combo_category = ""
	
	emit_signal("mana_changed", player_mana, player_max_mana)
	emit_signal("player_block_changed", player_block)
	emit_signal("combo_changed", combo_count, current_combo_category)
	
	for card in hand:
		if deck_manager != null:
			deck_manager.discard_card(card)
	hand.clear()
	
	for i in range(4):
		if deck_manager != null:
			var c = deck_manager.draw_card()
			if c != null:
				hand.append(c)
			else:
				emit_signal("log_event", "Deck is empty!")
				break
				
	emit_signal("log_event", "\n[b][color=#3b82f6]--- Player Turn Started ---[/color][/b]")
	emit_signal("draw_finished")

func check_smart_end_turn() -> bool:
	if hand.is_empty():
		emit_signal("smart_end_turn_triggered")
		return true
	var min_cost = 99
	for card in hand:
		if card.cost < min_cost:
			min_cost = card.cost
	if player_mana < min_cost:
		emit_signal("smart_end_turn_triggered")
		return true
	return false

func check_win_condition() -> bool:
	if enemy_hp <= 0:
		emit_signal("game_over_triggered", true)
		return true
	if player_hp <= 0:
		emit_signal("game_over_triggered", false)
		return true
	return false
