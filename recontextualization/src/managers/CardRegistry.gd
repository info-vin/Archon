extends Node

@export var cards_dir: String = "res://src/models/cards/resources/"

var cards: Dictionary = {}

func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null

var _preloaded_cards: Array[Resource] = [
	preload("res://src/models/cards/resources/keyword_search.tres"),
	preload("res://src/models/cards/resources/dense_search.tres"),
	preload("res://src/models/cards/resources/reranker.tres")
]

func _ready() -> void:
	for card in _preloaded_cards:
		if card and card.get("id") != null:
			register_card(card)

func register_card(card: Resource) -> void:
	if card.id == "":
		push_warning("Card %s has no ID, skipping registration" % card.title)
		return
	cards[card.id] = card

func get_card(id: String) -> Resource:
	if cards.has(id):
		return cards[id].duplicate()
	push_error("Card with ID %s not found in registry" % id)
	return null
