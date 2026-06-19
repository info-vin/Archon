extends RefCounted
class_name GitLogParser

var git_translator = preload("res://Scripts/Logic/GitTranslator.gd").new()

func generate_card_from_log(log_output: String) -> CardStats:
	var lines = log_output.split("\n", false)
	if lines.size() < 2:
		return null
		
	var card = CardStats.new()
	var raw_title = lines[0].strip_edges()
	
	var title_lower = raw_title.to_lower()
	if title_lower.contains("merge") or title_lower.begins_with("merged"):
		card.category = "Merge"
	elif "🤖" in raw_title or title_lower.begins_with("agent:") or title_lower.begins_with("ai:"):
		card.category = "Agent"
	elif title_lower.begins_with("feat") or "✨" in raw_title:
		card.category = "Feature"
	elif title_lower.begins_with("docs") or title_lower.begins_with("doc") or title_lower.contains("readme"):
		card.category = "Docs"
	elif title_lower.begins_with("fix") or title_lower.begins_with("bug") or title_lower.begins_with("hotfix") or title_lower.contains("issue"):
		card.category = "Fix"
	elif title_lower.begins_with("refactor") or title_lower.begins_with("clean"):
		card.category = "Refactor"
	elif title_lower.begins_with("perf") or "⚡" in raw_title or title_lower.contains("performance"):
		card.category = "Performance"
	elif title_lower.begins_with("test") or "🧪" in raw_title or title_lower.contains("pytest") or title_lower.contains("vitest") or title_lower.contains("unittest"):
		card.category = "Test"
	elif title_lower.begins_with("style") or "🎨" in raw_title or title_lower.contains("css") or title_lower.contains("theme") or title_lower.begins_with("ui:"):
		card.category = "Style"
	elif title_lower.begins_with("chore") or title_lower.begins_with("ci:") or title_lower.begins_with("build:") or title_lower.begins_with("deps:"):
		card.category = "Chore"
	else:
		card.category = "Feature"
	
	card.card_name = git_translator.translate_message(raw_title)
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
	var args = ["log", "-n", "50", "--shortstat", "--no-merges", "--pretty=format:%s"]
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
		"[Feature] 實作雙生模擬器核心 (feat: implement twin simulator core)\n 8 files changed, 250 insertions(+), 30 deletions(-)",
		"[Docs] 撰寫 API 整合說明文件 (docs: document api integrations)\n 1 file changed, 45 insertions(+)",
		"[Merge] 合併分支 dev/twins 到 main (Merge branch dev/twins into main)\n 12 files changed, 500 insertions(+), 200 deletions(-)",
		"[Fix] 修復 RAG 設置中的無窮重渲染 (fix: infinite re-render loop in RAGSettings)\n 2 files changed, 15 insertions(+), 8 deletions(-)",
		"[Refactor] 重構驗證與憑證模組 (refactor: restructure auth credentials module)\n 4 files changed, 120 insertions(+), 90 deletions(-)",
		"[Performance] 效能優化：減少冷啟動延遲 (perf: reduce cold start latency)\n 3 files changed, 60 insertions(+), 10 deletions(-)",
		"[Chore] 升級前端相依套件與設定 (chore: upgrade packages)\n 5 files changed, 300 insertions(+), 150 deletions(-)",
		"[Test] 新增 TDD 戰鬥邏輯單元測試 (test: add unit tests for combat logic)\n 3 files changed, 85 insertions(+)",
		"[Style] 霓虹邊框樣式與毛玻璃特效優化 (style: adjust glow border and glassmorphism styling)\n 2 files changed, 40 insertions(+), 15 deletions(-)",
		"[Agent] 實作自動化 UI 審計與視覺裁判 (agent: deploy visual UI audit agent)\n 6 files changed, 180 insertions(+), 25 deletions(-)"
	]

