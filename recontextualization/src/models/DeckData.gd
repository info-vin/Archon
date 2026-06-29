extends Resource
class_name DeckData

@export var title: String = "Deck"
@export var cards: Array = [] # Avoid Array[CardData] for headless resolution issues

func size() -> int:
	return cards.size()

func shuffle():
	cards.shuffle()

func draw_card() -> Resource:
	return cards.pop_front()

func add_card(card: Resource):
	if not is_instance_valid(card):
		return
	cards.append(card)

func clear():
	cards.clear()

func draw_all() -> Array:
	var discarded: Array = cards.duplicate()
	clear()
	return discarded

# --- RAG Core Math ---
func calculate_context_purity(safe_threshold: float = 0.5) -> float:
	if cards.is_empty():
		return 0.0
	var data_cards_count := 0
	var valid_count := 0
	for card in cards:
		# DATA_CHIP = 2, NOISE_CHIP = 3
		if card.get("type") == 2 or card.get("type") == 3:
			data_cards_count += 1
			if not card.is_noise(safe_threshold):
				valid_count += 1
	if data_cards_count == 0:
		return 0.0
	return float(valid_count) / float(data_cards_count)

func get_noise_chips(safe_threshold: float = 0.5) -> int:
	var noise_count := 0
	for card in cards:
		if card.get("type") == 2 or card.get("type") == 3:
			if card.is_noise(safe_threshold):
				noise_count += 1
	return noise_count

func calculate_delivery_damage(base_firepower: float = 1000.0, safe_threshold: float = 0.5, has_chain_multiplier: bool = false) -> float:
	var purity := calculate_context_purity(safe_threshold)
	if purity < 1.0: # Model Hallucination Penalty
		return 0.0 
	var multiplier := 1.5 if has_chain_multiplier else 1.0
	return float(base_firepower) * purity * multiplier
