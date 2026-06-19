extends Node
class_name CombatJuice

var main_ui: Node2D
var hit_sound: AudioStreamPlayer
var error_sound: AudioStreamPlayer

func setup(p_main_ui: Node2D, p_hit: AudioStreamPlayer, p_error: AudioStreamPlayer) -> void:
	main_ui = p_main_ui
	hit_sound = p_hit
	error_sound = p_error

func play_error() -> void:
	error_sound.play()
	CombatVFX.shake_camera(main_ui, main_ui.camera, 5.0)

func handle_player_damaged(amount: int) -> void:
	CombatVFX.shake_camera(main_ui, main_ui.camera, 15.0)
	hit_sound.play()
	CombatVFX.animate_fighter(main_ui, main_ui.player_avatar, -50)
	CombatVFX.spawn_floating_text(main_ui, main_ui.get_node("UILayer"), main_ui.player_avatar.global_position + Vector2(100, 100), "-" + str(amount), Color(1, 0.2, 0.2))

func handle_enemy_damaged(amount: int) -> void:
	CombatVFX.shake_camera(main_ui, main_ui.camera, amount * 0.5)
	hit_sound.play()
	CombatVFX.spawn_floating_text(main_ui, main_ui.get_node("UILayer"), main_ui.enemy_avatar.global_position + Vector2(100, 100), "-" + str(amount), Color(1, 0.2, 0.2))

func handle_player_gained_block(amount: int) -> void:
	CombatVFX.spawn_floating_text(main_ui, main_ui.get_node("UILayer"), main_ui.player_avatar.global_position + Vector2(100, 100), "+" + str(amount) + " [Block]", Color(0.2, 0.8, 1))
