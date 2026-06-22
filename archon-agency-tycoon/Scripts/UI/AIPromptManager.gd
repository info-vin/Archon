extends VBoxContainer
class_name AIPromptManager

var path_edits: Array = []
var lock_label: Label

signal copy_prompt_requested(idx: int)
signal browse_requested(idx: int)

func setup() -> void:
	self.name = "AIPromptManager"
	self.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	self.size_flags_vertical = Control.SIZE_EXPAND_FILL
	self.add_theme_constant_override("separation", 10)
	
	var scroll = ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	
	var steps_vbox = VBoxContainer.new()
	steps_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	steps_vbox.add_theme_constant_override("separation", 15)
	scroll.add_child(steps_vbox)
	
	var steps_data = ["Box Art (Full Body)", "South Anchor (32x32 Head to Toes)", "Neutral Reset (Remove gear)", "Directions (SE, E, NE, N)", "Walk Video (South walking)", "Work Sheet", "Idle Sheet"]
	
	path_edits = []
	
	for i in range(len(steps_data)):
		var step_card = PanelContainer.new()
		var style = StyleBoxFlat.new()
		style.bg_color = Color(0.05, 0.05, 0.15, 0.8)
		style.border_width_left = 2
		style.border_width_right = 2
		style.border_color = Color(0, 0.8, 1, 1) # Neon Cyan
		style.set_corner_radius_all(5)
		step_card.add_theme_stylebox_override("panel", style)
		
		var margin = MarginContainer.new()
		margin.add_theme_constant_override("margin_left", 15)
		margin.add_theme_constant_override("margin_right", 15)
		margin.add_theme_constant_override("margin_top", 15)
		margin.add_theme_constant_override("margin_bottom", 15)
		step_card.add_child(margin)
		
		var card_vbox = VBoxContainer.new()
		card_vbox.add_theme_constant_override("separation", 8)
		margin.add_child(card_vbox)
		
		var title = Label.new()
		title.text = "Step 0" + str(i+1) + " - " + steps_data[i]
		title.add_theme_color_override("font_color", Color(0, 1, 1, 1)) # Cyan text
		card_vbox.add_child(title)
		
		var prompt_rt = RichTextLabel.new()
		prompt_rt.bbcode_enabled = true
		prompt_rt.custom_minimum_size = Vector2(0, 160)
		prompt_rt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		prompt_rt.add_theme_color_override("default_color", Color(0.8, 0.8, 0.8, 1))
		card_vbox.add_child(prompt_rt)
		
		var actions_hbox = HBoxContainer.new()
		actions_hbox.add_theme_constant_override("separation", 10)
		card_vbox.add_child(actions_hbox)
		
		var copy_btn = Button.new()
		copy_btn.text = "Copy Prompt"
		var copy_style = StyleBoxFlat.new()
		copy_style.bg_color = Color(0.1, 0.3, 0.5, 1)
		copy_style.border_width_left = 1
		copy_style.border_width_right = 1
		copy_style.border_width_top = 1
		copy_style.border_width_bottom = 1
		copy_style.border_color = Color(0, 1, 1, 1)
		copy_btn.add_theme_stylebox_override("normal", copy_style)
		copy_btn.pressed.connect(_on_copy_pressed.bind(i))
		actions_hbox.add_child(copy_btn)
		
		var path_edit = LineEdit.new()
		path_edit.placeholder_text = "No image selected..."
		path_edit.editable = false
		path_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		path_edits.append(path_edit)
		actions_hbox.add_child(path_edit)
		
		var browse_btn = Button.new()
		browse_btn.text = "Browse..."
		browse_btn.pressed.connect(_on_browse_pressed.bind(i))
		actions_hbox.add_child(browse_btn)
		
		steps_vbox.add_child(step_card)
		
	lock_label = Label.new()
	lock_label.modulate = Color(1, 0.4, 0.4)
	add_child(lock_label)

func _on_copy_pressed(idx: int) -> void:
	copy_prompt_requested.emit(idx)

func _on_browse_pressed(idx: int) -> void:
	browse_requested.emit(idx)

func update_prompts(prompts: Array) -> void:
	var scroll = get_child(0) as ScrollContainer
	if not scroll: return
	var steps_vbox = scroll.get_child(0) as VBoxContainer
	for i in range(min(prompts.size(), steps_vbox.get_child_count())):
		var step_card = steps_vbox.get_child(i)
		var margin = step_card.get_child(0)
		var card_vbox = margin.get_child(0)
		var prompt_rt = card_vbox.get_child(1) as RichTextLabel
		if prompt_rt:
			prompt_rt.text = prompts[i]

func update_paths(slot_paths: Array) -> void:
	for i in range(min(slot_paths.size(), path_edits.size())):
		path_edits[i].text = slot_paths[i]
