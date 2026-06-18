extends RefCounted
class_name DeckManager

# 我們的牌庫只是一個裝著 CardStats 資源的陣列
var draw_pile: Array[CardStats] = []
var discard_pile: Array[CardStats] = []

func add_card(card: CardStats) -> void:
	draw_pile.append(card)

func get_deck_size() -> int:
	return draw_pile.size()

func get_discard_size() -> int:
	return discard_pile.size()

func draw_card() -> CardStats:
	if draw_pile.is_empty():
		if discard_pile.is_empty():
			return null
		reshuffle()
	# pop_back() 會移除陣列最後一個元素並回傳它（就像從牌堆最上方抽牌）
	return draw_pile.pop_back()

func discard_card(card: CardStats) -> void:
	discard_pile.append(card)

func shuffle_deck() -> void:
	draw_pile.shuffle()

func reshuffle() -> void:
	draw_pile = discard_pile.duplicate()
	discard_pile.clear()
	draw_pile.shuffle()

