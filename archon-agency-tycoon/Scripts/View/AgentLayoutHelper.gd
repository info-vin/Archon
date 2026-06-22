extends RefCounted
class_name AgentLayoutHelper

const PIXEL_LAYOUT = {
	"body": {"pos": Vector2.ZERO, "scale": Vector2.ONE},
	"eyes": {"pos": Vector2(3.5, -19.5), "scale": Vector2.ONE},
	"hair": {"pos": Vector2(0, -18), "scale": Vector2.ONE},
	"outfit": {"pos": Vector2(0, 2), "scale": Vector2.ONE},
	"tool": {"pos": Vector2(18, 6), "scale": Vector2(0.8, 0.8)}
}

const SVG_LAYOUT = {
	"body": {"pos": Vector2.ZERO, "scale": Vector2.ONE},
	"eyes": {"pos": Vector2(0, -180), "scale": Vector2(0.12, 0.12)},
	"hair": {"pos": Vector2(0, -220), "scale": Vector2(0.7, 0.7)},
	"outfit": {"pos": Vector2(0, 10), "scale": Vector2(0.75, 0.75)},
	"tool": {"pos": Vector2(150, -50), "scale": Vector2(0.4, 0.4)}
}

const BOB_LAYOUT = {
	"body": {"pos": Vector2(0, -18), "scale": Vector2(0.35, 0.35)},
	"outfit": {"pos": Vector2(0, 0), "scale": Vector2(0.35, 0.35)},
	"hair": {"pos": Vector2(0, 21), "scale": Vector2(0.35, 0.35)},
	"tool": {"pos": Vector2(6, 2), "scale": Vector2(0.3, 0.3)}
}

static func apply_layout_dict(sprites: Dictionary, layout: Dictionary) -> void:
	for n in layout:
		if sprites.has(n) and sprites[n]:
			var sprite = sprites[n]
			sprite.position = layout[n].pos
			sprite.scale = layout[n].scale
			sprite.rotation = 0.0
			if n != "hair":
				sprite.modulate = Color.WHITE

static func reset_layout_for_option_a(is_bob: bool, sprites: Dictionary) -> void:
	if is_bob:
		if sprites.get("body"):
			sprites["body"].position = Vector2(0, -18)
			sprites["body"].scale = Vector2(0.35, 0.35)
			sprites["body"].region_enabled = true
		if sprites.get("outfit"):
			sprites["outfit"].position = Vector2(0, 0)
			sprites["outfit"].scale = Vector2(0.35, 0.35)
			sprites["outfit"].region_enabled = true
		if sprites.get("hair"):
			sprites["hair"].position = Vector2(0, 21)
			sprites["hair"].scale = Vector2(0.35, 0.35)
			sprites["hair"].region_enabled = true
		if sprites.get("tool"):
			sprites["tool"].position = Vector2(6, 2)
			sprites["tool"].scale = Vector2(0.3, 0.3)
		return

	apply_layout_dict(sprites, PIXEL_LAYOUT)
	if sprites.get("eyes"):
		sprites["eyes"].region_enabled = true
		sprites["eyes"].region_rect = Rect2(29, 34, 13, 11)

static func reset_layout_for_option_b(sprites: Dictionary) -> void:
	apply_layout_dict(sprites, SVG_LAYOUT)
	if sprites.get("eyes"):
		sprites["eyes"].region_enabled = false
