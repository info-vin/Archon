import json

with open("Scripts/Resources/prompt_templates.json", "r") as f:
    data = json.load(f)

data["roles"]["sales"] = {
  "character_name": "Deal-Closer",
  "character_archetype": "sales representative",
  "core_identity": "charismatic male sales rep, wearing a sleek neon yellow vest over a dark shirt, holding a deck of holographic business cards, standing with a confident pitch pose",
  "costume_and_color_palette": "dark grey clothing with bright neon yellow vest",
  "signature_prop": "holographic business cards",
  "personality_or_pose": "confident, charismatic pose",
  "character_specific_biome": "corporate negotiation room with neon city view",
  "logical_frame_size": "256x256",
  "output_size": "1024x1024",
  "chroma_color": "#FF00FF",
  "silhouette_notes": "sharp vest outline, dynamic arm gesture",
  "costume_details": "neon yellow vest, professional but cyber tie",
  "prop_details": "deck of glowing yellow cards",
  "dynamic_effect": "yellow holographic projections from cards",
  "dynamic_effect_hand": "Right hand",
  "direction": "WEST",
  "direction_description": "facing left in profile, body in 3/4 left turn",
  "directional_silhouette_details": "show charismatic face profile, sleek vest side view",
  "attack_or_work_name": "pitching and dealing cards action",
  "effect_color": "yellow",
  "projectile_or_effect": "glowing yellow cards flying horizontally",
  "effect_travel_direction": "forward"
}

with open("Scripts/Resources/prompt_templates.json", "w") as f:
    json.dump(data, f, indent=2)
