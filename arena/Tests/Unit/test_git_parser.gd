extends MiniTest

func test_parse_git_shortstat_full() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Fix memory leak\n 3 files changed, 45 insertions(+), 12 deletions(-)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.card_name, "修復錯誤 memory leak", "Card name should match commit message")
	assert_eq(card_data.cost, 3, "Cost should match clamped files changed (3)")
	assert_eq(card_data.damage, 5, "Damage should match clamped insertions / 10 (45/10=4, clamped to min 5)")
	assert_eq(card_data.block, 2, "Block should match clamped deletions / 5 (12/5=2)")

func test_parse_git_shortstat_insertions_only() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Update readme\n 1 file changed, 5 insertions(+)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.card_name, "更新 readme", "Card name should match commit message")
	assert_eq(card_data.cost, 1, "Cost should match clamped files changed (1)")
	assert_eq(card_data.damage, 5, "Damage should match clamped insertions / 10 (5/10=0, clamped to min 5)")
	assert_eq(card_data.block, 0, "Block should be 0 when there are no deletions")

func test_parse_git_shortstat_deletions_only() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Clean up dead code\n 2 files changed, 100 deletions(-)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.card_name, "清理 up dead code", "Card name should match commit message")
	assert_eq(card_data.cost, 2, "Cost should match clamped files changed (2)")
	assert_eq(card_data.damage, 5, "Damage should match min damage limit 5")
	assert_eq(card_data.block, 20, "Block should match clamped deletions / 5 (100/5=20)")

func test_parse_git_extreme_limits() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Extreme refactor\n 15 files changed, 1000 insertions(+), 500 deletions(-)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.cost, 3, "Cost should be capped at max 3")
	assert_eq(card_data.damage, 50, "Damage should be capped at max 50")
	assert_eq(card_data.block, 30, "Block should be capped at max 30")

func test_all_10_categories_parsing() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var test_cases = {
		"🤖 deploy visual UI audit agent\n 1 file changed, 10 insertions(+)": "Agent",
		"✨ implement twin simulator core\n 1 file changed, 10 insertions(+)": "Feature",
		"docs: document api integrations\n 1 file changed, 10 insertions(+)": "Docs",
		"Merge branch dev/twins\n 1 file changed, 10 insertions(+)": "Merge",
		"fix: memory leak\n 1 file changed, 10 insertions(+)": "Fix",
		"refactor: restructure auth credentials module\n 1 file changed, 10 insertions(+)": "Refactor",
		"⚡ reduce cold start latency\n 1 file changed, 10 insertions(+)": "Performance",
		"test: add unit tests\n 1 file changed, 10 insertions(+)": "Test",
		"style: adjust glow border styling\n 1 file changed, 10 insertions(+)": "Style",
		"chore: upgrade packages\n 1 file changed, 10 insertions(+)": "Chore"
	}
	for log_str in test_cases:
		var expected = test_cases[log_str]
		var card: CardStats = parser.generate_card_from_log(log_str)
		assert_eq(card.category, expected, "Log should map to " + expected)
