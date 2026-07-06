extends Resource
class_name HandData

var cards: Array = []
var max_cards: int = 5

signal card_added(card: Resource)
signal hand_full()

func add_card(card: Resource) -> bool:
	if not is_instance_valid(card):
		return false
		
	if cards.size() >= max_cards:
		hand_full.emit()
		return false
				
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
