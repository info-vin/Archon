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
	load_all_cards(cards_dir)

func load_all_cards(path: String) -> void:
	var dir = DirAccess.open(path)
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if not dir.current_is_dir() and file_name.ends_with(".tres"):
				var full_path = path + file_name if path.ends_with("/") else path + "/" + file_name
				var resource = load(full_path)
				print("Attempting to load card: ", full_path)
				if resource and resource.get("id") != null: # Duck typing check
					print("Loaded card successfully: ", resource.get("id"))
					register_card(resource)
			file_name = dir.get_next()
	else:
		push_warning("Directory not found or error accessing: " + path)

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
