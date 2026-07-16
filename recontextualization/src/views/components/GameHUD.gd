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
	# Cyberpunk Style Wrapper
	call_deferred("_apply_cyberpunk_wrapper")
	
	var create_bg = func(color: Color) -> StyleBoxFlat:
		var style = StyleBoxFlat.new()
		style.bg_color = color
		style.border_width_left = 1
		style.border_width_top = 1
		style.border_width_right = 1
		style.border_width_bottom = 1
		style.border_color = Color(0.3, 0.3, 0.3, 0.8)
		style.set_corner_radius_all(2)
		return style
	
	player_hp_bar.add_theme_stylebox_override("background", create_bg.call(Color(0.05, 0.1, 0.2, 0.8)))
	purity_bar.add_theme_stylebox_override("background", create_bg.call(Color(0.05, 0.2, 0.05, 0.8)))
	poison_bar.add_theme_stylebox_override("background", create_bg.call(Color(0.2, 0.05, 0.05, 0.8)))
	crisis_hp_bar.add_theme_stylebox_override("background", create_bg.call(Color(0.2, 0.0, 0.1, 0.8)))
	
	if style_green:
		purity_bar.add_theme_stylebox_override("fill", style_green)
	if style_red:
		poison_bar.add_theme_stylebox_override("fill", style_red)
	if style_dark_red:
		crisis_hp_bar.add_theme_stylebox_override("fill", style_dark_red)

func _apply_cyberpunk_wrapper() -> void:
	var parent = get_parent()
	if parent and not get_parent() is PanelContainer:
		var panel = PanelContainer.new()
		var style = StyleBoxFlat.new()
		style.bg_color = Color(0.05, 0.05, 0.1, 0.85)
		style.border_width_left = 2
		style.border_width_top = 2
		style.border_width_right = 2
		style.border_width_bottom = 2
		style.border_color = Color(0.2, 0.9, 0.8, 0.6)
		style.set_corner_radius_all(6)
		style.content_margin_left = 15
		style.content_margin_right = 15
		style.content_margin_top = 10
		style.content_margin_bottom = 10
		panel.add_theme_stylebox_override("panel", style)
		
		var idx = get_index()
		parent.remove_child(self)
		panel.add_child(self)
		parent.add_child(panel)
		parent.move_child(panel, idx)

	_setup_bar_label(player_hp_bar, "hud_player_hp")
	_setup_bar_label(crisis_hp_bar, "hud_crisis_hp")
	_setup_bar_label(purity_bar, "hud_purity")
	_setup_bar_label(poison_bar, "hud_poisoning")

func _setup_bar_label(bar: ProgressBar, loc_key: String) -> void:
	bar.show_percentage = false
	var lbl = Label.new()
	lbl.set_anchors_preset(Control.PRESET_FULL_RECT)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.add_theme_font_size_override("font_size", 16)
	lbl.add_theme_color_override("font_shadow_color", Color(0,0,0,1))
	lbl.name = "TextLabel"
	lbl.set_meta("loc_key", loc_key)
	bar.add_child(lbl)

func _update_bar_label(bar: ProgressBar, value: float, is_percent: bool = false) -> void:
	var lbl = bar.get_node_or_null("TextLabel")
	if lbl:
		var loc_key = lbl.get_meta("loc_key", "")
		var prefix = tr(loc_key)
		if is_percent:
			lbl.text = "[%s] %d%%" % [prefix, int(value)]
		else:
			lbl.text = "[%s] %d" % [prefix, int(value)]

func initialize_career(level: int, player_hp: float) -> void:
	career_label.text = tr("hud_rank") + " L" + str(level)
	player_hp_bar.max_value = 100.0
	player_hp_bar.value = player_hp
	_update_bar_label(player_hp_bar, player_hp, false)
	_update_bar_label(crisis_hp_bar, crisis_hp_bar.value, false)
	_update_bar_label(purity_bar, purity_bar.value, true)
	_update_bar_label(poison_bar, poison_bar.value, true)

func update_ap(new_ap: int) -> void:
	ap_label.text = "[" + tr("hud_ap") + "] %d" % new_ap

func update_purity(purity: float) -> void:
	purity_bar.value = purity * 100.0
	_update_bar_label(purity_bar, purity * 100.0, true)

func update_player_hp(new_hp: float) -> void:
	player_hp_bar.value = new_hp
	_update_bar_label(player_hp_bar, new_hp, false)

func update_crisis_hp(new_hp: float, event_queue: Node = null) -> void:
	var old_val = crisis_hp_bar.value
	crisis_hp_bar.value = new_hp
	_update_bar_label(crisis_hp_bar, new_hp, false)
	
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
	sla_text.text = "[%s] %02d:%02d" % [tr("hud_sla"), mins, secs]
	
	if new_sla < 30.0:
		CombatJuice.warning_pulse(sla_progress, Time.get_ticks_msec())
	elif new_sla < 60.0:
		sla_progress.modulate = Color.RED
	else:
		sla_progress.modulate = Color.WHITE

func update_poisoning(ratio: float) -> void:
	poison_bar.value = ratio * 100.0
	_update_bar_label(poison_bar, ratio * 100.0, true)

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
