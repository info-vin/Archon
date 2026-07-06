extends HBoxContainer

@onready var poison_bar: ProgressBar = $PoisonBar
@onready var rate_limit_label: Label = $RateLimitLabel
@onready var career_label: Label = $CareerLabel
@onready var player_hp_bar: ProgressBar = $PlayerHPBar
@onready var ap_label: Label = $APLabel
@onready var purity_bar: ProgressBar = $PurityBar
@onready var crisis_hp_bar: ProgressBar = $CrisisHPBar
@onready var sla_progress: ProgressBar = $SLAPorgressBar
@onready var sla_text: Label = $SLAPorgressBar/SLAText

@export var style_green: StyleBox
@export var style_red: StyleBox
@export var style_dark_red: StyleBox



func _ready() -> void:
	if style_green:
		purity_bar.add_theme_stylebox_override("fill", style_green)
	if style_red:
		poison_bar.add_theme_stylebox_override("fill", style_red)
	if style_dark_red:
		crisis_hp_bar.add_theme_stylebox_override("fill", style_dark_red)

func initialize_career(level: int, max_player_hp: float) -> void:
	career_label.text = "L" + str(level)
	player_hp_bar.max_value = max_player_hp

func update_ap(new_ap: int) -> void:
	ap_label.text = tr("hud_ap") + ": %d" % new_ap

func update_purity(purity: float) -> void:
	purity_bar.value = purity * 100.0

func update_player_hp(new_hp: float) -> void:
	player_hp_bar.value = new_hp

func update_crisis_hp(new_hp: float, event_queue: Node = null) -> void:
	var old_val = crisis_hp_bar.value
	crisis_hp_bar.value = new_hp
	
	if old_val > new_hp:
		if event_queue:
			event_queue.add_animation(func():
				var tween = CombatJuice.damage_flash_and_shake(crisis_hp_bar)
				await tween.finished
			)
		else:
			CombatJuice.damage_flash_and_shake(crisis_hp_bar)

func update_sla(new_sla: float) -> void:
	sla_progress.value = new_sla
	var mins = int(new_sla) / 60
	var secs = int(new_sla) % 60
	sla_text.text = "SLA: %02d:%02d" % [mins, secs]
	
	if new_sla < 30.0:
		CombatJuice.warning_pulse(sla_progress, Time.get_ticks_msec())
	elif new_sla < 60.0:
		sla_progress.modulate = Color.RED
	else:
		sla_progress.modulate = Color.WHITE

func update_poisoning(ratio: float) -> void:
	poison_bar.value = ratio * 100.0

func update_rate_limit(compression: float, event_queue: Node = null) -> void:
	if compression < 0.8:
		rate_limit_label.show()
		if event_queue:
			event_queue.add_animation(func():
				var tween = CombatJuice.flash_alpha(rate_limit_label)
				await tween.finished
			)
		else:
			CombatJuice.flash_alpha(rate_limit_label)
	else:
		rate_limit_label.hide()
