extends HBoxContainer

@onready var player_hud = $PlayerStatusHUD
@onready var enemy_hud = $EnemyThreatHUD

# Player HUD nodes
@onready var player_shader = player_hud.get_node("ShaderRect")
@onready var purity_label = player_hud.get_node("PurityLabel")
@onready var rank_label = player_hud.get_node("RankLabel")
@onready var ap_label = player_hud.get_node("APLabel")

# Enemy HUD nodes
@onready var enemy_shader = enemy_hud.get_node("ShaderRect")
@onready var poison_label = enemy_hud.get_node("PoisonLabel")
@onready var rate_limit_label = enemy_hud.get_node("RateLimitLabel")
@onready var sla_label = enemy_hud.get_node("SLALabel")

var max_crisis_hp: float = 10000.0
var current_ap_max: int = 10

func _ready() -> void:
	pass

func initialize_career(level: int, player_hp: float) -> void:
	rank_label.text = tr("hud_rank") + " L" + str(level)
	update_player_hp(player_hp)

func update_ap(new_ap: int) -> void:
	ap_label.text = str(new_ap) + " / " + str(current_ap_max)
	player_shader.material.set_shader_parameter("ap_current", new_ap)

func update_purity(purity: float) -> void:
	purity_label.text = str(int(purity * 100.0)) + "%"
	player_shader.material.set_shader_parameter("purity_pct", purity)

func update_player_hp(new_hp: float) -> void:
	var pct = clamp(new_hp / 100.0, 0.0, 1.0)
	player_shader.material.set_shader_parameter("hp_pct", pct)

func update_crisis_hp(new_hp: float, event_queue: Node = null) -> void:
	var old_val = enemy_shader.material.get_shader_parameter("hp_pct") * max_crisis_hp
	var pct = clamp(new_hp / max_crisis_hp, 0.0, 1.0)
	enemy_shader.material.set_shader_parameter("hp_pct", pct)
	
	if old_val > new_hp:
		if event_queue:
			event_queue.add_animation(func():
				var tween = CombatJuice.damage_flash_and_shake(enemy_hud)
				await tween.finished
			)
		else:
			CombatJuice.damage_flash_and_shake(enemy_hud)

func update_sla(new_sla: float) -> void:
	var mins = int(new_sla) / 60
	var secs = int(new_sla) % 60
	sla_label.text = "[%s] %02d:%02d" % [tr("hud_sla"), mins, secs]
	
	# Mapping SLA time to the 10 triangles
	var max_sla = 300.0
	var ap_current = clamp(int((new_sla / max_sla) * 10), 0, 10)
	enemy_shader.material.set_shader_parameter("ap_current", ap_current)
	
	if new_sla < 30.0:
		CombatJuice.warning_pulse(sla_label, Time.get_ticks_msec())

func update_poisoning(ratio: float) -> void:
	poison_label.text = str(int(ratio * 100.0)) + "%"
	enemy_shader.material.set_shader_parameter("purity_pct", ratio)
	
	if ratio > 0.5:
		enemy_shader.material.set_shader_parameter("glitch_intensity", (ratio - 0.5) * 2.0)
	else:
		enemy_shader.material.set_shader_parameter("glitch_intensity", 0.0)

func update_rate_limit(compression: float, event_queue: Node = null) -> void:
	if compression < 0.8:
		rate_limit_label.text = "[ RATE LIMITED ]"
		rate_limit_label.add_theme_color_override("font_color", Color(1.0, 0.0, 0.0))
		enemy_shader.material.set_shader_parameter("glitch_intensity", 1.0)
		
		if event_queue:
			event_queue.add_animation(func():
				var tween = CombatJuice.flash_alpha(rate_limit_label)
				await tween.finished
			)
		else:
			CombatJuice.flash_alpha(rate_limit_label)
	else:
		rate_limit_label.text = "[ SYSTEM STABLE ]"
		rate_limit_label.remove_theme_color_override("font_color")
		enemy_shader.material.set_shader_parameter("glitch_intensity", 0.0)
