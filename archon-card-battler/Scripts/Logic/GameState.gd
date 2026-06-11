extends RefCounted
class_name GameState

var current_mana: int
var max_mana: int

func _init(mana: int):
	self.max_mana = mana
	self.current_mana = mana

func play_card(card: CardStats, enemy: EnemyAgent) -> bool:
	if current_mana >= card.cost:
		current_mana -= card.cost
		enemy.take_damage(card.damage)
		return true
	else:
		return false
