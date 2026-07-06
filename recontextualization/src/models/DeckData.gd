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
