extends Node

signal exp_gained(amount: int)
signal leveled_up(new_level: int)

var total_exp: int = 0
var current_level: int = 3 # L3, L4, L5, L6
var unlocked_cards: Array[String] = ["bm25_search", "dense_search"]
var ap_cap: int = 5

func gain_exp(amount: int):
	total_exp += amount
	exp_gained.emit(amount)
	check_level_up()

func check_level_up():
	# Simple progression curve
	var needed_exp = (current_level - 2) * 1000 
	if total_exp >= needed_exp and current_level < 6:
		current_level += 1
		total_exp -= needed_exp
		_on_level_up()
		leveled_up.emit(current_level)

func _on_level_up():
	match current_level:
		4:
			if not unlocked_cards.has("reranker_shield"):
				unlocked_cards.append("reranker_shield")
			ap_cap = 6
		5:
			if not unlocked_cards.has("graphrag_shield"):
				unlocked_cards.append("graphrag_shield")
			ap_cap = 7
		6:
			if not unlocked_cards.has("matryoshka_shrink"):
				unlocked_cards.append("matryoshka_shrink")
			ap_cap = 8
