extends RefCounted

var templates_dict: Dictionary = {}

func _init() -> void:
	_load_templates()

func _load_templates() -> void:
	var path = "res://Scripts/Resources/prompt_templates.json"
	if FileAccess.file_exists(path):
		var file = FileAccess.open(path, FileAccess.READ)
		var text = file.get_as_text()
		file.close()
		var json = JSON.new()
		if json.parse(text) == OK:
			templates_dict = json.data

func get_prompt_text_for_step(idx: int, role_name: String, agent_name: String) -> String:
	if not templates_dict.has("templates"): return ""
	var prompts = templates_dict["templates"]
	var step_keys = ["01_box_art", "02_south_anchor", "03_neutral_anchor", "04_directional_anchors", "05_walk_cycle", "06_attack_spritesheet", "07_idle_spritesheet"]
	if idx < 0 or idx >= len(step_keys): return ""
	var key = step_keys[idx]
	if not prompts.has(key): return ""
	
	var text = prompts[key]
	var replacements = {
		"{CHARACTER_NAME}": agent_name,
		"{CHARACTER_ARCHETYPE}": role_name,
		"{ARCHETYPE}": role_name,
		"{CORE_IDENTITY}": "cyborg hacker with neon accents",
		"{COSTUME_AND_COLOR_PALETTE}": "dark suit, neon green tie",
		"{SIGNATURE_PROP}": "holographic datapad",
		"{PERSONALITY_OR_POSE}": "confident and professional",
		"{CHARACTER_SPECIFIC_BIOME}": "cyberpunk office",
		"{LOGICAL_FRAME_SIZE}": "32x32",
		"{OUTPUT_SIZE}": "1024x1024",
		"{DIRECTION}": "SOUTH",
		"{DIRECTION_DESCRIPTION}": "directly toward the camera",
		"{CHROMA_COLOR}": "#FF00FF",
		"{SILHOUETTE_NOTES}": "readable silhouette",
		"{COSTUME_DETAILS}": "detailed vest",
		"{PROP_DETAILS}": "datapad in hand",
		"{DYNAMIC_EFFECT}": "none",
		"{DYNAMIC_EFFECT_HAND}": "empty",
		"{DIRECTIONAL_SILHOUETTE_DETAILS}": "clean profile",
		"{SHEET_SIZE}": "5x2 spritesheet",
		"{CELL_SIZE}": "32x32 cells",
		"{ATTACK_OR_WORK_NAME}": "typing on keyboard",
		"{EFFECT_COLOR}": "neon green",
		"{PROJECTILE_OR_EFFECT}": "hologram",
		"{EFFECT_TRAVEL_DIRECTION}": "forward"
	}
	
	for r_key in replacements:
		text = text.replace(r_key, "[color=#39ff14]" + replacements[r_key] + "[/color]")
		
	return text
