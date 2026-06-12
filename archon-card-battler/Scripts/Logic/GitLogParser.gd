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
	var files_changed = 0
	var files_regex = RegEx.new()
	files_regex.compile("(\\d+) file")
	var file_match = files_regex.search(stat_line)
	if file_match:
		files_changed = file_match.get_string(1).to_int()
	
	# Cost (費用)：最小值 1 費，最大值 3 費
	card.cost = clampi(files_changed, 1, 3)
		
	# Parse insertions
	var insertions = 0
	var insert_regex = RegEx.new()
	insert_regex.compile("(\\d+) insertion")
	var insert_match = insert_regex.search(stat_line)
	if insert_match:
		insertions = insert_match.get_string(1).to_int()
		
	# Attack (傷害)：Insertions / 10。保底 5 點，天花板 50 點
	card.damage = clampi(insertions / 10, 5, 50)
		
	# Parse deletions
	var deletions = 0
	var delete_regex = RegEx.new()
	delete_regex.compile("(\\d+) deletion")
	var delete_match = delete_regex.search(stat_line)
	if delete_match:
		deletions = delete_match.get_string(1).to_int()
		
	# Defense (護盾)：Deletions / 5。最大值 30 點
	card.block = clampi(deletions / 5, 0, 30)
		
	return card

# OS.execute() to retrieve git logs dynamically
func get_local_git_logs() -> Array[String]:
	var output = []
	var args = ["log", "-n", "20", "--shortstat", "--no-merges", "--pretty=format:%s"]
	var exit_code = OS.execute("git", args, output, true)
	if exit_code != 0 or output.is_empty():
		return get_fallback_logs()
	
	var raw_stdout = output[0]
	var parsed_logs = parse_raw_git_output(raw_stdout)
	if parsed_logs.is_empty():
		return get_fallback_logs()
	return parsed_logs

# Group commit titles with corresponding shortstat lines
func parse_raw_git_output(raw_stdout: String) -> Array[String]:
	var commits: Array[String] = []
	var lines = raw_stdout.split("\n")
	
	var i = 0
	while i < lines.size():
		var title = lines[i].strip_edges()
		if title.is_empty():
			i += 1
			continue
		
		var stat = ""
		var j = i + 1
		while j < lines.size():
			var line = lines[j].strip_edges()
			if line.is_empty():
				j += 1
				continue
			if "file" in line and ("changed" in line or "insertion" in line or "deletion" in line):
				stat = line
				i = j
				break
			else:
				break
			j += 1
		
		if not stat.is_empty():
			commits.append(title + "\n" + stat)
		i += 1
		
	return commits

# Fallback logs for web build or non-git environments
func get_fallback_logs() -> Array[String]:
	return [
		"Refactor auth module\n 4 files changed, 120 insertions(+), 30 deletions(-)",
		"Fix memory leak in parser\n 2 files changed, 15 insertions(+), 8 deletions(-)",
		"Update README.md\n 1 file changed, 5 insertions(+)",
		"Clean up dead CSS\n 3 files changed, 200 deletions(-)",
		"Implement RLS rules\n 2 files changed, 45 insertions(+), 5 deletions(-)",
		"Hotfix production crash\n 1 file changed, 2 insertions(+), 2 deletions(-)",
		"Upgrade dependencies\n 5 files changed, 300 insertions(+), 150 deletions(-)"
	]
