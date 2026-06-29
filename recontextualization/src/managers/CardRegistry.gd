extends Node

var cards: Dictionary = {}

func _ready():
	load_all_cards("res://src/models/cards/resources/")

func load_all_cards(path: String):
	var dir = DirAccess.open(path)
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if not dir.current_is_dir() and file_name.ends_with(".tres"):
				# IMPORTANT: Use preload pattern or load cautiously. For dynamic loading in Godot 4, load() is fine if the paths are exported, but we'll use load() here since it's scanning.
				var resource = load(path + "/" + file_name)
				if resource.get("id") != null: # Duck typing check
					register_card(resource)
			file_name = dir.get_next()
	else:
		push_warning("Directory not found or error accessing: " + path)

func register_card(card: Resource):
	if card.id == "":
		push_warning("Card %s has no ID, skipping registration" % card.title)
		return
	cards[card.id] = card

func get_card(id: String) -> Resource:
	if cards.has(id):
		return cards[id].duplicate()
	push_error("Card with ID %s not found in registry" % id)
	return null
