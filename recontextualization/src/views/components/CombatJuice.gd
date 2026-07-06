extends RefCounted
class_name CombatJuice
## Applies a damage shake effect to a UI Control node.
static func shake_ui_element(node: Control, intensity: float = 10.0, duration: float = 0.2) -> Tween:
	var tween = node.create_tween()
	var original_pos = node.position
	tween.tween_property(node, "position", original_pos + Vector2(intensity, 0), duration * 0.25)
	tween.tween_property(node, "position", original_pos - Vector2(intensity, 0), duration * 0.25)
	tween.tween_property(node, "position", original_pos + Vector2(intensity/2.0, 0), duration * 0.25)
	tween.tween_property(node, "position", original_pos, duration * 0.25)
	return tween

## Flashes a UI element red and shakes it.
static func damage_flash_and_shake(node: Control) -> Tween:
	node.modulate = Color.RED
	var tween = shake_ui_element(node, 10.0, 0.2)
	tween.parallel().tween_property(node, "modulate", Color.WHITE, 0.3)
	return tween

## Creates a pulsing warning color.
static func warning_pulse(node: CanvasItem, time_msec: float, speed: float = 150.0) -> void:
	var pulse = (sin(time_msec / speed) + 1.0) / 2.0
	node.modulate = Color.WHITE.lerp(Color.RED, pulse)

## Flashes an element's alpha.
static func flash_alpha(node: CanvasItem) -> Tween:
	var tween = node.create_tween()
	tween.tween_property(node, "modulate:a", 0.0, 0.2)
	tween.tween_property(node, "modulate:a", 1.0, 0.2)
	return tween

## Applies a visual glitch/jitter effect, suitable for chaos events or errors
static func glitch_effect(node: Control, duration: float = 0.5) -> Tween:
	var tween = node.create_tween()
	var orig_pos = node.position
	for i in range(10):
		var offset = Vector2(randf_range(-15.0, 15.0), randf_range(-5.0, 5.0))
		var color = Color.GREEN if i % 2 == 0 else Color.RED
		tween.tween_property(node, "position", orig_pos + offset, duration / 10.0)
		tween.parallel().tween_property(node, "modulate", color, duration / 10.0)
	tween.tween_property(node, "position", orig_pos, 0.05)
	tween.parallel().tween_property(node, "modulate", Color.WHITE, 0.05)
	return tween

## A powerful blast effect for successfully delivering data to LLM
static func deliver_blast(node: Control) -> Tween:
	var tween = node.create_tween()
	var orig_scale = node.scale
	# Explosive scale up and color flash
	tween.tween_property(node, "scale", orig_scale * 1.5, 0.1).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(node, "modulate", Color(0.2, 0.8, 1.0, 1.0), 0.1)
	# Snap back to normal
	tween.tween_property(node, "scale", orig_scale, 0.2).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(node, "modulate", Color.WHITE, 0.2)
	return tween

## Dissolves a card out of existence when played/discarded
static func card_dissolve(node: Control) -> Tween:
	var tween = node.create_tween()
	# Shift upwards while fading out and shrinking
	tween.tween_property(node, "position:y", node.position.y - 50.0, 0.3)
	tween.parallel().tween_property(node, "scale", Vector2.ZERO, 0.3).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tween.parallel().tween_property(node, "modulate:a", 0.0, 0.3)
	# Free the node at the end of the animation
	tween.tween_callback(node.queue_free)
	return tween
