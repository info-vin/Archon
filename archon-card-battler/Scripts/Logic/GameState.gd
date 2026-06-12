extends RefCounted
class_name GameState

var current_mana: int
var max_mana: int
var player_hp: int
var max_hp: int
var player_block: int

func _init(mana: int, hp: int = 100):
	self.max_mana = mana
	self.current_mana = mana
	self.max_hp = hp
	self.player_hp = hp
	self.player_block = 0

func play_card(card: CardStats, enemy: EnemyAgent) -> bool:
	if current_mana >= card.cost:
		current_mana -= card.cost
		enemy.take_damage(card.damage)
		player_block += card.block
		return true
	else:
		return false

func enemy_attack(damage: int) -> int:
	var actual_damage = max(0, damage - player_block)
	player_block = max(0, player_block - damage)
	player_hp -= actual_damage
	if player_hp < 0:
		player_hp = 0
	return actual_damage
