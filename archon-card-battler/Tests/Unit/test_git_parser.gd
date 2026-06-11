@tool
extends MiniTest

func _run() -> void:
	run_test_suite()

func test_parse_git_shortstat_full() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Fix memory leak\n 3 files changed, 45 insertions(+), 12 deletions(-)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.card_name, "Fix memory leak", "Card name should match commit message")
	assert_eq(card_data.cost, 3, "Cost should equal files changed")
	assert_eq(card_data.damage, 45, "Damage should equal insertions")
	assert_eq(card_data.block, 12, "Block should equal deletions")

func test_parse_git_shortstat_insertions_only() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Update readme\n 1 file changed, 5 insertions(+)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.card_name, "Update readme", "Card name should match commit message")
	assert_eq(card_data.cost, 1, "Cost should equal files changed")
	assert_eq(card_data.damage, 5, "Damage should equal insertions")
	assert_eq(card_data.block, 0, "Block should be 0 when there are no deletions")

func test_parse_git_shortstat_deletions_only() -> void:
	var parser = preload("res://Scripts/Logic/GitLogParser.gd").new()
	var mock_git_log = "Clean up dead code\n 2 files changed, 100 deletions(-)"
	var card_data: CardStats = parser.generate_card_from_log(mock_git_log)
	
	assert_not_null(card_data, "CardStats should be created")
	assert_eq(card_data.card_name, "Clean up dead code", "Card name should match commit message")
	assert_eq(card_data.cost, 2, "Cost should equal files changed")
	assert_eq(card_data.damage, 0, "Damage should be 0 when there are no insertions")
	assert_eq(card_data.block, 100, "Block should equal deletions")
