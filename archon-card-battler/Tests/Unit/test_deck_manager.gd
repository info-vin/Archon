@tool
extends MiniTest

# Godot EditorScript 的進入點
func _run() -> void:
	run_test_suite()

func test_add_and_draw_card() -> void:
	# 1. Arrange (準備階段：實例化要測試的物件)
	var deck_manager = preload("res://Scripts/Logic/DeckManager.gd").new()
	var dummy_card = preload("res://Scripts/Resources/CardStats.gd").new()
	dummy_card.card_name = "Test Bug Fix"
	
	# 2. Act (執行動作：把卡牌塞入牌庫)
	deck_manager.add_card(dummy_card)
	
	# 驗證牌庫數量是否為 1
	assert_eq(deck_manager.get_deck_size(), 1, "新增卡牌後，牌庫應該要有 1 張牌")
	
	# 執行抽牌動作
	var drawn_card = deck_manager.draw_card()
	
	# 3. Assert (斷言驗證結果)
	assert_not_null(drawn_card, "抽出來的卡牌不應該是 null")
	assert_eq(drawn_card.card_name, "Test Bug Fix", "抽出來的卡牌名稱要吻合")
	assert_eq(deck_manager.get_deck_size(), 0, "抽牌後，牌庫應該歸零")
