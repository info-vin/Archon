extends RefCounted
class_name DeckController

static func initialize_deck(deck_manager: DeckManager, git_parser: RefCounted) -> void:
	var logs = git_parser.get_local_git_logs()
	logs.shuffle() # Prevent deterministic starting decks
	for i in range(15):
		var log_str = logs[i % logs.size()]
		var card = git_parser.generate_card_from_log(log_str)
		deck_manager.add_card(card)
	deck_manager.shuffle_deck()
