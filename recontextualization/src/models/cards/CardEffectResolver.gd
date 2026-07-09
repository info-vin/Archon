class_name CardEffectResolver
extends RefCounted

## Resolves the effect of an action card on the game state.
static func resolve_action_card(game_state: Node, card: Resource) -> void:
	var card_id = card.get("id") if card.get("id") != null else ""
	var cost = card.get("ap_cost") if card.get("ap_cost") != null else 1
	
	game_state.env_mgr.deduct_sla(cost * 2.0) # Cost * 2.0 seconds penalty for playing action card
	
	if card_id == "reranker":
		# Reranker filter logic: remove similarity < 0.5 cards from active_context
		var remaining_cards = []
		for c in game_state.active_context.cards:
			var sim = c.get("similarity") if c.get("similarity") != null else 0.0
			if sim >= 0.5:
				remaining_cards.append(c)
		game_state.active_context.cards = remaining_cards
		var purity = BattleRuleEngine.calculate_context_purity(game_state.active_context.cards, 0.5)
		game_state.context_updated.emit(purity)
		game_state.context_purified.emit(remaining_cards)
		
	elif card_id == "action_keyword":
		game_state.search_ctrl.search_triggered.emit(3) # KEYWORD
		# Draw back so it's reusable
		var event_bus = game_state._safe_get_node("EventBus")
		if event_bus != null:
			event_bus.card_drawn.emit(card.duplicate())
		game_state.context_purified.emit(game_state.active_context.cards)
			
	elif card_id == "dense_search":
		game_state.search_ctrl.search_triggered.emit(2) # VECTOR
		var event_bus = game_state._safe_get_node("EventBus")
		if event_bus != null:
			event_bus.card_drawn.emit(card.duplicate())
		game_state.context_purified.emit(game_state.active_context.cards)
		
	elif card_id == "graph_rag":
		game_state.active_context.add_card(card)
		var purity = BattleRuleEngine.calculate_context_purity(game_state.active_context.cards, 0.5)
		game_state.context_updated.emit(purity)
