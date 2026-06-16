import os

gd_path = 'archon-agency-tycoon/Scripts/Main.gd'

with open(gd_path, 'r') as f:
    gd = f.read()

# Replace the top bar references
old_refs = """@onready var funds_label: Label = $VBox/TopBar/HBox/FundsValue
@onready var funds_title: Label = $VBox/TopBar/HBox/FundsLabel
@onready var rep_title: Label = $VBox/TopBar/HBox/RepLabel"""
new_refs = """@onready var ticker: RichTextLabel = $VBox/TopBar/HBox/TickerLabel"""
gd = gd.replace(old_refs, new_refs)

# Replace the static labels update
old_static = """func _update_static_labels() -> void:
	funds_title.text = tr("UI_FUNDS")
	rep_title.text = tr("UI_REP")"""
new_static = """func _update_static_labels() -> void:"""
gd = gd.replace(old_static, new_static)

# Remove the language button text update
gd = gd.replace('lang_button.text = "Language: " + lang_names[current_lang_index]', '')

# Update the UI update function to use the ticker
old_ui = """func _update_ui() -> void:
	funds_label.text = "$%d" % tycoon_manager.funds"""
new_ui = """func _update_ui() -> void:
	if ticker:
		var f_color = "#39ff14" if tycoon_manager.funds > 0 else "#ff003c"
		var r_color = "#39ff14" if tycoon_manager.reputation > 50 else "#ff003c"
		ticker.text = "[color=#888888]ARCHON CORP | TICK:[/color] [color=#ffffff]%d[/color] [color=#888888]| %s:[/color] [color=%s]$%d[/color] [color=#888888]| %s:[/color] [color=%s]%d[/color]" % [
			task_manager.current_tick, 
			tr("UI_FUNDS"), f_color, tycoon_manager.funds,
			tr("UI_REP"), r_color, tycoon_manager.reputation
		]"""
gd = gd.replace(old_ui, new_ui)

with open(gd_path, 'w') as f:
    f.write(gd)
    
print("✅ Main.gd Updated!")
