extends Node

@export var cards_dir: String = "res://src/models/cards/resources/"

var cards: Dictionary = {}

func _safe_get_node(singleton_name: String) -> Node:
	if Engine.has_singleton(singleton_name):
		return Engine.get_singleton(singleton_name)
	if is_inside_tree():
		return get_node_or_null("/root/" + singleton_name)
	return null

func _ready() -> void:
	var dir = DirAccess.open(cards_dir)
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if not dir.current_is_dir():
				if file_name.ends_with(".tres") or file_name.ends_with(".tres.remap"):
					var actual_name = file_name.replace(".remap", "")
					var res = ResourceLoader.load(cards_dir + actual_name)
					if res and res.get("id") != null:
						register_card(res)
			file_name = dir.get_next()

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
