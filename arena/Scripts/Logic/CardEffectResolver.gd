extends RefCounted
class_name CardEffectResolver

func resolve_effects(card: CardStats, state: GameState, final_damage: int) -> String:
	var msg = ""
	
	match card.category:
		"Performance":
			state.player_mana = min(state.player_max_mana, state.player_mana + 2)
			state.emit_signal("mana_changed", state.player_mana, state.player_max_mana)
			msg += " [color=#facc15][Str] Performance: Restored 2 Tokens![/color]"
			
		"Merge":
			state.player_hp = min(state.player_max_hp, state.player_hp + 10)
			state.emit_signal("player_hp_changed", state.player_hp, state.player_max_hp)
			msg += " [color=#fbbf24][Merge] Healed 10 HP![/color]"
			
		"Refactor":
			var bonus_block = int(float(final_damage) * 0.5)
			state.player_block += bonus_block
			state.emit_signal("player_block_changed", state.player_block)
			state.emit_signal("player_gained_block", bonus_block)
			msg += " [color=#60a5fa][Refactor] Gained %d Block from damage![/color]" % bonus_block
			
		"Test":
			state.player_block += card.block # Double block
			state.emit_signal("player_block_changed", state.player_block)
			state.emit_signal("player_gained_block", card.block)
			msg += " [color=#c084fc][Test] Doubled Block (+%d Block)![/color]" % card.block
			
		"Docs":
			if state.deck_manager != null and state.deck_manager.has_method("draw_card"):
				var drawn = state.deck_manager.draw_card()
				if drawn != null:
					state.hand.append(drawn)
					msg += " [color=#22d3ee][Docs] Drew 1 card (%s).[/color]" % drawn.card_name
					state.emit_signal("draw_finished")
					
		"Style":
			state.player_block += 10
			state.emit_signal("player_block_changed", state.player_block)
			state.emit_signal("player_gained_block", 10)
			msg += " [color=#f472b6][Style] Gained 10 Block![/color]"
			
		"Agent":
			state.enemy_hp -= 20
			if state.enemy_hp < 0:
				state.enemy_hp = 0
			state.emit_signal("enemy_hp_changed", state.enemy_hp, state.enemy_max_hp)
			state.emit_signal("enemy_took_damage", 20)
			msg += " [color=#a78bfa][Agent] Dealt 20 direct DMG (bypassed shields)![/color]"
			
		"Chore":
			var cards_to_discard = []
			for h_card in state.hand:
				if h_card != card:
					cards_to_discard.append(h_card)
			for h_card in cards_to_discard:
				if state.deck_manager != null and state.deck_manager.has_method("discard_card"):
					state.deck_manager.discard_card(h_card)
				state.hand.erase(h_card)
			msg += " [color=#9ca3af][Chore] Discarded hand and drew 2 cards.[/color]"
			for i in range(2):
				if state.deck_manager != null and state.deck_manager.has_method("draw_card"):
					var drawn = state.deck_manager.draw_card()
					if drawn != null:
						state.hand.append(drawn)
			state.emit_signal("draw_finished")
			
	return msg
