extends Resource
class_name HandData

var cards: Array = []
var max_cards: int = 5

signal card_added(card: Resource)
signal hand_full()

func add_card(card: Resource, poisoning_ratio: float) -> bool:
	if not is_instance_valid(card):
		return false
		
	if cards.size() >= max_cards:
		hand_full.emit()
		return false
		
	# Apply Data Poisoning
	if randf() < poisoning_ratio:
		var type_val = card.get("type") if card.get("type") != null else 1
		if type_val == 2: # DATA_CHIP = 2
			card.set("type", 3) # Convert to NOISE_CHIP = 3
			var current_title = card.get("title")
			if current_title != null and not current_title.begins_with("[CORRUPTED]"):
				card.set("title", "[CORRUPTED] " + current_title)
				
	cards.append(card)
	card_added.emit(card)
	return true

func remove_card(card: Resource) -> bool:
	if cards.has(card):
		cards.erase(card)
		return true
	return false

func clear() -> void:
	cards.clear()
