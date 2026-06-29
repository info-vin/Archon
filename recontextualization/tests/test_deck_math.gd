extends RefCounted

func assert_eq(actual, expected, message: String = "") -> bool:
	if actual == expected:
		return true
	print("FAIL: Expected ", expected, " but got ", actual, ". ", message)
	return false

func assert_float_eq(actual, expected, epsilon: float = 0.001, message: String = "") -> bool:
	if abs(actual - expected) < epsilon:
		return true
	print("FAIL: Expected ~", expected, " but got ", actual, ". ", message)
	return false

func run_tests() -> bool:
	var passed = true
	print("Running test_deck_math...")
	
	# 1. Setup Data
	var deck_script = preload("res://src/models/DeckData.gd")
	var deck = deck_script.new()
	
	var card_script = preload("res://src/models/cards/CardData.gd")
	
	var card1 = card_script.new()
	card1.set("type", 2) # DATA_CHIP = 2
	card1.set("similarity", 0.8)
	
	var card2 = card_script.new()
	card2.set("type", 2)
	card2.set("similarity", 0.9)
	
	var card3 = card_script.new()
	card3.set("type", 2)
	card3.set("similarity", 0.6)
	
	var card4 = card_script.new()
	card4.set("type", 2)
	card4.set("similarity", 0.2)
	
	var card5 = card_script.new()
	card5.set("type", 2)
	card5.set("similarity", 0.4)
	
	deck.add_card(card1)
	deck.add_card(card2)
	deck.add_card(card3)
	deck.add_card(card4)
	deck.add_card(card5)
	
	# 2. Test calculate_context_purity()
	var purity = deck.calculate_context_purity(0.5)
	if not assert_float_eq(purity, 0.6, 0.001, "Context Purity should be 0.6"): passed = false
	
	# 3. Test get_noise_chips()
	var noise = deck.get_noise_chips(0.5)
	if not assert_eq(noise, 2, "Noise chips should be 2"): passed = false
	
	# 4. Test calculate_delivery_damage()
	var damage = deck.calculate_delivery_damage(1000.0, 0.5)
	if not assert_float_eq(damage, 0.0, 0.001, "Damage should be 0 due to hallucination penalty"): passed = false
	
	# Remove noise and re-test
	var _pop1 = deck.cards.pop_back()
	var _pop2 = deck.cards.pop_back()
	
	damage = deck.calculate_delivery_damage(1000.0, 0.5)
	if not assert_float_eq(damage, 1000.0, 0.001, "Damage should be 1000.0 (purity is 1.0)"): passed = false
	
	# Test chain multiplier
	damage = deck.calculate_delivery_damage(1000.0, 0.5, true)
	if not assert_float_eq(damage, 1500.0, 0.001, "Damage should be 1500.0 with chain multiplier"): passed = false
	
	if passed:
		print("test_deck_math PASSED")
	else:
		print("test_deck_math FAILED")
	
	return passed
