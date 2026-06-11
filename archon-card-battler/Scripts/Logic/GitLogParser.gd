extends RefCounted
class_name GitLogParser

func generate_card_from_log(log_output: String) -> CardStats:
	var lines = log_output.split("\n", false)
	if lines.size() < 2:
		return null
		
	var card = CardStats.new()
	card.card_name = lines[0].strip_edges()
	
	var title_lower = card.card_name.to_lower()
	if title_lower.begins_with("fix") or title_lower.begins_with("bug") or title_lower.begins_with("hotfix"):
		card.category = "Fix"
	elif title_lower.begins_with("refactor") or title_lower.begins_with("clean"):
		card.category = "Refactor"
	elif title_lower.begins_with("chore") or title_lower.begins_with("update") or title_lower.begins_with("upgrade"):
		card.category = "Chore"
	else:
		card.category = "Feature"
	
	var stat_line = lines[1].strip_edges()
	
	# Parse files changed
	var files_regex = RegEx.new()
	files_regex.compile("(\\d+) file")
	var file_match = files_regex.search(stat_line)
	if file_match:
		card.cost = file_match.get_string(1).to_int()
	else:
		card.cost = 0
		
	# Parse insertions
	var insert_regex = RegEx.new()
	insert_regex.compile("(\\d+) insertion")
	var insert_match = insert_regex.search(stat_line)
	if insert_match:
		card.damage = insert_match.get_string(1).to_int()
	else:
		card.damage = 0
		
	# Parse deletions
	var delete_regex = RegEx.new()
	delete_regex.compile("(\\d+) deletion")
	var delete_match = delete_regex.search(stat_line)
	if delete_match:
		card.block = delete_match.get_string(1).to_int()
	else:
		card.block = 0
		
	return card
