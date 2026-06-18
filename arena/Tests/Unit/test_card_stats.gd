extends MiniTest

func test_card_initialization():
	# 嘗試實例化我們定義的 CardStats 資源
	var card = preload("res://Scripts/Resources/CardStats.gd").new()
	
	# 預期剛建立的卡牌，數值應該要有預設值
	assert_eq(card.card_name, "New Card", "預設卡牌名稱應該是 'New Card'")
	assert_eq(card.cost, 1, "預設卡牌花費應該是 1 Token")
	assert_eq(card.damage, 0, "預設傷害應該是 0")
	assert_eq(card.block, 0, "預設護盾應該是 0")

func test_card_custom_values():
	var card = preload("res://Scripts/Resources/CardStats.gd").new()
	
	# 修改數值
	card.card_name = "Deep Refactor"
	card.cost = 3
	card.damage = 15
	
	# 驗證修改是否成功
	assert_eq(card.card_name, "Deep Refactor", "名稱修改應生效")
	assert_eq(card.cost, 3, "花費修改應生效")
	assert_eq(card.damage, 15, "傷害修改應生效")
