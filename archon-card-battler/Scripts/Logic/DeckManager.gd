extends RefCounted
class_name DeckManager

# 我們的牌庫只是一個裝著 CardStats 資源的陣列
var draw_pile: Array[CardStats] = []

func add_card(card: CardStats) -> void:
	draw_pile.append(card)

func get_deck_size() -> int:
	return draw_pile.size()

func draw_card() -> CardStats:
	if draw_pile.is_empty():
		return null
	# pop_back() 會移除陣列最後一個元素並回傳它（就像從牌堆最上方抽牌）
	return draw_pile.pop_back()
