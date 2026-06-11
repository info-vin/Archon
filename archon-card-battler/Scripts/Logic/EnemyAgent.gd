extends RefCounted
class_name EnemyAgent

var current_hp: int
var max_hp: int

func _init(hp: int):
	self.max_hp = hp
	self.current_hp = hp

func take_damage(amount: int):
	current_hp -= amount
	if current_hp < 0:
		current_hp = 0
