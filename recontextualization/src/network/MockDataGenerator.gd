class_name MockDataGenerator

static func generate_mock_rag_chunks() -> Array:
	var mock_cards = []
	var num_cards = randi_range(3, 4)

	
	for i in range(num_cards):
		var card = CardData.new()
		card.type = CardData.CardType.DATA_CHIP
		card.similarity = randf_range(0.3, 0.98)
		card.title = "[MOCK] RAG Chunk #%d" % [i + 1]
		card.match_type = randi_range(1, 3)
		mock_cards.append(card)
		
	return mock_cards
